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

            parsed_path = urlparse(request.path).path
            self.logger.info("%s %s %s", request.method, parsed_path, peer_display)

            upgrade = request.headers.get('upgrade', '')
            connection = request.headers.get('connection', '')

            if upgrade.lower() == 'websocket':
                route_handler = self.websocket_routes.get(parsed_path)
                if route_handler is None:
                    self.logger.warning("No WebSocket route for %s from %s", parsed_path, peer_display)
                    await self._send_http_error(writer, 404, b"Not Found")
                    return

                if request.method.upper() != 'GET':
                    self.logger.warning("Invalid method %s for WebSocket upgrade from %s", request.method, peer_display)
                    await self._send_http_error(writer, 405, b"Method Not Allowed")
                    return

                if 'upgrade' not in connection.lower():
                    self.logger.warning("Connection header missing upgrade token from %s", peer_display)
                    await self._send_http_error(writer, 400, b"Bad Request")
                    return

                if not await self._perform_websocket_handshake(writer, request.headers, peer_display):
                    return

                self.logger.info("WebSocket upgraded for %s on %s", peer_display, parsed_path)
                await route_handler(reader, writer)
            else:
                await self.http_handler.handle(writer, request.method, request.path)

        except Exception as exc:
            self.logger.exception("Error handling client %s: %s", peer_display, exc)
        finally:
            try:
                if not writer.is_closing():
                    writer.close()
                await writer.wait_closed()
                self.logger.info("Closed connection to %s", peer_display)
            except Exception:
                self.logger.exception("Failed to close connection to %s", peer_display)

    async def _perform_websocket_handshake(
        self,
        writer: asyncio.StreamWriter,
        headers: Dict[str, str],
        peer_display: str,
    ) -> bool:
        try:
            websocket_key = headers.get('sec-websocket-key')
            if not websocket_key:
                self.logger.warning("Missing Sec-WebSocket-Key from %s", peer_display)
                await self._send_http_error(writer, 400, b"Missing Sec-WebSocket-Key")
                return False

            accept_key = base64.b64encode(
                hashlib.sha1((websocket_key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode('utf-8')).digest()
            ).decode('utf-8')

            response = (
                'HTTP/1.1 101 Switching Protocols\r\n'
                'Upgrade: websocket\r\n'
                'Connection: Upgrade\r\n'
                f'Sec-WebSocket-Accept: {accept_key}\r\n'
                '\r\n'
            )

            writer.write(response.encode('utf-8'))
            await writer.drain()
            self.logger.info("WebSocket handshake successful with %s", peer_display)
            return True
        except Exception as exc:
            self.logger.exception("WebSocket handshake failed with %s: %s", peer_display, exc)
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
