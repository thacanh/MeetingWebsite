# 🚀 QUICKSTART - Bắt đầu ngay

## Ngày 0: Setup (30 phút)

### 1. Clone & Setup

```bash
# Clone repo
git clone <your-repo-url>
cd assignment-network-project

# Kiểm tra git
git status
git log --oneline -5

# Pull latest changes
git pull origin main
```

### 2. Cài dependencies

```bash
# Python dependencies (cho test)
cd source/server
pip install -r requirements.txt

# Hoặc dùng venv (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

### 3. Test server hiện tại

```bash
# Chạy server
python server.py

# Nếu thấy:
# Server starting on 0.0.0.0:8080
# Server running on 0.0.0.0:8080
# → OK!

# Mở browser: http://localhost:8080
# Mở 2 tabs, join cùng room → test chat
```

### 4. Test các test scripts

```bash
cd test

# Test signaling
python test_signaling.py

# Test media
python test_media.py

# Test HTTP
python test_http.py

# Nếu có lỗi → OK, chưa implement features mới
```

### 5. Tạo branch của mình

```bash
# Quay về root project
cd ../..

# Tạo branch
git checkout -b feature/signaling-enhancement    # Người A
git checkout -b feature/media-optimization        # Người B  
git checkout -b feature/http-infrastructure       # Người C

# Push branch lên remote
git push -u origin <your-branch-name>
```

---

## Phân công cụ thể

### 👤 Người A - Signaling
**Files bạn sẽ edit:**
- `source/server/signaling_handler.py` ⭐ (main)
- `source/server/room_manager.py` ⭐ (main)
- `source/client/js/websocket.js` ⭐ (main)
- `source/server/test/test_signaling.py` (update)

**Files bạn tạo mới:**
- `docs/SIGNALING.md`
- `source/server/test/test_reconnection.py`

**Test command:**
```bash
python test/test_signaling.py
# Mở 2 browsers test chat
```

---

### 👤 Người B - Media Protocol
**Files bạn sẽ edit:**
- `source/server/media_handler.py` ⭐ (main)
- `source/client/js/media.js` ⭐ (main)
- `source/client/index.html` (thêm stats display)
- `source/server/test/test_media.py` (update)

**Files bạn tạo mới:**
- `docs/MEDIA_PROTOCOL.md`
- `source/server/test/test_packet_loss.py`
- `source/client/stats.html` (stats dashboard)

**Test command:**
```bash
python test/test_media.py
python test/test_bandwidth.py
# Chrome DevTools → Network tab → Throttling
```

---

### 👤 Người C - HTTP Infrastructure
**Files bạn sẽ edit:**
- `source/server/http_handler.py` ⭐ (main)
- `source/server/server.py` ⭐ (main)
- `source/server/test/test_http.py` (update)

**Files bạn tạo mới:**
- `source/server/stats_handler.py`
- `docs/HTTP_FEATURES.md`
- `source/client/dashboard.html` (stats UI)

**Test command:**
```bash
python test/test_http.py
python test/test_connections.py
curl -I http://localhost:8080/  # Check headers
```

---

## Daily Workflow

### Mỗi sáng:
```bash
# Check có updates từ main không
git checkout main
git pull origin main

# Merge vào branch của mình (nếu có updates)
git checkout <your-branch>
git merge main

# Hoặc rebase (cleaner history)
git rebase main

# Bắt đầu code
```

### Mỗi tối hoặc sau mỗi feature:
```bash
# Stage changes
git add .

# Check xem đang add gì
git status
git diff --staged

# Commit
git commit -m "feat: implement heartbeat mechanism"

# Push
git push origin <your-branch>

# Check trên GitHub → thấy commit mới
```

### Commit message convention:
```bash
feat: thêm tính năng mới
fix: sửa bug
test: thêm/sửa test
docs: viết documentation
refactor: refactor code (không thay đổi behavior)
perf: cải thiện performance
style: format code (whitespace, etc)
chore: tasks khác (update .gitignore, etc)

# Example:
git commit -m "feat: add ping/pong heartbeat to signaling"
git commit -m "fix: handle WebSocket close frame properly"
git commit -m "test: add reconnection test script"
git commit -m "docs: write signaling protocol specification"
```

---

## Khi gặp vấn đề

### Server không start:
```bash
# Check port có bị chiếm không
netstat -ano | findstr :8080   # Windows
lsof -i :8080                  # Linux/Mac

# Kill process nếu cần
```

### WebSocket không connect:
```bash
# Check browser console (F12)
# Check server logs

# Test bằng curl
curl -i -N -H "Connection: Upgrade" \
     -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Key: test" \
     -H "Sec-WebSocket-Version: 13" \
     http://localhost:8080/signaling
```

### Import errors:
```bash
# Check đang ở đúng directory
pwd  # hoặc cd

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Chạy từ đúng directory
cd source/server
python server.py
```

### Git conflicts:
```bash
# Khi merge/rebase bị conflict:
git status  # Xem files bị conflict

# Edit files, tìm:
<<<<<<< HEAD
your code
=======
their code
>>>>>>> branch-name

# Chọn code nào giữ lại, xóa markers

# Sau khi sửa:
git add <file>
git commit  # (nếu merge)
git rebase --continue  # (nếu rebase)
```

---

## Testing Guidelines

### Test trên localhost:
```bash
# Terminal 1: Server
cd source/server
python server.py

# Terminal 2: Test
cd source/server/test
python test_signaling.py

# Browser: 
# http://localhost:8080
# Mở 2-3 tabs test
```

### Test trên LAN (2 máy):
```bash
# Máy A (server):
# Check IP
ipconfig           # Windows
ifconfig           # Linux/Mac
ip addr show       # Linux modern

# Example: 192.168.1.100

python server.py
# Server running on 0.0.0.0:8080

# Máy B (client):
# Mở browser: http://192.168.1.100:8080
```

### Test network conditions:
```bash
# Chrome DevTools (F12)
# → Network tab
# → Throttling dropdown
# → Choose: Slow 3G, Fast 3G, etc.

# Hoặc Linux tc command:
sudo tc qdisc add dev eth0 root netem delay 100ms loss 5%
# Test...
sudo tc qdisc del dev eth0 root
```

---

## Progress Tracking

### Mỗi ngày tự check:
```markdown
## Ngày 1 - [DD/MM/YYYY]

### Done:
- [x] Task 1
- [x] Task 2

### In Progress:
- [ ] Task 3 (50% done)

### Blocked:
- None

### Tomorrow:
- [ ] Task 3 (finish)
- [ ] Task 4 (start)
```

### Update file progress.md trong branch:
```bash
echo "## Day 1 Progress" >> progress.md
echo "- Implemented heartbeat" >> progress.md
git add progress.md
git commit -m "docs: update progress day 1"
git push
```

---

## Integration Day (Ngày 8)

### Người C merge trước:
```bash
# Người C:
git checkout main
git pull origin main
git merge feature/http-infrastructure
# Test
python server.py
curl http://localhost:8080/
# OK → push
git push origin main
```

### Người A merge:
```bash
# Người A: pull latest main
git checkout main
git pull origin main

# Merge branch của mình
git merge feature/signaling-enhancement
# Resolve conflicts nếu có
# Test
python test/test_signaling.py
# OK → push
git push origin main
```

### Người B merge cuối:
```bash
# Tương tự như trên
git checkout main
git pull origin main
git merge feature/media-optimization
# Test
python test/test_media.py
# OK → push
git push origin main
```

### Cả team test together:
```bash
# Mỗi người mở 1 browser
# Join cùng room "test-room"
# Test:
# - Video streaming
# - Audio
# - Chat
# - Disconnect/reconnect
# - Stats dashboard
```

---

## Demo Preparation

### Record video demo:
```bash
# Windows: Xbox Game Bar (Win + G)
# Mac: QuickTime → New Screen Recording
# Linux: OBS Studio, SimpleScreenRecorder

# Demo checklist:
# 1. Show architecture diagram
# 2. Start server
# 3. Open 2-3 browsers
# 4. Join same room
# 5. Show video/audio/chat
# 6. Show network stats
# 7. Show reconnection
# 8. Show code highlights
```

### Wireshark capture:
```bash
# Install Wireshark

# Capture localhost traffic:
# 1. Start capture on Loopback interface
# 2. Filter: tcp.port == 8080
# 3. Join room, send messages
# 4. Stop capture
# 5. Analyze:
#    - HTTP requests
#    - WebSocket handshake
#    - WebSocket frames
#    - Binary packets

# Save as: demo/network-capture.pcap
```

---

## Tips & Tricks

### Debug WebSocket:
```javascript
// Browser console
const ws = new WebSocket('ws://localhost:8080/signaling');
ws.onopen = () => console.log('Connected');
ws.onmessage = (e) => console.log('Message:', e.data);
ws.onerror = (e) => console.error('Error:', e);
ws.onclose = () => console.log('Closed');
```

### Monitor network:
```bash
# Watch connections
watch -n 1 'netstat -an | grep 8080'

# Monitor bandwidth
iftop -i lo              # Linux
nethogs                  # Linux
Resource Monitor         # Windows

# Packet capture
tcpdump -i lo port 8080 -w capture.pcap
```

### Performance profiling:
```python
# Add to code
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Your code here

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

---

## Useful Commands Cheat Sheet

```bash
# Git
git status
git log --oneline --graph --all
git diff
git diff --staged
git checkout <file>        # Discard changes
git reset HEAD <file>      # Unstage
git stash                  # Temporary save
git stash pop              # Restore

# Python
python -m http.server 8000  # Simple HTTP server
python -m json.tool file.json  # Format JSON
python -i script.py         # Interactive mode after run

# Network
netstat -an | grep 8080
lsof -i :8080
curl -v http://localhost:8080/
curl -I http://localhost:8080/  # Headers only

# Process
ps aux | grep python
kill -9 <PID>
pkill -f "python server.py"

# System
top                        # CPU/Memory
df -h                      # Disk space
du -sh *                   # Directory sizes
```

---

## Resources

### Documentation:
- [RFC 6455 - WebSocket Protocol](https://datatracker.ietf.org/doc/html/rfc6455)
- [Python asyncio docs](https://docs.python.org/3/library/asyncio.html)
- [MDN Web APIs](https://developer.mozilla.org/en-US/docs/Web/API)

### Tools:
- [Wireshark](https://www.wireshark.org/) - Network analysis
- [Postman](https://www.postman.com/) - API testing
- [ngrok](https://ngrok.com/) - Tunneling for remote testing

### Learning:
- [Beej's Guide to Network Programming](https://beej.us/guide/bgnet/)
- [High Performance Browser Networking](https://hpbn.co/)

---

## Support

**Có vấn đề?**
1. Check PLAN.md → Troubleshooting section
2. Search error message trên Google/Stack Overflow
3. Hỏi team members
4. Check server logs
5. Debug với print statements
6. Use debugger (pdb, VSCode debugger)

**Before asking for help:**
- [ ] Đã đọc error message đầy đủ?
- [ ] Đã Google error message?
- [ ] Đã check server logs?
- [ ] Đã test với curl/browser console?
- [ ] Đã commit code gần đây nhất?

---

**Bắt đầu nào! 🚀**

```bash
git checkout -b <your-branch>
# Happy coding!
```

