# 📋 KẾ HOẠCH DỰ ÁN - TEAM 3 NGƯỜI

## 🎯 MỤC TIÊU
Phát triển ứng dụng Video Call với custom protocol (không WebRTC API), mỗi người phụ trách 1 module độc lập có liên quan đến lập trình mạng.

---

## 👥 PHÂN CÔNG NHIỆM VỤ

### 🔵 NGƯỜI A - WebSocket Signaling & Room Management
**Branch:** `feature/signaling-enhancement`  
**Thời gian:** 5-7 ngày  
**Độ khó:** ⭐⭐⭐

#### Nhiệm vụ:

##### 1. Heartbeat Mechanism (Ngày 1-2)
- [ ] Implement ping/pong protocol trong `signaling_handler.py`
  - Server gửi PING frame mỗi 30s
  - Client phải trả lời PONG trong 10s
  - Đóng connection nếu không nhận PONG
- [ ] Client-side reconnection trong `websocket.js`
  - Exponential backoff (1s, 2s, 4s, 8s, max 30s)
  - Message queue khi offline
  - Tự động gửi lại messages khi reconnect

**Code mẫu:**
```python
# signaling_handler.py
async def heartbeat_loop(self, client_id):
    while client_id in self.clients:
        try:
            await self.send_ping(client_id)
            await asyncio.sleep(30)
        except:
            break

async def send_ping(self, client_id):
    writer = self.clients[client_id]['writer']
    # WebSocket PING frame (opcode 0x9)
    frame = bytearray([0x89, 0x00])  # FIN=1, opcode=9, no payload
    writer.write(frame)
    await writer.drain()
```

##### 2. Room Authentication (Ngày 3-4)
- [ ] Thêm room password/token system
  - Hash password với SHA256
  - Validate trước khi join
  - Broadcast error nếu sai password
- [ ] Room capacity limits
  - Max 10 users per room
  - Return error khi full

##### 3. Message Persistence (Ngày 5-6)
- [ ] Lưu 100 messages gần nhất trong `room_manager.py`
- [ ] Gửi history khi user mới join
- [ ] Implement message ordering với timestamp

##### 4. Testing & Documentation (Ngày 7)
- [ ] Chạy `test_signaling.py` - pass 100%
- [ ] Test với 2 browsers khác nhau
- [ ] Test reconnection: Tắt WiFi 10s rồi bật lại
- [ ] Viết README cho module

#### Deliverables:
```
✅ signaling_handler.py (enhanced)
✅ room_manager.py (với message history)
✅ websocket.js (với reconnection)
✅ test_signaling_advanced.py
✅ SIGNALING.md (documentation)
```

#### Test checklist:
- [ ] 2 clients connect → thấy nhau
- [ ] Client disconnect → server nhận biết sau 40s (30s + 10s timeout)
- [ ] Reconnect → nhận lại messages cũ
- [ ] 5 users cùng room → chat OK
- [ ] Wrong password → reject

---

### 🟢 NGƯỜI B - Binary Media Protocol & Streaming
**Branch:** `feature/media-optimization`  
**Thời gian:** 5-7 ngày  
**Độ khó:** ⭐⭐⭐⭐

#### Nhiệm vụ:

##### 1. Enhanced Binary Protocol (Ngày 1-2)
- [ ] Thêm header fields trong `media_handler.py`:
  ```
  [1 byte] type (1=video, 2=audio)
  [4 bytes] sequence number (uint32)
  [8 bytes] timestamp (uint64 milliseconds)
  [2 bytes] payload size (uint16)
  [1 byte] quality level (0-9)
  [1 byte] client_id_len
  [N bytes] client_id
  [1 byte] room_id_len  
  [M bytes] room_id
  [X bytes] payload
  ```
- [ ] Implement packet decoder với struct unpacking

**Code mẫu:**
```python
def encode_packet_v2(self, type, sequence, timestamp, quality, payload):
    header = struct.pack(
        '!BIQHBBnBm',  # Format string
        type,
        sequence,
        timestamp,
        len(payload),
        quality,
        len(self.client_id),
        self.client_id.encode(),
        len(self.room_id),
        self.room_id.encode()
    )
    return header + payload
```

##### 2. Packet Loss Detection (Ngày 3-4)
- [ ] Track sequence numbers
- [ ] Detect gaps trong sequence
- [ ] Log packet loss rate
- [ ] Request retransmission (optional)

##### 3. Adaptive Quality (Ngày 4-5)
- [ ] Measure RTT mỗi 5s
- [ ] Đếm packets sent/received
- [ ] Tính packet loss rate
- [ ] Thay đổi JPEG quality:
  - RTT < 50ms, loss < 1% → quality = 0.9
  - RTT 50-100ms, loss < 5% → quality = 0.7
  - RTT > 100ms, loss > 5% → quality = 0.4

```javascript
// media.js
adaptQuality() {
    const lossRate = this.packetsLost / this.packetsSent;
    const rtt = this.lastRTT;
    
    if (rtt < 50 && lossRate < 0.01) {
        this.quality = 0.9;
    } else if (rtt < 100 && lossRate < 0.05) {
        this.quality = 0.7;
    } else {
        this.quality = 0.4;
    }
}
```

##### 4. Network Statistics (Ngày 6)
- [ ] Thu thập metrics:
  - Packets sent/received
  - Bytes sent/received
  - RTT avg/min/max
  - Loss rate
  - Current quality
- [ ] Hiển thị lên UI (update mỗi 1s)

##### 5. Testing (Ngày 7)
- [ ] `test_media.py` - verify protocol
- [ ] `test_bandwidth.py` - measure throughput
- [ ] Test với Chrome DevTools Network throttling
- [ ] Wireshark capture & analyze packets

#### Deliverables:
```
✅ media_handler.py (enhanced protocol)
✅ media.js (adaptive quality)
✅ stats-display.html (network stats UI)
✅ test_packet_loss.py
✅ MEDIA_PROTOCOL.md (documentation)
```

#### Test checklist:
- [ ] Gửi 1000 frames → nhận đủ (hoặc detect loss)
- [ ] Sequence numbers tăng dần liên tục
- [ ] RTT < 50ms trên localhost
- [ ] Quality thay đổi khi throttle network
- [ ] Stats update real-time trên UI

---

### 🔴 NGƯỜI C - HTTP Server & Network Infrastructure
**Branch:** `feature/http-infrastructure`  
**Thời gian:** 5-7 ngày  
**Độ khó:** ⭐⭐⭐

#### Nhiệm vụ:

##### 1. HTTP Caching (Ngày 1-2)
- [ ] Implement ETag trong `http_handler.py`
  - Generate MD5 hash của file content
  - Return 304 Not Modified nếu match
- [ ] Add Cache-Control headers
  - Static files: `max-age=3600`
  - HTML: `no-cache`
- [ ] Support If-None-Match header

**Code mẫu:**
```python
import hashlib

def generate_etag(self, content):
    return hashlib.md5(content).hexdigest()

async def serve_file_with_cache(self, writer, path, headers):
    # Read file
    content = self.read_file(path)
    etag = self.generate_etag(content)
    
    # Check If-None-Match
    if headers.get('if-none-match') == etag:
        return await self.send_304(writer, etag)
    
    # Send with ETag
    await self.send_200(writer, content, {
        'ETag': etag,
        'Cache-Control': 'max-age=3600'
    })
```

##### 2. Gzip Compression (Ngày 2-3)
- [ ] Detect Accept-Encoding header
- [ ] Compress response nếu size > 1KB
- [ ] Add Content-Encoding: gzip

##### 3. Connection Management (Ngày 3-4)
- [ ] Implement idle timeout (30s)
- [ ] Connection pooling tracking
- [ ] Graceful shutdown handler
- [ ] Keep-alive support

##### 4. Stats Endpoint (Ngày 4-5)
- [ ] Tạo `/stats` endpoint return JSON:
  ```json
  {
    "active_connections": 15,
    "total_requests": 1234,
    "rooms": [
      {"id": "room1", "users": 3},
      {"id": "room2", "users": 2}
    ],
    "uptime_seconds": 3600,
    "bandwidth": {
      "sent_mb": 123.45,
      "received_mb": 98.76
    }
  }
  ```
- [ ] Tạo dashboard HTML hiển thị stats
- [ ] WebSocket real-time update stats

##### 5. Logging & Monitoring (Ngày 6)
- [ ] Log mỗi request: `[timestamp] method path status_code duration_ms`
- [ ] Error logging với traceback
- [ ] Rotate log files

##### 6. Testing (Ngày 7)
- [ ] `test_http.py` - verify caching
- [ ] `test_connections.py` - verify timeout
- [ ] Load test với 100 concurrent requests
- [ ] Monitor với `netstat`

#### Deliverables:
```
✅ http_handler.py (với caching, gzip)
✅ server.py (với connection management)
✅ stats_handler.py (new file)
✅ dashboard.html (stats visualization)
✅ HTTP_FEATURES.md (documentation)
```

#### Test checklist:
- [ ] Request 2 lần → lần 2 return 304
- [ ] Large file → compressed
- [ ] Idle 35s → connection closed
- [ ] `/stats` return correct data
- [ ] 100 concurrent requests → tất cả OK
- [ ] Dashboard update real-time

---

## 🔄 WORKFLOW GIT

### Setup (Ngày 0)
```bash
# Mọi người làm cùng:
git clone <repo>
cd assignment-network-project

# Check git status
git status
git branch

# Mỗi người tạo branch của mình
git checkout -b feature/signaling-enhancement  # Người A
git checkout -b feature/media-optimization      # Người B
git checkout -b feature/http-infrastructure     # Người C
```

### Daily Work (Ngày 1-6)
```bash
# Mỗi sáng:
git pull origin main  # Update từ main (nếu có)

# Code code code...

# Mỗi tối:
git add .
git commit -m "feat: implement heartbeat mechanism"
git push origin <your-branch>

# Convention commit messages:
# feat: thêm feature mới
# fix: sửa bug
# test: thêm test
# docs: viết documentation
# refactor: refactor code
```

### Testing (Ngày 7)
```bash
# Mỗi người test riêng branch của mình:
python source/server/test/test_signaling.py     # A
python source/server/test/test_media.py         # B
python source/server/test/test_http.py          # C

# Tất cả phải PASS
```

### Integration (Ngày 8-9)

#### Thứ tự merge:
```bash
# 1. Người C merge trước (infrastructure)
git checkout main
git pull origin feature/http-infrastructure
# Test
python server.py
# Check http://localhost:8080

# 2. Người A merge (signaling)
git pull origin feature/signaling-enhancement
# Test WebSocket
python test/test_signaling.py

# 3. Người B merge (media)
git pull origin feature/media-optimization
# Test end-to-end
# Mở 2 browsers test video call

# 4. Final testing
# Cả team cùng test:
# - 3 người mỗi người mở 1 browser
# - Join cùng room
# - Test video, audio, chat
# - Disconnect/reconnect
# - Monitor stats
```

### Conflict Resolution
```bash
# Nếu có conflict:
git checkout main
git pull origin main
git checkout <your-branch>
git merge main

# Sửa conflicts thủ công
# Test lại
git add .
git commit -m "fix: resolve merge conflicts"
git push origin <your-branch>
```

---

## 📊 TIMELINE TỔNG QUAN

```
Ngày 0 (Setup):
├─ Clone repo
├─ Tạo branches
└─ Setup môi trường

Ngày 1-6 (Development):
├─ Người A: Signaling features
├─ Người B: Media protocol
└─ Người C: HTTP infrastructure

Ngày 7 (Individual Testing):
├─ Mỗi người test branch riêng
├─ Fix bugs
└─ Write documentation

Ngày 8 (Integration):
├─ Merge theo thứ tự C → A → B
├─ Resolve conflicts
└─ Integration testing

Ngày 9 (Final Testing & Demo):
├─ End-to-end testing
├─ Performance testing
├─ Prepare demo
└─ Write final report
```

---

## ✅ CHECKLIST CUỐI CÙNG

### Cả team phải đảm bảo:

#### Chức năng:
- [ ] 3 users có thể join cùng room
- [ ] Video/audio streaming hoạt động
- [ ] Chat messages real-time
- [ ] Reconnection sau disconnect
- [ ] Stats dashboard hiển thị đúng

#### Lập trình mạng:
- [ ] WebSocket protocol implementation (A)
- [ ] Binary protocol với custom header (B)
- [ ] HTTP caching & compression (C)
- [ ] Connection management (C)
- [ ] Network error handling (All)

#### Testing:
- [ ] All test scripts pass
- [ ] Test với 2+ máy khác nhau (LAN)
- [ ] Test với network throttling
- [ ] Load test 10+ concurrent users

#### Documentation:
- [ ] README.md updated
- [ ] Mỗi người có 1 file .md giải thích module
- [ ] Code có comments đầy đủ
- [ ] API documentation (nếu cần)

#### Demo:
- [ ] Video demo hoạt động (record màn hình)
- [ ] Slide giải thích kiến trúc
- [ ] Giải thích lập trình mạng đã làm
- [ ] Show network stats/monitoring

---

## 🎯 DELIVERABLES CUỐI CÙNG

### Code:
```
source/
├── server/
│   ├── server.py (enhanced by C)
│   ├── http_handler.py (enhanced by C)
│   ├── signaling_handler.py (enhanced by A)
│   ├── media_handler.py (enhanced by B)
│   ├── room_manager.py (enhanced by A)
│   ├── stats_handler.py (new by C)
│   └── test/
│       ├── test_signaling.py
│       ├── test_media.py
│       ├── test_http.py
│       ├── test_bandwidth.py
│       └── test_connections.py
└── client/
    ├── js/
    │   ├── websocket.js (enhanced by A)
    │   ├── media.js (enhanced by B)
    │   ├── app.js
    │   └── chat.js
    └── dashboard.html (new by C)
```

### Documentation:
```
docs/
├── SIGNALING.md (Người A)
├── MEDIA_PROTOCOL.md (Người B)
├── HTTP_FEATURES.md (Người C)
├── ARCHITECTURE.md (Cả team)
└── TESTING.md (Cả team)
```

### Demo:
```
demo/
├── video-demo.mp4
├── slides.pdf
├── network-analysis.pcap (Wireshark capture)
└── performance-report.pdf
```

---

## 🔥 TIPS & BEST PRACTICES

### Người A (Signaling):
- Dùng `asyncio.create_task()` cho heartbeat
- Test reconnection bằng cách tắt WiFi
- Log tất cả WebSocket frames để debug

### Người B (Media):
- Dùng `struct.pack/unpack` cho binary data
- Monitor với Chrome DevTools Performance
- Test với different image sizes (640x480, 320x240)

### Người C (HTTP):
- Dùng `hashlib.md5()` cho ETag
- Test caching với curl: `curl -H "If-None-Match: xxx"`
- Monitor connections với `netstat -an | grep 8080`

### Tất cả:
- Commit thường xuyên (mỗi feature nhỏ)
- Write tests trước khi code (TDD)
- Comment giải thích network logic
- Handle exceptions properly
- Log errors với traceback

---

## 🆘 TROUBLESHOOTING

### Conflicts khi merge:
```bash
# Keep both changes
git checkout --ours file.py   # Giữ code của mình
git checkout --theirs file.py # Giữ code của người khác

# Hoặc edit thủ công
# Tìm <<<<<<, ======, >>>>>> và sửa
```

### Test fail:
1. Check server đang chạy: `netstat -an | grep 8080`
2. Check logs: `tail -f server.log`
3. Debug với print statements
4. Dùng Wireshark capture packets

### Performance issues:
1. Profile với `cProfile`
2. Check CPU/memory: `top` hoặc Task Manager
3. Reduce frame rate nếu lag
4. Implement frame dropping

---

## 📞 COMMUNICATION

### Daily standup (10 phút mỗi ngày):
1. Hôm qua làm gì?
2. Hôm nay làm gì?
3. Có blocker không?

### Code review:
- Mỗi pull request phải có 1 người review
- Check logic, performance, security
- Test code trước khi approve

### Kênh liên lạc:
- Discord/Telegram cho daily chat
- GitHub Issues cho bug tracking
- Pull Request cho code review

---

Bắt đầu từ **Ngày 0** nhé! Good luck! 🚀

