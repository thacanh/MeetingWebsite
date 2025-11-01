# Ứng dụng gọi video thời gian thực (WebRTC + STUN/TURN + AES động)

## Tổng quan
- Truyền **video/audio** qua WebRTC (SRTP, DTLS).
- **Signaling** qua WebSocket (Python).
- **STUN/TURN** tự cấu hình (coturn) để xuyên NAT.
- **Chat + DataChannel** có **mã hoá AES-GCM** và **xoay khoá theo thời gian**.

## Chạy nhanh (localhost/LAN)
```bash
cd source/server
pip install -r requirements.txt
python server.py
```
Mở trình duyệt: http://localhost:8000  
Mở 2 tab, nhập **Room ID** giống nhau → thấy nhau + chat.

## Demo nhiều máy (cùng Wi‑Fi)
- Trên máy chạy server, lấy IP LAN (vd `172.11.59.61`).
- Máy khác mở: `http://<IP_LAN>:8000`.
- WebSocket auto theo `location.hostname:8765`.

**Lưu ý mobile:** Chrome trên điện thoại yêu cầu **HTTPS** nếu truy cập qua IP LAN để cấp cam/mic. Xem `source/server/README.md` để dùng ngrok nhanh.

## Dùng TURN (xuyên NAT)
- Dựng coturn theo `source/server/turn_config.md`.
- Cập nhật ICE servers trong `source/client/app.js`.

## Cấu trúc
- `statics/diagram.png` – Sơ đồ hệ thống
- `source/client/` – Frontend WebRTC + AES DataChannel
- `source/server/` – Python signaling + HTTP static
- `source/scripts/` – Script đo lường (tùy chọn)
