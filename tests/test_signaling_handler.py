import asyncio
import json
import os

from room_manager import RoomManager
from signaling_handler import SignalingHandler


def build_client_frame(payload: bytes, opcode: int = 0x1) -> bytes:
    mask = os.urandom(4)
    frame = bytearray()
    frame.append(0x80 | opcode)

    payload_len = len(payload)
    if payload_len < 126:
        frame.append(0x80 | payload_len)
    elif payload_len < 65536:
        frame.append(0x80 | 126)
        frame.extend(payload_len.to_bytes(2, 'big'))
    else:
        frame.append(0x80 | 127)
        frame.extend(payload_len.to_bytes(8, 'big'))

    frame.extend(mask)
    frame.extend(bytes(b ^ mask[i % 4] for i, b in enumerate(payload)))
    return bytes(frame)


def build_server_frame_reader():
    async def read_frame(reader: asyncio.StreamReader):
        header = await reader.readexactly(2)
        first, second = header
        opcode = first & 0x0F
        masked = (second & 0x80) != 0
        payload_len = second & 0x7F

        if payload_len == 126:
            payload_len = int.from_bytes(await reader.readexactly(2), 'big')
        elif payload_len == 127:
            payload_len = int.from_bytes(await reader.readexactly(8), 'big')

        masking_key = b''
        if masked:
            masking_key = await reader.readexactly(4)

        payload = await reader.readexactly(payload_len)
        if masked:
            payload = bytes(b ^ masking_key[i % 4] for i, b in enumerate(payload))

        return opcode, payload

    return read_frame


async def send_client_json(writer: asyncio.StreamWriter, message: dict) -> None:
    payload = json.dumps(message).encode('utf-8')
    frame = build_client_frame(payload)
    writer.write(frame)
    await writer.drain()


async def send_client_control(writer: asyncio.StreamWriter, opcode: int, payload: bytes = b'') -> None:
    frame = build_client_frame(payload, opcode=opcode)
    writer.write(frame)
    await writer.drain()


async def read_server_json(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, timeout: float = 1.0) -> dict:
    read_frame = build_server_frame_reader()
    while True:
        opcode, payload = await asyncio.wait_for(read_frame(reader), timeout=timeout)
        if opcode == 0x9:  # ping
            await send_client_control(writer, 0xA, payload)
            continue
        if opcode == 0xA:  # pong
            continue
        if opcode == 0x8:  # close
            return {'type': 'closed'}
        if opcode == 0x1:
            return json.loads(payload.decode('utf-8'))


def test_signaling_join_and_chat():
    async def scenario():
        room_manager = RoomManager()
        handler = SignalingHandler(room_manager, heartbeat_interval=1.0, heartbeat_grace=3.0)

        server = await asyncio.start_server(handler.handle, '127.0.0.1', 0)
        host, port = server.sockets[0].getsockname()[:2]

        reader, writer = await asyncio.open_connection(host, port)

        try:
            connected = await read_server_json(reader, writer)
            assert connected['type'] == 'connected'
            client_id = connected['client_id']

            await send_client_json(writer, {'type': 'join', 'room': 'room1', 'username': 'Alice'})
            room_users = await read_server_json(reader, writer)
            assert room_users['type'] == 'room_users'
            assert {user['username'] for user in room_users['users']} == {'Alice'}

            await send_client_json(writer, {'type': 'chat', 'text': 'Hello'})
            chat = await read_server_json(reader, writer)
            assert chat['type'] == 'chat'
            assert chat['text'] == 'Hello'
            assert chat['client_id'] == client_id

            await send_client_json(writer, {'type': 'ping', 'timestamp': 123})
            pong = await read_server_json(reader, writer)
            assert pong['type'] == 'pong'
            assert pong['timestamp'] == 123

            await send_client_json(writer, {'type': 'unknown'})
            error = await read_server_json(reader, writer)
            assert error['type'] == 'error'
            assert error['error'] == 'unknown_type'

            await send_client_control(writer, 0x8)
        finally:
            writer.close()
            await writer.wait_closed()
            server.close()
            await server.wait_closed()

    asyncio.run(scenario())


def test_signaling_heartbeat_timeout():
    async def scenario():
        room_manager = RoomManager()
        handler = SignalingHandler(room_manager, heartbeat_interval=0.2, heartbeat_grace=0.4)

        server = await asyncio.start_server(handler.handle, '127.0.0.1', 0)
        host, port = server.sockets[0].getsockname()[:2]

        reader, writer = await asyncio.open_connection(host, port)

        async def wait_for_disconnect():
            while True:
                chunk = await reader.read(1024)
                if chunk == b'':
                    break

        try:
            connected = await read_server_json(reader, writer)
            assert connected['type'] == 'connected'

            await asyncio.sleep(1.0)
            await asyncio.wait_for(wait_for_disconnect(), timeout=2.0)
            assert reader.at_eof()
        finally:
            writer.close()
            await writer.wait_closed()
            server.close()
            await server.wait_closed()

    asyncio.run(scenario())
