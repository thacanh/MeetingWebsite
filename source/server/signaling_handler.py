import asyncio
import json
from datetime import datetime

class SignalingHandler:
    def __init__(self, room_manager):
        self.room_manager = room_manager
        self.clients = {}
    
    async def handle(self, reader, writer):
        client_id = self.generate_client_id()
        
        self.clients[client_id] = {
            'reader': reader,
            'writer': writer,
            'room': None,
            'username': None
        }
        
        try:
            await self.send_message(writer, {
                'type': 'connected',
                'client_id': client_id
            })
            
            while True:
                message = await self.receive_message(reader)
                if message is None:
                    break
                
                await self.handle_message(client_id, message)
                
        except Exception as e:
            pass
        finally:
            await self.cleanup_client(client_id)
    
    async def receive_message(self, reader):
        try:
            header = await reader.readexactly(2)
            
            fin = (header[0] & 0x80) != 0
            opcode = header[0] & 0x0F
            masked = (header[1] & 0x80) != 0
            payload_len = header[1] & 0x7F
            
            if opcode == 8:
                return None
            
            if payload_len == 126:
                payload_len = int.from_bytes(await reader.readexactly(2), 'big')
            elif payload_len == 127:
                payload_len = int.from_bytes(await reader.readexactly(8), 'big')
            
            if masked:
                masking_key = await reader.readexactly(4)
            
            payload = await reader.readexactly(payload_len)
            
            if masked:
                payload = bytes([payload[i] ^ masking_key[i % 4] for i in range(len(payload))])
            
            message_str = payload.decode('utf-8')
            return json.loads(message_str)
            
        except asyncio.IncompleteReadError:
            return None
        except Exception as e:
            return None
    
    async def send_message(self, writer, message):
        try:
            payload = json.dumps(message).encode('utf-8')
            
            frame = bytearray()
            frame.append(0x81)
            
            payload_len = len(payload)
            if payload_len < 126:
                frame.append(payload_len)
            elif payload_len < 65536:
                frame.append(126)
                frame.extend(payload_len.to_bytes(2, 'big'))
            else:
                frame.append(127)
                frame.extend(payload_len.to_bytes(8, 'big'))
            
            frame.extend(payload)
            
            writer.write(frame)
            await writer.drain()
            
        except Exception as e:
            pass
    
    async def handle_message(self, client_id, message):
        msg_type = message.get('type')
        
        if msg_type == 'join':
            await self.handle_join(client_id, message)
        elif msg_type == 'leave':
            await self.handle_leave(client_id)
        elif msg_type == 'chat':
            await self.handle_chat(client_id, message)
    
    async def handle_join(self, client_id, message):
        room_id = message.get('room')
        username = message.get('username', f'User-{client_id[:8]}')
        
        self.clients[client_id]['room'] = room_id
        self.clients[client_id]['username'] = username
        
        self.room_manager.add_client(room_id, client_id, username)
        
        users = self.room_manager.get_room_users(room_id)
        
        await self.send_message(self.clients[client_id]['writer'], {
            'type': 'room_users',
            'users': users
        })
        
        await self.broadcast_to_room(room_id, {
            'type': 'user_joined',
            'client_id': client_id,
            'username': username
        }, exclude=client_id)
    
    async def handle_leave(self, client_id):
        if client_id not in self.clients:
            return
        
        room_id = self.clients[client_id]['room']
        username = self.clients[client_id]['username']
        
        if room_id:
            self.room_manager.remove_client(room_id, client_id)
            
            await self.broadcast_to_room(room_id, {
                'type': 'user_left',
                'client_id': client_id,
                'username': username
            })
    
    async def handle_chat(self, client_id, message):
        if client_id not in self.clients:
            return
        
        room_id = self.clients[client_id]['room']
        username = self.clients[client_id]['username']
        text = message.get('text', '')
        
        if room_id and text:
            await self.broadcast_to_room(room_id, {
                'type': 'chat',
                'client_id': client_id,
                'username': username,
                'text': text,
                'timestamp': datetime.now().isoformat()
            })
    
    async def broadcast_to_room(self, room_id, message, exclude=None):
        clients_in_room = self.room_manager.get_clients_in_room(room_id)
        
        for cid in clients_in_room:
            if cid != exclude and cid in self.clients:
                try:
                    await self.send_message(self.clients[cid]['writer'], message)
                except Exception as e:
                    pass
    
    async def cleanup_client(self, client_id):
        if client_id in self.clients:
            await self.handle_leave(client_id)
            del self.clients[client_id]
    
    def generate_client_id(self):
        import uuid
        return str(uuid.uuid4())
