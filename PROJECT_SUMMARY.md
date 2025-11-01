# 📊 DỰ ÁN VIDEO CALL - TÓM TẮT NHANH

## 🎯 MỤC TIÊU 1 DÒNG
**3 người implement 3 modules lập trình mạng độc lập, merge lại thành 1 app video call hoàn chỉnh trong 9 ngày.**

---

## 👥 PHÂN CÔNG

```
┌─────────────────────────────────────────────────────────────────┐
│                        DỰ ÁN VIDEO CALL                         │
└────────────┬──────────────────┬──────────────────┬──────────────┘
             │                  │                  │
   ┌─────────▼────────┐  ┌─────▼──────┐  ┌───────▼────────┐
   │   NGƯỜI A        │  │  NGƯỜI B   │  │   NGƯỜI C      │
   │   Signaling      │  │   Media    │  │     HTTP       │
   └─────────┬────────┘  └─────┬──────┘  └───────┬────────┘
             │                  │                  │
   ┌─────────▼────────┐  ┌─────▼──────┐  ┌───────▼────────┐
   │ • Ping/Pong      │  │ • Binary   │  │ • ETag Cache   │
   │ • Reconnect      │  │   Protocol │  │ • Gzip         │
   │ • Room Auth      │  │ • Adaptive │  │ • Timeout      │
   │ • Msg History    │  │   Quality  │  │ • Stats API    │
   └──────────────────┘  └────────────┘  └────────────────┘
```

---

## 📅 TIMELINE

```
┌──────────┬────────────────────────────────────────────────┐
│  Ngày 0  │  Setup: Clone repo, tạo branches              │
├──────────┼────────────────────────────────────────────────┤
│ Ngày 1-2 │  Code core features (mỗi người làm riêng)     │
├──────────┼────────────────────────────────────────────────┤
│ Ngày 3-4 │  Code advanced features                        │
├──────────┼────────────────────────────────────────────────┤
│ Ngày 5-6 │  Testing & optimization                        │
├──────────┼────────────────────────────────────────────────┤
│  Ngày 7  │  Individual testing, write docs               │
├──────────┼────────────────────────────────────────────────┤
│  Ngày 8  │  Merge all branches, integration test         │
├──────────┼────────────────────────────────────────────────┤
│  Ngày 9  │  Final testing, prepare demo                  │
└──────────┴────────────────────────────────────────────────┘
```

---

## 🎯 NGƯỜI A - SIGNALING & ROOM

### Làm gì?
Implement WebSocket protocol cho signaling (join/leave/chat) với advanced features.

### Features:
1. **Heartbeat Mechanism** (Ngày 1-2)
   - Server ping mỗi 30s
   - Client phải pong trong 10s
   - Auto close nếu timeout

2. **Auto-Reconnection** (Ngày 1-2)
   - Exponential backoff: 1s, 2s, 4s, 8s...
   - Queue messages khi offline
   - Resend khi reconnect

3. **Room Authentication** (Ngày 3-4)
   - Password protection
   - Max capacity (10 users)
   - Reject unauthorized

4. **Message History** (Ngày 5-6)
   - Store last 100 messages
   - Send history on join
   - Timestamp ordering

### Files:
- `signaling_handler.py` ⭐
- `room_manager.py` ⭐
- `websocket.js` ⭐
- `docs/SIGNALING.md`

### Test:
```bash
python test/test_signaling.py
# 2 browsers join same room
# Disconnect WiFi, wait 10s, reconnect
```

---

## 🎯 NGƯỜI B - MEDIA & PROTOCOL

### Làm gì?
Implement custom binary protocol cho video/audio streaming với quality adaptation.

### Features:
1. **Enhanced Binary Protocol** (Ngày 1-2)
   ```
   [type][seq][timestamp][size][quality][client_id][room_id][payload]
     1B   4B      8B       2B      1B        NB        MB       XB
   ```

2. **Packet Loss Detection** (Ngày 3-4)
   - Track sequence numbers
   - Detect gaps
   - Calculate loss rate

3. **Adaptive Quality** (Ngày 4-5)
   - Measure RTT every 5s
   - Adjust JPEG quality:
     - RTT < 50ms → quality 0.9
     - RTT 50-100ms → quality 0.7
     - RTT > 100ms → quality 0.4

4. **Network Stats** (Ngày 6)
   - Display on UI:
     - Packets sent/received
     - RTT avg/min/max
     - Loss rate
     - Current quality

### Files:
- `media_handler.py` ⭐
- `media.js` ⭐
- `stats.html`
- `docs/MEDIA_PROTOCOL.md`

### Test:
```bash
python test/test_media.py
python test/test_bandwidth.py
# Chrome DevTools → Throttle network
# Check stats update real-time
```

---

## 🎯 NGƯỜI C - HTTP & INFRASTRUCTURE

### Làm gì?
Enhance HTTP server với caching, compression và monitoring.

### Features:
1. **HTTP Caching** (Ngày 1-2)
   - Generate ETag (MD5 hash)
   - Return 304 Not Modified
   - Cache-Control headers

2. **Gzip Compression** (Ngày 2-3)
   - Check Accept-Encoding
   - Compress if size > 1KB
   - Content-Encoding header

3. **Connection Management** (Ngày 3-4)
   - Idle timeout (30s)
   - Graceful shutdown
   - Keep-alive support

4. **Stats Endpoint** (Ngày 4-5)
   - `/stats` API returning JSON
   - Dashboard HTML
   - WebSocket real-time update

5. **Logging** (Ngày 6)
   - Request logging
   - Error logging
   - Log rotation

### Files:
- `http_handler.py` ⭐
- `server.py` ⭐
- `stats_handler.py`
- `dashboard.html`
- `docs/HTTP_FEATURES.md`

### Test:
```bash
python test/test_http.py
curl -I http://localhost:8080/  # Check headers
ab -n 1000 -c 10 http://localhost:8080/  # Load test
```

---

## 🔄 GIT WORKFLOW

```
main branch
    │
    ├─── feature/signaling-enhancement (Người A)
    │        │
    │        └── commit 1, 2, 3...
    │
    ├─── feature/media-optimization (Người B)
    │        │
    │        └── commit 1, 2, 3...
    │
    └─── feature/http-infrastructure (Người C)
             │
             └── commit 1, 2, 3...

Ngày 8: Merge C → main → merge A → main → merge B → main
```

### Commands:
```bash
# Daily
git add .
git commit -m "feat: implement heartbeat"
git push origin <your-branch>

# Merge day
git checkout main
git merge <branch>
git push origin main
```

---

## 🧪 TESTING STRATEGY

### Level 1: Unit Tests (Mỗi người)
```bash
python test/test_<module>.py
```

### Level 2: Integration (Cả team)
```bash
# 2 browsers, same room
http://localhost:8080
```

### Level 3: Network Conditions
- Localhost: RTT ~5ms
- LAN: RTT ~20ms
- Throttled: RTT 100-400ms

### Level 4: Load Test
```bash
# 10+ concurrent users
# Monitor CPU, memory, bandwidth
```

---

## 📊 SUCCESS METRICS

```
┌──────────────────────┬──────────┬──────────┬──────────┐
│       Metric         │   Min    │   Good   │ Excellent│
├──────────────────────┼──────────┼──────────┼──────────┤
│ Users per room       │    2     │     5    │    10+   │
│ Video quality        │   480p   │   640p   │   720p   │
│ RTT (localhost)      │  <100ms  │  <50ms   │  <20ms   │
│ Packet loss          │   <5%    │   <1%    │  <0.1%   │
│ Test coverage        │   70%    │   80%    │   90%+   │
│ Code comments        │  Some    │   Good   │ Excellent│
│ Documentation pages  │    3     │     5    │     7+   │
└──────────────────────┴──────────┴──────────┴──────────┘
```

---

## 📁 FILES TO CREATE/EDIT

### Người A:
```
✏️  source/server/signaling_handler.py
✏️  source/server/room_manager.py
✏️  source/client/js/websocket.js
✏️  source/server/test/test_signaling.py
📄 docs/SIGNALING.md
📄 source/server/test/test_reconnection.py
```

### Người B:
```
✏️  source/server/media_handler.py
✏️  source/client/js/media.js
✏️  source/server/test/test_media.py
✏️  source/server/test/test_bandwidth.py
📄 docs/MEDIA_PROTOCOL.md
📄 source/server/test/test_packet_loss.py
📄 source/client/stats.html
```

### Người C:
```
✏️  source/server/http_handler.py
✏️  source/server/server.py
✏️  source/server/test/test_http.py
✏️  source/server/test/test_connections.py
📄 source/server/stats_handler.py
📄 docs/HTTP_FEATURES.md
📄 source/client/dashboard.html
```

**Legend:**
- ✏️  = Edit existing file
- 📄 = Create new file

---

## 📚 DOCUMENTATION FILES

```
📂 Docs structure:
│
├── README.md                 (Original)
├── README_PROJECT.md         (Project overview) ⭐ READ FIRST
├── PLAN.md                   (Detailed plan) ⭐ READ SECOND
├── QUICKSTART.md             (Getting started) ⭐ READ THIRD
├── CONTRIBUTION.md           (Daily tracking)
├── PROJECT_SUMMARY.md        (This file - Quick reference)
│
└── docs/
    ├── ARCHITECTURE.md       (System design)
    ├── TEMPLATE_PERSON.md    (Doc template)
    ├── SIGNALING.md          (A writes)
    ├── MEDIA_PROTOCOL.md     (B writes)
    └── HTTP_FEATURES.md      (C writes)
```

---

## 🎯 KEY CONCEPTS - LẬP TRÌNH MẠNG

### 1. WebSocket Protocol (RFC 6455)
```
Client                          Server
  │                               │
  ├─ HTTP Upgrade ──────────────→ │
  │                               │
  │ ←──── 101 Switching ──────────┤
  │                               │
  ├─ Text Frame (opcode 0x1) ───→ │  (Signaling)
  ├─ Binary Frame (opcode 0x2) ─→ │  (Media)
  ├─ Ping (opcode 0x9) ─────────→ │
  │ ←──── Pong (opcode 0xA) ──────┤
  │                               │
```

### 2. Binary Protocol
```
Packet structure:
┌────┬──────┬───────────┬──────┬─────────┬──────────┬─────────┬─────────┐
│Type│  Seq │ Timestamp │ Size │ Quality │ClientID  │ RoomID  │ Payload │
│ 1B │  4B  │    8B     │  2B  │   1B    │ var len  │ var len │ var len │
└────┴──────┴───────────┴──────┴─────────┴──────────┴─────────┴─────────┘
```

### 3. HTTP Caching
```
Request 1:
GET /app.js → Server calculates ETag → 200 OK + ETag: "abc123"

Request 2:
GET /app.js + If-None-Match: "abc123" → Server checks → 304 Not Modified
```

### 4. Connection Lifecycle
```
┌─────────────────────────────────────────────────────┐
│  1. TCP Connect                                     │
│  2. WebSocket Handshake                             │
│  3. Data Transfer (frames)                          │
│  4. Heartbeat (ping/pong)                           │
│  5. Timeout or Close frame → Disconnect            │
└─────────────────────────────────────────────────────┘
```

---

## ✅ DAILY CHECKLIST

### Mỗi ngày:
```
Morning:
□ Pull latest main
□ Review yesterday's code
□ Plan today's tasks

During day:
□ Code features
□ Write tests as you go
□ Add comments
□ Commit frequently

Evening:
□ Run tests
□ Fix bugs
□ Commit & push
□ Update CONTRIBUTION.md
```

---

## 🚨 COMMON PITFALLS

### ❌ Don't:
- Copy code không hiểu
- Commit code chưa test
- Edit files của người khác (trừ khi discuss)
- Merge mà chưa test
- Bỏ qua documentation

### ✅ Do:
- Test mỗi feature nhỏ
- Commit với message rõ ràng
- Ask khi không chắc
- Review code của nhau
- Document as you code

---

## 🎬 DEMO CHECKLIST

```
□ Video recorded (5 phút)
□ Slides prepared (10 slides)
□ Wireshark capture saved
□ Performance report written
□ All code commented
□ All docs complete
□ All tests passing
□ Ready to present!
```

---

## 📞 NEED HELP?

```
1. Check README_PROJECT.md → File structure
2. Check PLAN.md → Detailed tasks
3. Check QUICKSTART.md → Setup guide
4. Check docs/ARCHITECTURE.md → System design
5. Ask team members
6. Debug with print/console.log
7. Google the error
8. Check Stack Overflow
```

---

## 🎓 LEARNING OUTCOMES

Sau khi hoàn thành, bạn sẽ hiểu:

**Network Programming:**
- ✅ TCP socket programming
- ✅ WebSocket protocol implementation
- ✅ Binary protocol design
- ✅ HTTP caching mechanisms
- ✅ Connection management
- ✅ Network error handling

**Software Engineering:**
- ✅ Git branching workflow
- ✅ Code review process
- ✅ Testing strategies
- ✅ Documentation practices
- ✅ Team collaboration

**Performance:**
- ✅ Bandwidth optimization
- ✅ Latency reduction
- ✅ Quality adaptation
- ✅ Load testing

---

## 🏆 FINAL DELIVERABLES

```
✅ Working video call app (3+ users)
✅ All tests passing
✅ Complete documentation (7+ files)
✅ Demo video & slides
✅ Network analysis (Wireshark)
✅ Performance report
✅ Clean git history
✅ Professional presentation
```

---

## 💡 TIPS FOR SUCCESS

1. **Start early** - Don't wait until last minute
2. **Test frequently** - Catch bugs early
3. **Communicate** - Update team daily
4. **Document** - Write as you code
5. **Review** - Check each other's code
6. **Optimize** - Don't over-engineer
7. **Focus** - Stick to assigned tasks
8. **Help** - Support teammates

---

## 🎯 YOUR NEXT STEPS

```bash
# 1. Read all docs
cat README_PROJECT.md
cat PLAN.md
cat QUICKSTART.md

# 2. Setup
git checkout -b <your-branch>
pip install -r source/server/requirements.txt

# 3. Test current code
python source/server/server.py
# Open http://localhost:8080

# 4. Start coding!
# Follow PLAN.md for your module

# 5. Update progress daily
# Edit CONTRIBUTION.md

# 6. Merge day
# Follow QUICKSTART.md → Integration section

# 7. Demo day
# Present your work confidently!
```

---

**GOOD LUCK! 🚀**

You got this! 💪

---

## 📊 QUICK REFERENCE TABLE

| Need | File | Section |
|------|------|---------|
| Overview | README_PROJECT.md | All |
| Detailed plan | PLAN.md | Your role section |
| Setup guide | QUICKSTART.md | Setup + Daily workflow |
| Architecture | docs/ARCHITECTURE.md | All |
| Progress tracking | CONTRIBUTION.md | Your section |
| Quick lookup | PROJECT_SUMMARY.md | This file |
| Git help | QUICKSTART.md | Git commands |
| Test help | QUICKSTART.md | Testing section |
| Troubleshoot | QUICKSTART.md | Troubleshooting |
| Template | docs/TEMPLATE_PERSON.md | Copy this |

---

**Version:** 1.0  
**Last updated:** [Date]  
**Quick ref for:** Team A, B, C

