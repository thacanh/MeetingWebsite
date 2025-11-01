import asyncio
import websockets
import struct

async def test_media_protocol():
    uri = "ws://localhost:8080/media"
    async with websockets.connect(uri) as ws:
        # Test packet encoding
        client_id = b"test-client-123"
        room_id = b"room1"
        fake_video = b"\xff\xd8\xff\xe0" + b"\x00" * 100  # JPEG header
        
        # Encode packet
        packet = bytearray()
        packet.append(1)  # Video type
        packet.append(len(client_id))
        packet.extend(client_id)
        packet.append(len(room_id))
        packet.extend(room_id)
        packet.extend(fake_video)
        
        # Send
        await ws.send(bytes(packet))
        print(f"✓ Sent {len(packet)} bytes")
        
        # Measure RTT
        import time
        start = time.time()
        await ws.ping()
        rtt = (time.time() - start) * 1000
        print(f"✓ RTT: {rtt:.2f}ms")

asyncio.run(test_media_protocol())