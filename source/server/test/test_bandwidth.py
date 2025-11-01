# tests/test_bandwidth.py
import asyncio
import websockets
import time

async def measure_bandwidth():
    uri = "ws://localhost:8080/media"
    
    # Test với packets khác nhau
    sizes = [1024, 10240, 102400]  # 1KB, 10KB, 100KB
    
    for size in sizes:
        async with websockets.connect(uri) as ws:
            data = b"\x00" * size
            
            start = time.time()
            for i in range(100):
                await ws.send(data)
            elapsed = time.time() - start
            
            bandwidth = (size * 100 * 8) / elapsed / 1_000_000  # Mbps
            print(f"Size: {size}B - Bandwidth: {bandwidth:.2f} Mbps")

asyncio.run(measure_bandwidth())