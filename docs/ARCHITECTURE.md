# Architecture Overview

## Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────┐
│                   Browser                        │
│  ┌───────────┐  ┌───────────┐  ┌──────────┐   │
│  │ app.js    │  │ websocket │  │ media.js │   │
│  │ (main)    │  │ (signal)  │  │ (binary) │   │
│  └─────┬─────┘  └─────┬─────┘  └────┬─────┘   │
└────────┼──────────────┼─────────────┼──────────┘
         │              │              │
         │ HTTP         │ WS Text      │ WS Binary
         │              │              │
┌────────▼──────────────▼──────────────▼──────────┐
│              Python Server (Port 8080)           │
│  ┌─────────────────────────────────────────┐   │
│  │           UnifiedServer                  │   │
│  │  - TCP socket server (asyncio)          │   │
│  │  - WebSocket handshake                  │   │
│  │  - Route: HTTP vs WS                    │   │
│  └────────┬─────────┬──────────┬────────────┘   │
│           │         │          │                 │
│  ┌────────▼─┐  ┌───▼────┐  ┌──▼──────────┐     │
│  │ HTTP     │  │Signaling│  │   Media     │     │
│  │ Handler  │  │ Handler │  │   Handler   │     │
│  └──────────┘  └────┬────┘  └──────┬──────┘     │
│                     │               │            │
│                ┌────▼───────────────▼───┐        │
│                │    RoomManager         │        │
│                │  - Users per room      │        │
│                │  - Message history     │        │
│                └────────────────────────┘        │
└──────────────────────────────────────────────────┘
```

## Luồng dữ liệu

### 1. HTTP Request (Static files)
```
Browser → TCP:8080 → HTTPHandler → read file → return 200
```

### 2. WebSocket Signaling (JSON)
```
Browser → WS:8080/signaling → SignalingHandler
  ↓
  ├─ join    → RoomManager.add_client()
  ├─ chat    → broadcast to room
  └─ leave   → RoomManager.remove_client()
```

### 3. WebSocket Media (Binary)
```
Browser → WS:8080/media → MediaHandler
  ↓
  ├─ Decode packet header
  ├─ Extract: type, seq, timestamp, client_id, room_id, payload
  └─ Forward to all users in room (except sender)
```

## Protocol Specifications

### WebSocket Frame Format (RFC 6455)
```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-------+-+-------------+-------------------------------+
|F|R|R|R| opcode|M| Payload len |    Extended payload length    |
|I|S|S|S|  (4)  |A|     (7)     |             (16/64)           |
|N|V|V|V|       |S|             |   (if payload len==126/127)   |
| |1|2|3|       |K|             |                               |
+-+-+-+-+-------+-+-------------+ - - - - - - - - - - - - - - - +
|     Extended payload length continued, if payload len == 127  |
+ - - - - - - - - - - - - - - - +-------------------------------+
|                               |Masking-key, if MASK set to 1  |
+-------------------------------+-------------------------------+
| Masking-key (continued)       |          Payload Data         |
+-------------------------------- - - - - - - - - - - - - - - - +
:                     Payload Data continued ...                :
+ - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - +
|                     Payload Data continued ...                |
+---------------------------------------------------------------+
```

**Opcodes:**
- 0x1: Text frame (Signaling uses this)
- 0x2: Binary frame (Media uses this)
- 0x8: Close
- 0x9: Ping
- 0xA: Pong

### Custom Media Packet Format (v2)
```
Offset  Size  Field           Description
------  ----  -----           -----------
0       1     type            1=video, 2=audio
1       4     sequence        uint32 packet number
5       8     timestamp       uint64 milliseconds since epoch
13      2     payload_size    uint16 bytes
15      1     quality         0-9 (JPEG quality level)
16      1     client_id_len   Length of client ID
17      N     client_id       UTF-8 string
17+N    1     room_id_len     Length of room ID
18+N    M     room_id         UTF-8 string
18+N+M  X     payload         Video/audio data
```

## Network Programming Concepts

### 1. TCP Socket Server (UnifiedServer)
- Listen on `0.0.0.0:8080`
- Accept connections
- Read HTTP/WebSocket request
- Route to appropriate handler

### 2. WebSocket Protocol Implementation
- **Handshake:** HTTP Upgrade + Sec-WebSocket-Key
- **Framing:** FIN, opcode, mask, payload length
- **Masking:** Client must mask, server must not
- **Control frames:** Ping, Pong, Close

### 3. Binary Protocol Design
- **Header:** Fixed fields for parsing
- **Length-prefixed strings:** Variable length data
- **Big-endian:** Network byte order
- **Payload:** Raw bytes (JPEG, Float32Array)

### 4. Error Handling
- Connection timeout (30s idle)
- WebSocket close frames
- Exception handling at each layer
- Graceful degradation

## Performance Considerations

### Bandwidth Usage
```
Video: 640x480 JPEG @ 15fps, quality 0.6
  ≈ 10-20KB per frame
  ≈ 150-300KB/s = 1.2-2.4 Mbps

Audio: 48kHz mono @ 4096 samples
  ≈ 16KB per chunk @ 12 chunks/sec
  ≈ 192KB/s = 1.5 Mbps

Total per user: ~3-4 Mbps upload + (3-4 Mbps * N users) download
```

### Latency Components
```
Total latency = Capture + Encode + Network + Decode + Render

Capture:     ~16ms (60fps camera)
Encode:      ~10ms (Canvas.toBlob)
Network:     <5ms (localhost), 20-100ms (LAN/Internet)
Decode:      ~5ms (JPEG decode)
Render:      ~16ms (requestAnimationFrame)

Expected:    50-150ms end-to-end
```

### Scalability Limits
Current architecture (single-threaded):
- ~10 concurrent users per room
- ~5 rooms simultaneously
- ~50 total connections

Bottlenecks:
1. CPU (JPEG encoding on client)
2. Network bandwidth (upload on each client)
3. Memory (video buffers)

## Security Considerations

### Current Implementation
- ❌ No encryption (cleartext WebSocket)
- ❌ No authentication
- ❌ No input validation
- ⚠️  Path traversal protection in HTTPHandler

### Recommendations (Future)
- [ ] WSS (WebSocket Secure) with TLS
- [ ] Token-based authentication
- [ ] Rate limiting per client
- [ ] Input sanitization
- [ ] CORS headers
- [ ] AES encryption for media (as mentioned in README)

## Testing Strategy

### Unit Tests
- Individual handler functions
- Protocol encoding/decoding
- Room management logic

### Integration Tests
- WebSocket connection flow
- Media packet forwarding
- HTTP caching logic

### End-to-End Tests
- 2+ browsers in same room
- Video/audio transmission
- Chat functionality

### Network Tests
- Bandwidth measurement
- RTT measurement
- Packet loss simulation
- Connection timeout

## References
- RFC 6455: The WebSocket Protocol
- RFC 2616: HTTP/1.1
- Python asyncio documentation
- Canvas API (MDN)
- WebRTC concepts (for reference, not used)

