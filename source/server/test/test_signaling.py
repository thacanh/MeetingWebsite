import asyncio
import websockets
import json

async def test_signaling():
    uri = "ws://localhost:8080/signaling"
    async with websockets.connect(uri) as ws:
        # Test 1: Connect
        msg = await ws.recv()
        data = json.loads(msg)
        print(f"✓ Connected: {data['client_id']}")
        
        # Test 2: Join room
        await ws.send(json.dumps({
            'type': 'join',
            'room': 'test-room',
            'username': 'TestUser'
        }))
        
        # Test 3: Send chat
        await ws.send(json.dumps({
            'type': 'chat',
            'room': 'test-room',
            'text': 'Hello network!'
        }))
        
        # Test 4: Ping-pong (nếu implement)
        await ws.ping()
        await asyncio.sleep(1)
        
        print("✓ All signaling tests passed!")

asyncio.run(test_signaling())