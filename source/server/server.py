import asyncio
import sys
import hashlib
import base64
from room_manager import RoomManager
from http_handler import HTTPHandler
from signaling_handler import SignalingHandler
from media_handler import MediaHandler

class UnifiedServer:
    def __init__(self, host='0.0.0.0', port=8080):
        self.host = host
        self.port = port
        self.room_manager = RoomManager()
        self.server = None
        
        self.http_handler = HTTPHandler()
        self.signaling_handler = SignalingHandler(self.room_manager)
        self.media_handler = MediaHandler(self.room_manager)
        
    async def start(self):
        print(f"Server starting on {self.host}:{self.port}")
        
        self.server = await asyncio.start_server(
            self.handle_client,
            self.host,
            self.port
        )
        
        print(f"Server running on {self.host}:{self.port}")
        
        async with self.server:
            await self.server.serve_forever()
    
    async def stop(self):
        if self.server:
            self.server.close()
            await self.server.wait_closed()
    
    async def handle_client(self, reader, writer):
        try:
            request_line = await reader.readline()
            if not request_line:
                writer.close()
                await writer.wait_closed()
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
                if not await self.websocket_handshake(writer, headers):
                    writer.close()
                    await writer.wait_closed()
                    return
                
                if '/signaling' in path:
                    await self.signaling_handler.handle(reader, writer)
                elif '/media' in path:
                    await self.media_handler.handle(reader, writer)
                else:
                    writer.close()
                    await writer.wait_closed()
            else:
                await self.http_handler.handle(writer, method, path)
                
        except Exception as e:
            pass
        finally:
            try:
                if not writer.is_closing():
                    writer.close()
                    await writer.wait_closed()
            except:
                pass
    
    async def websocket_handshake(self, writer, headers):
        try:
            websocket_key = headers.get('sec-websocket-key', '')
            if not websocket_key:
                return False
            
            accept_key = base64.b64encode(
                hashlib.sha1((websocket_key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode()).digest()
            ).decode()
            
            response = (
                'HTTP/1.1 101 Switching Protocols\r\n'
                'Upgrade: websocket\r\n'
                'Connection: Upgrade\r\n'
                f'Sec-WebSocket-Accept: {accept_key}\r\n'
                '\r\n'
            )
            
            writer.write(response.encode('utf-8'))
            await writer.drain()
            
            return True
            
        except Exception as e:
            return False

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
