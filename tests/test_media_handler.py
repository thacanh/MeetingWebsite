import asyncio
import os
import struct
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from source.server.media_handler import MediaHandler
from source.server.room_manager import RoomManager


class FakeWriter:
    def __init__(self):
        self.buffer = bytearray()
        self._closing = False

    def write(self, data: bytes):
        self.buffer.extend(data)

    async def drain(self):
        await asyncio.sleep(0)

    def is_closing(self):
        return self._closing

    def close(self):
        self._closing = True

    async def wait_closed(self):
        self._closing = True


def _build_packet(media_type: int, client_id: str, room_id: str, payload: bytes) -> bytes:
    client_bytes = client_id.encode("utf-8")
    room_bytes = room_id.encode("utf-8")
    packet = bytearray()
    packet.append(media_type)
    packet.append(len(client_bytes))
    packet.extend(client_bytes)
    packet.append(len(room_bytes))
    packet.extend(room_bytes)
    packet.extend(payload)
    return bytes(packet)


async def _run_media_forwarding_test():
    room_manager = RoomManager()
    room_manager.add_client("room", "sender", "Sender")
    room_manager.add_client("room", "receiver", "Receiver")

    handler = MediaHandler(room_manager, queue_size=4)

    sender_writer = FakeWriter()
    receiver_writer = FakeWriter()

    handler._register_client("sender", "room", sender_writer)
    handler._register_client("receiver", "room", receiver_writer)

    pipeline = handler._ensure_room_pipeline("room")

    timestamp = struct.pack("!d", 123.456)
    packet = _build_packet(1, "sender", "room", timestamp + b"payload")

    await handler.handle_packet(packet, sender_writer)

    await asyncio.wait_for(pipeline.queue.join(), timeout=1)

    assert receiver_writer.buffer, "Receiver should have received forwarded frame"
    # WebSocket binary frames start with 0x82 opcode and include payload length
    assert receiver_writer.buffer[0] == 0x82

    stats_key = ("room", "sender", 1)
    tracker = handler._latency_stats[stats_key]
    assert tracker.count == 1
    assert tracker.total_latency >= 0

    await handler.shutdown()


def test_media_forwarding_updates_latency_and_reaches_peers():
    asyncio.run(_run_media_forwarding_test())


async def _run_backpressure_test():
    room_manager = RoomManager()
    room_manager.add_client("room", "sender", "Sender")
    room_manager.add_client("room", "receiver", "Receiver")

    handler = MediaHandler(room_manager, queue_size=1)

    sender_writer = FakeWriter()
    receiver_writer = FakeWriter()

    handler._register_client("sender", "room", sender_writer)
    handler._register_client("receiver", "room", receiver_writer)

    pipeline = handler._ensure_room_pipeline("room")

    gate = asyncio.Event()

    async def slow_send(writer, data):
        await gate.wait()
        writer.write(data)

    handler.send_packet = slow_send  # type: ignore

    packet = _build_packet(1, "sender", "room", b"frame")

    # First packet enqueued and picked by worker but blocked on send
    await handler.handle_packet(packet, sender_writer)
    # Second packet queued while worker still sending first
    await handler.handle_packet(packet, sender_writer)
    # Third packet should trigger drop due to full queue
    await handler.handle_packet(packet, sender_writer)

    assert handler._dropped_frames >= 1

    gate.set()
    await asyncio.wait_for(pipeline.queue.join(), timeout=1)

    await handler.shutdown()


def test_media_backpressure_drops_excess_frames():
    asyncio.run(_run_backpressure_test())
