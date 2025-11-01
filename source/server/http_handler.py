import os
import mimetypes

class HTTPHandler:
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.client_dir = os.path.normpath(os.path.join(current_dir, '..', 'client'))
        
        if not os.path.exists(self.client_dir):
            os.makedirs(self.client_dir, exist_ok=True)
    
    async def handle(self, writer, method, path):
        if method != 'GET':
            await self.send_response(writer, 405, b"Method Not Allowed")
            return
        
        await self.serve_file(writer, path)
    
    async def serve_file(self, writer, path):
        if path == '/' or path == '':
            path = '/index.html'
        
        path = path.lstrip('/')
        file_path = os.path.normpath(os.path.join(self.client_dir, path))
        
        try:
            real_client_dir = os.path.realpath(self.client_dir)
            real_file_path = os.path.realpath(file_path)
            
            if not real_file_path.startswith(real_client_dir):
                await self.send_response(writer, 403, b"Forbidden")
                return
        except Exception as e:
            await self.send_response(writer, 403, b"Forbidden")
            return
        
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            await self.send_response(writer, 404, b"Not Found")
            return
        
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            content_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
            
            response = f"HTTP/1.1 200 OK\r\n"
            response += f"Content-Type: {content_type}\r\n"
            response += f"Content-Length: {len(content)}\r\n"
            response += "Connection: close\r\n"
            response += "\r\n"
            
            writer.write(response.encode('utf-8'))
            writer.write(content)
            await writer.drain()
            
        except Exception as e:
            await self.send_response(writer, 500, b"Internal Server Error")
    
    async def send_response(self, writer, status_code, body):
        status_messages = {
            200: "OK",
            400: "Bad Request",
            403: "Forbidden",
            404: "Not Found",
            405: "Method Not Allowed",
            500: "Internal Server Error"
        }
        
        status_message = status_messages.get(status_code, "Unknown")
        
        response = f"HTTP/1.1 {status_code} {status_message}\r\n"
        response += "Content-Type: text/plain\r\n"
        response += f"Content-Length: {len(body)}\r\n"
        response += "Connection: close\r\n"
        response += "\r\n"
        
        writer.write(response.encode('utf-8'))
        writer.write(body)
        await writer.drain()
