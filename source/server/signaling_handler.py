import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional


class SignalingHandler:
    def __init__(self, room_manager, heartbeat_interval: float = 15.0, heartbeat_grace: float = 45.0):
        self.room_manager = room_manager
        self.clients: Dict[str, Dict[str, Any]] = {}
        self.heartbeat_interval = heartbeat_interval
        self.heartbeat_grace = heartbeat_grace

    async def handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        client_id = self.generate_client_id()
        self.clients[client_id] = {
            'reader': reader,
            'writer': writer,
            'room': None,
            'username': None,
            'last_seen': datetime.utcnow(),
            'awaiting_pong': False,
        }

        try:
            await self._send_to_client(client_id, {
                'type': 'connected',
                'client_id': client_id
            })

            while True:
                try:
                    raw_message = await asyncio.wait_for(
                        self.receive_message(client_id),
                        timeout=self.heartbeat_interval
                    )
                except asyncio.TimeoutError:
                    if not await self._handle_heartbeat_timeout(client_id):
                        break
                    continue

                if raw_message is None:
                    break

                message, error = self.parse_message(raw_message)
                if error:
                    await self._send_to_client(client_id, {
                        'type': 'error',
                        'error': error
                    })
                    continue

                valid, validation_error = self.validate_message(message, client_id)
                if not valid:
                    await self._send_to_client(client_id, {
                        'type': 'error',
                        'error': validation_error
                    })
                    continue

                await self.handle_message(client_id, message)

        except asyncio.CancelledError:
            raise
        except Exception:
            pass
        finally:
            await self.cleanup_client(client_id)

    async def receive_message(self, client_id: str) -> Optional[str]:
        client = self.clients.get(client_id)
        if not client:
            return None

        reader: asyncio.StreamReader = client['reader']
        writer: asyncio.StreamWriter = client['writer']

        try:
            while True:
                header = await reader.readexactly(2)
                first_byte, second_byte = header
                opcode = first_byte & 0x0F
                masked = (second_byte & 0x80) != 0
                payload_len = second_byte & 0x7F

                if payload_len == 126:
                    payload_len = int.from_bytes(await reader.readexactly(2), 'big')
                elif payload_len == 127:
                    payload_len = int.from_bytes(await reader.readexactly(8), 'big')

                masking_key = b''
                if masked:
                    masking_key = await reader.readexactly(4)

                payload = await reader.readexactly(payload_len)
                if masked:
                    payload = bytes(
                        b ^ masking_key[i % 4]
                        for i, b in enumerate(payload)
                    )

                if opcode == 0x8:  # close
                    return None
                if opcode == 0x9:  # ping
                    await self._send_control_frame(writer, 0xA, payload)
                    self._mark_client_active(client_id)
                    continue
                if opcode == 0xA:  # pong
                    self._mark_client_active(client_id)
                    client['awaiting_pong'] = False
                    continue
                if opcode != 0x1:  # not text
                    continue

                try:
                    text = payload.decode('utf-8')
                except UnicodeDecodeError:
                    await self._send_to_client(client_id, {
                        'type': 'error',
                        'error': 'invalid_utf8'
                    })
                    continue

                self._mark_client_active(client_id)
                return text

        except asyncio.IncompleteReadError:
            return None
        except Exception:
            return None

    async def send_message(self, writer: asyncio.StreamWriter, message: Dict[str, Any]) -> None:
        try:
            if writer.is_closing():
                return

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

        except Exception:
            pass

    async def handle_message(self, client_id: str, message: Dict[str, Any]) -> None:
        msg_type = message.get('type')

        if msg_type == 'join':
            await self.handle_join(client_id, message)
        elif msg_type == 'leave':
            await self.handle_leave(client_id)
        elif msg_type == 'chat':
            await self.handle_chat(client_id, message)
        elif msg_type == 'ping':
            await self._send_to_client(client_id, {
                'type': 'pong',
                'timestamp': message.get('timestamp')
            })

    async def handle_join(self, client_id: str, message: Dict[str, Any]) -> None:
        room_id = message.get('room')
        username = message.get('username') or f'User-{client_id[:8]}'

        await self.handle_leave(client_id)

        self.clients[client_id]['room'] = room_id
        self.clients[client_id]['username'] = username

        await self.room_manager.add_client(room_id, client_id, username, self._create_send_callback(client_id))

        users = await self.room_manager.get_room_users(room_id)
        await self._send_to_client(client_id, {
            'type': 'room_users',
            'users': users
        })

        await self.broadcast_to_room(room_id, {
            'type': 'user_joined',
            'client_id': client_id,
            'username': username
        }, exclude=client_id)

    async def handle_leave(self, client_id: str) -> None:
        client = self.clients.get(client_id)
        if not client:
            return

        room_id = client.get('room')
        username = client.get('username')

        if not room_id:
            return

        client['room'] = None

        removed = await self.room_manager.remove_client(room_id, client_id)
        if removed:
            await self.broadcast_to_room(room_id, {
                'type': 'user_left',
                'client_id': client_id,
                'username': username
            }, exclude=client_id)

    async def handle_chat(self, client_id: str, message: Dict[str, Any]) -> None:
        client = self.clients.get(client_id)
        if not client:
            return

        room_id = client.get('room')
        username = client.get('username')
        text = message.get('text', '')

        if not room_id:
            await self._send_to_client(client_id, {
                'type': 'error',
                'error': 'not_in_room'
            })
            return

        payload = {
            'type': 'chat',
            'client_id': client_id,
            'username': username,
            'text': text,
            'timestamp': datetime.utcnow().isoformat()
        }
        await self.broadcast_to_room(room_id, payload)

    async def broadcast_to_room(self, room_id: str, message: Dict[str, Any], exclude: Optional[str] = None) -> None:
        await self.room_manager.broadcast(room_id, message, exclude=exclude)

    async def cleanup_client(self, client_id: str) -> None:
        client = self.clients.get(client_id)
        if not client:
            return

        await self.handle_leave(client_id)

        writer: asyncio.StreamWriter = client['writer']
        if not writer.is_closing():
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

        self.clients.pop(client_id, None)

    def parse_message(self, raw_message: str) -> (Optional[Dict[str, Any]], Optional[str]):
        try:
            message = json.loads(raw_message)
        except json.JSONDecodeError:
            return None, 'invalid_json'

        if not isinstance(message, dict):
            return None, 'invalid_message_format'

        return message, None

    def validate_message(self, message: Dict[str, Any], client_id: str) -> (bool, Optional[str]):
        msg_type = message.get('type')
        if not isinstance(msg_type, str):
            return False, 'missing_type'

        if msg_type == 'join':
            room = message.get('room')
            if not isinstance(room, str) or not room.strip():
                return False, 'invalid_room'
            username = message.get('username')
            if username is not None and (not isinstance(username, str) or not username.strip()):
                return False, 'invalid_username'
        elif msg_type == 'leave':
            pass
        elif msg_type == 'chat':
            text = message.get('text')
            if not isinstance(text, str) or not text.strip():
                return False, 'invalid_text'
            client = self.clients.get(client_id)
            if not client or not client.get('room'):
                return False, 'not_in_room'
        elif msg_type == 'ping':
            pass
        else:
            return False, 'unknown_type'

        return True, None

    def _create_send_callback(self, client_id: str):
        async def send(message: Dict[str, Any]) -> None:
            await self._send_to_client(client_id, message)
        return send

    async def _send_to_client(self, client_id: str, message: Dict[str, Any]) -> None:
        client = self.clients.get(client_id)
        if not client:
            return
        writer: asyncio.StreamWriter = client['writer']
        await self.send_message(writer, message)

    async def _handle_heartbeat_timeout(self, client_id: str) -> bool:
        client = self.clients.get(client_id)
        if not client:
            return False

        now = datetime.utcnow()
        last_seen: datetime = client.get('last_seen', now)
        awaiting_pong = client.get('awaiting_pong', False)

        if awaiting_pong and (now - last_seen) > timedelta(seconds=self.heartbeat_grace):
            return False

        await self._send_ping(client_id)
        client['awaiting_pong'] = True
        return True

    async def _send_ping(self, client_id: str) -> None:
        client = self.clients.get(client_id)
        if not client:
            return
        payload = os.urandom(4)
        await self._send_control_frame(client['writer'], 0x9, payload)

    async def _send_control_frame(self, writer: asyncio.StreamWriter, opcode: int, payload: bytes = b'') -> None:
        try:
            if writer.is_closing():
                return

            frame = bytearray()
            frame.append(0x80 | opcode)
            frame.append(len(payload))
            frame.extend(payload)

            writer.write(frame)
            await writer.drain()
        except Exception:
            pass

    def _mark_client_active(self, client_id: str) -> None:
        client = self.clients.get(client_id)
        if not client:
            return
        client['last_seen'] = datetime.utcnow()
        client['awaiting_pong'] = False

    def generate_client_id(self) -> str:
        import uuid
        return str(uuid.uuid4())
