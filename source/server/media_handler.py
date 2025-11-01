import asyncio
import logging
import time
from collections import defaultdict
from dataclasses import dataclass


@dataclass
class _ClientContext:
    writer: asyncio.StreamWriter
    room_id: str


@dataclass
class _MediaPacket:
    sender_id: str
    room_id: str
    media_type: int
    payload: bytes
    arrival_ts: float


@dataclass
class _RoomPipeline:
    queue: asyncio.Queue
    task: asyncio.Task


class _LatencyTracker:
    def __init__(self):
        self.count = 0
        self.total_latency = 0.0
        self.total_jitter = 0.0
        self._last_latency = None

    def update(self, latency: float):
        self.count += 1
        self.total_latency += latency
        jitter = 0.0
        if self._last_latency is not None:
            jitter = abs(latency - self._last_latency)
            self.total_jitter += jitter
        self._last_latency = latency

        avg_latency = self.total_latency / self.count
        avg_jitter = (self.total_jitter / (self.count - 1)) if self.count > 1 else 0.0
        return avg_latency, avg_jitter, jitter


class MediaHandler:
    def __init__(self, room_manager, *, queue_size: int = 256):
        self.room_manager = room_manager
        self.clients: dict[str, _ClientContext] = {}
        self._writer_to_client: dict[int, str] = {}
        self._queue_size = queue_size
        self._room_pipelines: dict[str, _RoomPipeline] = {}
        self._latency_stats: defaultdict[tuple[str, str, int], _LatencyTracker] = defaultdict(_LatencyTracker)
        self._dropped_frames = 0
        self._logger = logging.getLogger(__name__)

    async def handle(self, reader, writer):
        try:
            while True:
                packet = await self.receive_packet(reader)
                if packet is None:
                    break

                await self.handle_packet(packet, writer)

        except asyncio.IncompleteReadError:
            pass
        except Exception:
            self._logger.exception("Unhandled exception while reading media stream")
        finally:
            await self._detach_writer(writer)

    async def shutdown(self):
        """Cancel background tasks and drain queues."""
        for pipeline in list(self._room_pipelines.values()):
            pipeline.task.cancel()
        for pipeline in list(self._room_pipelines.values()):
            try:
                await pipeline.task
            except asyncio.CancelledError:
                pass
        self._room_pipelines.clear()

    async def receive_packet(self, reader):
        try:
            header = await reader.readexactly(2)

            opcode = header[0] & 0x0F
            masked = (header[1] & 0x80) != 0
            payload_len = header[1] & 0x7F

            if opcode == 8:
                return None

            if payload_len == 126:
                payload_len = int.from_bytes(await reader.readexactly(2), 'big')
            elif payload_len == 127:
                payload_len = int.from_bytes(await reader.readexactly(8), 'big')

            masking_key = b''
            if masked:
                masking_key = await reader.readexactly(4)

            payload = await reader.readexactly(payload_len)

            if masked:
                payload = bytes([payload[i] ^ masking_key[i % 4] for i in range(len(payload))])

            return payload

        except asyncio.IncompleteReadError:
            return None
        except Exception:
            self._logger.exception("Failed to receive media packet")
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

        except Exception:
            self._logger.exception("Failed to send media packet")

    async def handle_packet(self, data, sender_writer):
        try:
            packet = self._parse_packet(data, sender_writer)
            if packet is None:
                return

            pipeline = self._ensure_room_pipeline(packet.room_id)
            try:
                pipeline.queue.put_nowait(packet)
            except asyncio.QueueFull:
                self._dropped_frames += 1
                self._logger.warning(
                    "Dropping media frame from %s in room %s due to backpressure",
                    packet.sender_id,
                    packet.room_id,
                )

        except Exception:
            self._logger.exception("Failed to handle incoming media packet")

    def _parse_packet(self, data, sender_writer):
        if len(data) < 3:
            self._logger.warning("Discarding malformed media packet (too small)")
            return None

        offset = 0
        packet_type = data[offset]
        offset += 1

        client_id_len = data[offset]
        offset += 1
        client_id = data[offset:offset + client_id_len].decode('utf-8')
        offset += client_id_len

        room_id_len = data[offset]
        offset += 1
        room_id = data[offset:offset + room_id_len].decode('utf-8')
        offset += room_id_len

        payload = data[offset:]

        self._register_client(client_id, room_id, sender_writer)

        return _MediaPacket(
            sender_id=client_id,
            room_id=room_id,
            media_type=packet_type,
            payload=payload,
            arrival_ts=time.monotonic(),
        )

    def _register_client(self, client_id, room_id, writer):
        self.clients[client_id] = _ClientContext(writer=writer, room_id=room_id)
        self._writer_to_client[id(writer)] = client_id

    def _ensure_room_pipeline(self, room_id: str) -> _RoomPipeline:
        if room_id in self._room_pipelines:
            return self._room_pipelines[room_id]

        queue: asyncio.Queue = asyncio.Queue(maxsize=self._queue_size)
        task = asyncio.create_task(self._room_worker(room_id, queue))
        pipeline = _RoomPipeline(queue=queue, task=task)
        self._room_pipelines[room_id] = pipeline
        return pipeline

    async def _room_worker(self, room_id: str, queue: asyncio.Queue):
        try:
            while True:
                packet: _MediaPacket = await queue.get()
                try:
                    await self._forward_media_packet(packet)
                finally:
                    queue.task_done()

                # When the room becomes empty, stop the worker to release resources
                if not self.room_manager.get_clients_in_room(room_id) and queue.empty():
                    break
        except asyncio.CancelledError:
            pass
        finally:
            self._room_pipelines.pop(room_id, None)

    async def _forward_media_packet(self, packet: _MediaPacket):
        clients_in_room = self.room_manager.get_clients_in_room(packet.room_id)

        sender_bytes = packet.sender_id.encode('utf-8')
        room_bytes = packet.room_id.encode('utf-8')
        framed_payload = bytearray()
        framed_payload.append(packet.media_type)
        framed_payload.append(len(sender_bytes))
        framed_payload.extend(sender_bytes)
        framed_payload.append(len(room_bytes))
        framed_payload.extend(room_bytes)
        framed_payload.extend(packet.payload)

        latency = time.monotonic() - packet.arrival_ts
        stats_key = (packet.room_id, packet.sender_id, packet.media_type)
        avg_latency, avg_jitter, jitter = self._latency_stats[stats_key].update(latency)
        self._logger.debug(
            "Media frame forwarded: room=%s sender=%s type=%s latency=%.3fms jitter=%.3fms avg_latency=%.3fms avg_jitter=%.3fms",
            packet.room_id,
            packet.sender_id,
            packet.media_type,
            latency * 1000.0,
            jitter * 1000.0,
            avg_latency * 1000.0,
            avg_jitter * 1000.0,
        )

        for cid in clients_in_room:
            if cid == packet.sender_id:
                continue
            client_ctx = self.clients.get(cid)
            if not client_ctx:
                continue
            try:
                await self.send_packet(client_ctx.writer, bytes(framed_payload))
            except Exception:
                self._logger.exception("Failed to forward media frame to client %s", cid)

    async def _detach_writer(self, writer):
        client_id = self._writer_to_client.pop(id(writer), None)
        if client_id:
            self.clients.pop(client_id, None)
        if not writer.is_closing():
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
