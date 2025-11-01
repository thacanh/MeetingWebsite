import asyncio

class MediaHandler:
    def __init__(self, room_manager):
        self.room_manager = room_manager
        self.clients = {}
    
    async def handle(self, reader, writer):
        try:
            while True:
                packet = await self.receive_packet(reader)
                if packet is None:
                    break
                
                await self.handle_packet(packet, writer)
                
        except Exception as e:
            pass
    
    async def receive_packet(self, reader):
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
            
            return payload
            
        except asyncio.IncompleteReadError:
            return None
        except Exception as e:
            return None
    
    async def send_packet(self, writer, data):
        try:
            frame = bytearray()
            frame.append(0x82)
            
            payload_len = len(data)
            if payload_len < 126:
                frame.append(payload_len)
            elif payload_len < 65536:
                frame.append(126)
                frame.extend(payload_len.to_bytes(2, 'big'))
            else:
                frame.append(127)
                frame.extend(payload_len.to_bytes(8, 'big'))
            
            frame.extend(data)
            
            writer.write(frame)
            await writer.drain()
            
        except Exception as e:
            pass
    
    async def handle_packet(self, data, sender_writer):
        try:
            offset = 0
            packet_type = data[offset]
            offset += 1
            
            client_id_len = data[offset]
            offset += 1
            client_id = data[offset:offset+client_id_len].decode('utf-8')
            offset += client_id_len
            
            room_id_len = data[offset]
            offset += 1
            room_id = data[offset:offset+room_id_len].decode('utf-8')
            offset += room_id_len
            
            payload = data[offset:]
            
            if client_id not in self.clients:
                self.clients[client_id] = {
                    'writer': sender_writer,
                    'room': room_id
                }
            
            if packet_type == 1:
                await self.forward_media(client_id, room_id, 1, payload)
            elif packet_type == 2:
                await self.forward_media(client_id, room_id, 2, payload)
            
        except Exception as e:
            pass
    
    async def forward_media(self, sender_id, room_id, media_type, payload):
        clients_in_room = self.room_manager.get_clients_in_room(room_id)
        
        sender_id_bytes = sender_id.encode('utf-8')
        packet = bytearray()
        packet.append(media_type)
        packet.append(len(sender_id_bytes))
        packet.extend(sender_id_bytes)
        packet.extend(payload)
        
        for cid in clients_in_room:
            if cid != sender_id and cid in self.clients:
                try:
                    await self.send_packet(self.clients[cid]['writer'], bytes(packet))
                except Exception as e:
                    pass
