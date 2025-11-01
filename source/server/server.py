import asyncio
import base64
import hashlib
import logging
import sys
from dataclasses import dataclass
from typing import Dict, Optional
from urllib.parse import urlparse

from room_manager import RoomManager
from http_handler import HTTPHandler
from signaling_handler import SignalingHandler
from media_handler import MediaHandler


@dataclass
class HTTPRequest:
    method: str
    path: str
    version: str
    headers: Dict[str, str]
    body: bytes = b""

class UnifiedServer:
    def __init__(self, host: str = '0.0.0.0', port: int = 8080):
        self.host = host
        self.port = port
        self.room_manager = RoomManager()
        self.server: Optional[asyncio.AbstractServer] = None

        self.http_handler = HTTPHandler()
        self.signaling_handler = SignalingHandler(self.room_manager)
        self.media_handler = MediaHandler(self.room_manager)

        self.logger = logging.getLogger(self.__class__.__name__)
        self.websocket_routes = {
            '/signaling': self.signaling_handler.handle,
            '/media': self.media_handler.handle,
        }

    async def start(self) -> None:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        )
        self.logger.info("Server starting on %s:%s", self.host, self.port)

        self.server = await asyncio.start_server(
            self.handle_client,
            self.host,
            self.port,
        )

        self.logger.info("Server running on %s:%s", self.host, self.port)

        async with self.server:
            await self.server.serve_forever()

    async def stop(self) -> None:
        if self.server:
            self.logger.info("Stopping server on %s:%s", self.host, self.port)
            self.server.close()
            await self.server.wait_closed()

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peername = writer.get_extra_info('peername')
        peer_display = self._format_peer(peername)
        self.logger.info("Accepted connection from %s", peer_display)

        try:
            request = await self._read_http_request(reader)
            if request is None:
                self.logger.warning("Failed to read HTTP request from %s", peer_display)
                await self._send_http_error(writer, 400, b"Bad Request")
                return
                
            request_line = request_line.decode('utf-8').strip()
            
            parts = request_line.split()
            if len(parts) < 2:
                writer.close()
                await writer.wait_closed()
                return
            
            method = parts[0]
            path = parts[1]
            
            headers = {}
            while True:
                line = await reader.readline()
                if not line:
                    break
                line = line.decode('utf-8').strip()
                if not line:
                    break
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip().lower()] = value.strip()
            
            upgrade = headers.get('upgrade', '').lower()
            
            if upgrade == 'websocket':
                subprotocol = self.select_subprotocol(path, headers.get('sec-websocket-protocol', ''))
                if not await self.websocket_handshake(writer, headers, subprotocol):
                    writer.close()
                    await writer.wait_closed()
                    return

                if '/signaling' in path:
                    await self.signaling_handler.handle(reader, writer)
                elif '/media' in path:
                    setattr(writer, 'media_subprotocol', subprotocol)
                    await self.media_handler.handle(reader, writer)
                else:
                    writer.close()
                    await writer.wait_closed()
            else:
                await self.http_handler.handle(writer, request.method, request.path)

        except Exception as exc:
            self.logger.exception("Error handling client %s: %s", peer_display, exc)
        finally:
            try:
                if not writer.is_closing():
                    writer.close()
                    await writer.wait_closed()
            except:
                pass
    
    def select_subprotocol(self, path: str, offered: str):
        if not offered:
            return None

        candidates = [item.strip() for item in offered.split(',') if item.strip()]
        if not candidates:
            return None

        if '/media' in path:
            for candidate in candidates:
                if candidate.startswith('media.') or candidate in {'audio', 'video', 'media'}:
                    return candidate

        return candidates[0]

    async def websocket_handshake(self, writer, headers, subprotocol=None):
        try:
            websocket_key = headers.get('sec-websocket-key')
            if not websocket_key:
                self.logger.warning("Missing Sec-WebSocket-Key from %s", peer_display)
                await self._send_http_error(writer, 400, b"Missing Sec-WebSocket-Key")
                return False

            accept_key = base64.b64encode(
                hashlib.sha1((websocket_key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode()).digest()
            ).decode()
            
            response = [
                'HTTP/1.1 101 Switching Protocols\r\n',
                'Upgrade: websocket\r\n',
                'Connection: Upgrade\r\n',
                f'Sec-WebSocket-Accept: {accept_key}\r\n',
            ]

            if subprotocol:
                response.append(f'Sec-WebSocket-Protocol: {subprotocol}\r\n')

            response.append('\r\n')

            payload = ''.join(response)

            writer.write(payload.encode('utf-8'))
            await writer.drain()

            return True

        except Exception as e:
            return False

    async def _read_http_request(self, reader: asyncio.StreamReader) -> Optional[HTTPRequest]:
        try:
            request_line_bytes = await reader.readline()
            if not request_line_bytes:
                return None

            request_line = request_line_bytes.decode('utf-8').strip()
            if not request_line:
                return None

            parts = request_line.split()
            if len(parts) != 3:
                return None

            method, path, version = parts
            headers: Dict[str, str] = {}

            while True:
                line = await reader.readline()
                if not line:
                    break

                decoded_line = line.decode('utf-8')
                stripped_line = decoded_line.strip('\r\n')
                if stripped_line == '':
                    break

                if ':' not in stripped_line:
                    continue

                key, value = stripped_line.split(':', 1)
                headers[key.strip().lower()] = value.strip()

            body = b''
            content_length = headers.get('content-length')
            if content_length:
                try:
                    length = int(content_length)
                    if length > 0:
                        body = await reader.readexactly(length)
                except (ValueError, asyncio.IncompleteReadError):
                    return None

            return HTTPRequest(method=method, path=path, version=version, headers=headers, body=body)
        except UnicodeDecodeError:
            return None

    async def _send_http_error(self, writer: asyncio.StreamWriter, status: int, message: bytes) -> None:
        status_messages = {
            400: 'Bad Request',
            404: 'Not Found',
            405: 'Method Not Allowed',
        }
        status_message = status_messages.get(status, 'Error')
        response = (
            f'HTTP/1.1 {status} {status_message}\r\n'
            'Content-Type: text/plain\r\n'
            f'Content-Length: {len(message)}\r\n'
            'Connection: close\r\n'
            '\r\n'
        )
        writer.write(response.encode('utf-8'))
        writer.write(message)
        await writer.drain()

    @staticmethod
    def _format_peer(peername: Optional[object]) -> str:
        if isinstance(peername, tuple) and len(peername) >= 2:
            return f"{peername[0]}:{peername[1]}"
        return str(peername or 'unknown')

async def main():
    server = UnifiedServer(host='0.0.0.0', port=8080)
    
    try:
        await server.start()
    except KeyboardInterrupt:
        await server.stop()

if __name__ == '__main__':
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped")
