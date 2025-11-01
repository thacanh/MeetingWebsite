# 📚 TÀI LIỆU DỰ ÁN - VIDEO CALL SYSTEM

> **Dự án:** Ứng dụng gọi video real-time với custom protocol (no WebRTC API)  
> **Team:** 3 người (A, B, C)  
> **Timeline:** 9 ngày  
> **Mục tiêu:** Mỗi người implement 1 module lập trình mạng độc lập

---

## 📂 CẤU TRÚC TÀI LIỆU

```
📁 assignment-network-project/
│
├── 📄 README.md                  ← Giới thiệu project gốc
├── 📄 PLAN.md                    ⭐ KẾ HOẠCH CHI TIẾT (ĐỌC NGAY)
├── 📄 QUICKSTART.md              ⭐ HƯỚNG DẪN BẮT ĐẦU (ĐỌC THỨ 2)
├── 📄 CONTRIBUTION.md            ← Tracking progress
├── 📄 .gitignore                 ← Git ignore rules
│
├── 📁 docs/
│   ├── ARCHITECTURE.md           ← Kiến trúc hệ thống
│   ├── TEMPLATE_PERSON.md        ← Template viết docs
│   ├── SIGNALING.md              ← (Người A viết)
│   ├── MEDIA_PROTOCOL.md         ← (Người B viết)
│   └── HTTP_FEATURES.md          ← (Người C viết)
│
├── 📁 source/
│   ├── 📁 server/
│   │   ├── server.py             ← TCP server (Người C)
│   │   ├── http_handler.py       ← HTTP logic (Người C)
│   │   ├── signaling_handler.py  ← Signaling (Người A)
│   │   ├── media_handler.py      ← Media binary (Người B)
│   │   ├── room_manager.py       ← Room logic (Người A)
│   │   ├── requirements.txt      ← Python dependencies
│   │   └── 📁 test/
│   │       ├── test_signaling.py
│   │       ├── test_media.py
│   │       ├── test_http.py
│   │       ├── test_bandwidth.py
│   │       └── test_connections.py
│   │
│   └── 📁 client/
│       ├── index.html
│       ├── 📁 js/
│       │   ├── app.js
│       │   ├── websocket.js      ← (Người A)
│       │   ├── media.js          ← (Người B)
│       │   └── chat.js
│       └── 📁 css/
│           └── style.css
│
└── 📁 statics/
    └── diagram.png               ← Sơ đồ hệ thống
```

---

## 🎯 BẮT ĐẦU TỪ ĐÂU?

### Lần đầu đọc? Follow thứ tự này:

```
1️⃣ Đọc file này (README_PROJECT.md) để nắm tổng quan
   ↓
2️⃣ Đọc PLAN.md để hiểu chi tiết kế hoạch và phân công
   ↓
3️⃣ Đọc QUICKSTART.md để setup môi trường
   ↓
4️⃣ Đọc docs/ARCHITECTURE.md để hiểu kiến trúc
   ↓
5️⃣ Bắt đầu code theo phần của mình trong PLAN.md
   ↓
6️⃣ Update CONTRIBUTION.md hàng ngày
   ↓
7️⃣ Viết docs riêng theo TEMPLATE_PERSON.md
```

---

## 👥 PHÂN CÔNG NHANH

| Người | Module | Branch | Files chính |
|-------|--------|--------|-------------|
| **A** | Signaling & Room | `feature/signaling-enhancement` | `signaling_handler.py`, `room_manager.py`, `websocket.js` |
| **B** | Media & Protocol | `feature/media-optimization` | `media_handler.py`, `media.js` |
| **C** | HTTP & Infrastructure | `feature/http-infrastructure` | `http_handler.py`, `server.py` |

### Người A - WebSocket Signaling (⏱️ 5-7 ngày)
**Nhiệm vụ lập trình mạng:**
- ✅ Heartbeat ping/pong mechanism
- ✅ Auto-reconnection với exponential backoff
- ✅ Room authentication
- ✅ Message history & persistence

**Deliverables:**
- Enhanced signaling_handler.py
- Enhanced websocket.js
- docs/SIGNALING.md
- Test scripts

---

### Người B - Binary Media Protocol (⏱️ 5-7 ngày)
**Nhiệm vụ lập trình mạng:**
- ✅ Custom binary protocol với header
- ✅ Packet loss detection & sequence tracking
- ✅ Adaptive quality based on network
- ✅ Network statistics (RTT, loss rate, bandwidth)

**Deliverables:**
- Enhanced media_handler.py
- Enhanced media.js
- docs/MEDIA_PROTOCOL.md
- Stats dashboard UI

---

### Người C - HTTP Server & Infrastructure (⏱️ 5-7 ngày)
**Nhiệm vụ lập trình mạng:**
- ✅ HTTP caching (ETag, Cache-Control)
- ✅ Gzip compression
- ✅ Connection pooling & timeout
- ✅ Stats endpoint & monitoring

**Deliverables:**
- Enhanced http_handler.py
- Enhanced server.py
- docs/HTTP_FEATURES.md
- Dashboard HTML

---

## 🔄 WORKFLOW

### Setup (Ngày 0)
```bash
git clone <repo>
cd assignment-network-project
git checkout -b <your-branch>
pip install -r source/server/requirements.txt
```

### Daily (Ngày 1-6)
```bash
# Morning
git pull origin main

# Code...

# Evening
git add .
git commit -m "feat: ..."
git push origin <your-branch>
```

### Testing (Ngày 7)
```bash
cd source/server/test
python test_<your_module>.py
# Must pass 100%
```

### Integration (Ngày 8)
```bash
# Merge order: C → A → B
git checkout main
git merge <branch>
# Test together
```

### Demo (Ngày 9)
- 3 người mỗi người mở 1 browser
- Join cùng room
- Demo video/audio/chat
- Show stats & reconnection
- Present code & architecture

---

## 🧪 TESTING

### Run all tests:
```bash
cd source/server

# Signaling
python test/test_signaling.py

# Media
python test/test_media.py
python test/test_bandwidth.py

# HTTP
python test/test_http.py
python test/test_connections.py
```

### Browser testing:
```
1. Start server: python server.py
2. Open: http://localhost:8080
3. Open 2+ tabs
4. Join same room
5. Test video/audio/chat
```

### Network testing:
```
- Chrome DevTools → Network → Throttling
- Wireshark capture packets
- netstat monitor connections
```

---

## 📊 PROGRESS TRACKING

Cập nhật hàng ngày trong `CONTRIBUTION.md`:

```markdown
### [DD/MM/YYYY] - Day X

#### Người A:
Yesterday: Implemented heartbeat
Today: Working on reconnection
Blockers: None

#### Người B:
Yesterday: Designed packet format
Today: Implementing packet loss detection
Blockers: None

#### Người C:
Yesterday: Added ETag support
Today: Implementing gzip compression
Blockers: None
```

---

## ✅ CHECKLIST CUỐI CÙNG

### Chức năng:
- [ ] 3+ users join cùng room
- [ ] Video streaming works
- [ ] Audio streaming works
- [ ] Chat real-time
- [ ] Reconnection after disconnect
- [ ] Stats dashboard hiển thị

### Lập trình mạng:
- [ ] WebSocket protocol implementation
- [ ] Binary protocol custom header
- [ ] HTTP caching & compression
- [ ] Connection management
- [ ] Error handling

### Testing:
- [ ] All tests pass
- [ ] Test trên 2+ máy (LAN)
- [ ] Test với throttling
- [ ] Load test

### Documentation:
- [ ] SIGNALING.md (A)
- [ ] MEDIA_PROTOCOL.md (B)
- [ ] HTTP_FEATURES.md (C)
- [ ] Code comments đầy đủ

### Demo:
- [ ] Video demo recorded
- [ ] Slides prepared
- [ ] Wireshark capture
- [ ] Performance report

---

## 🛠️ TOOLS

**Development:**
- Python 3.8+
- Modern browser (Chrome/Firefox)
- Git
- Text editor/IDE

**Testing:**
- Browser DevTools
- curl
- Python websockets library
- requests library

**Network Analysis:**
- Wireshark
- tcpdump
- netstat/ss
- iftop (Linux)

**Optional:**
- ngrok (remote testing)
- Apache Bench (load testing)
- Postman (API testing)

---

## 📚 LEARNING RESOURCES

### Network Programming:
- [RFC 6455 - WebSocket Protocol](https://datatracker.ietf.org/doc/html/rfc6455)
- [Beej's Guide to Network Programming](https://beej.us/guide/bgnet/)
- [High Performance Browser Networking](https://hpbn.co/)

### Python:
- [asyncio documentation](https://docs.python.org/3/library/asyncio.html)
- [socket programming tutorial](https://realpython.com/python-sockets/)

### Web APIs:
- [MDN WebSockets](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [MDN Canvas API](https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API)
- [MDN Media Capture](https://developer.mozilla.org/en-US/docs/Web/API/Media_Capture_and_Streams_API)

---

## 🎯 SUCCESS METRICS

### Minimum (Pass):
- ✅ 2 users can video call
- ✅ Chat works
- ✅ All tests pass
- ✅ Documentation complete

### Good:
- ✅ Above + 3+ users
- ✅ Reconnection works
- ✅ Stats dashboard
- ✅ Performance optimized

### Excellent:
- ✅ Above + Network analysis
- ✅ Load testing results
- ✅ Advanced features (adaptive quality)
- ✅ Professional demo

---

## 🆘 TROUBLESHOOTING

### Port already in use:
```bash
# Windows
netstat -ano | findstr :8080
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8080
kill -9 <PID>
```

### WebSocket won't connect:
1. Check server is running
2. Check browser console (F12)
3. Check firewall
4. Try different browser

### Git conflicts:
1. `git status` to see conflicts
2. Edit files, remove `<<<<<<<`, `=======`, `>>>>>>>`
3. `git add <file>`
4. `git commit`

### Tests fail:
1. Check server is running
2. Check dependencies installed
3. Check logs
4. Debug with print statements

**More help:** See QUICKSTART.md → Troubleshooting section

---

## 📞 COMMUNICATION

**Daily standups:** 10 phút mỗi ngày  
**Code review:** Required before merge  
**Questions:** Ask trong group chat  
**Blockers:** Báo ngay để team support

---

## 🎓 EXPECTATIONS

**Mỗi người phải:**
1. ✅ Code module của mình
2. ✅ Viết tests
3. ✅ Viết documentation
4. ✅ Review code của người khác
5. ✅ Contribute vào demo

**Không được:**
- ❌ Copy code từ Internet không hiểu
- ❌ Commit code không test
- ❌ Merge mà không thông báo
- ❌ Bỏ viết documentation

**Mục tiêu:**
- 📚 Học lập trình mạng thực chiến
- 💻 Xây dựng app hoàn chỉnh
- 🤝 Làm việc nhóm hiệu quả
- 🎯 Đạt điểm cao môn học

---

## 🚀 LET'S GO!

```bash
# Bước 1: Đọc PLAN.md kỹ
cat PLAN.md

# Bước 2: Đọc QUICKSTART.md
cat QUICKSTART.md

# Bước 3: Setup
git checkout -b <your-branch>
pip install -r source/server/requirements.txt

# Bước 4: Start coding!
code .
```

---

**Good luck team! 💪**

**Questions?** 
- Đọc lại docs
- Search trong files
- Ask team
- Debug carefully
- Test frequently
- Commit often

**Remember:**
> "The best way to learn networking is to implement it yourself!"

---

**Last updated:** [Date]  
**Version:** 1.0  
**Authors:** Team A, B, C

