# [Module Name] - Documentation

**Author:** [Tên bạn]  
**Branch:** [feature/xxx]  
**Date:** [DD/MM/YYYY]

---

## 📌 Mục tiêu

[Mô tả ngắn gọn module của bạn làm gì]

---

## 🔧 Các tính năng đã implement

### 1. [Tên tính năng 1]

**Mô tả:**  
[Giải thích tính năng này làm gì]

**Lập trình mạng liên quan:**  
[Giải thích phần network programming: socket, protocol, data format, etc.]

**Code chính:**
```python
# Paste code snippet quan trọng
```

**Test:**
```bash
python test/test_xxx.py
```

**Kết quả:**
```
✓ Test 1 passed
✓ Test 2 passed
```

---

### 2. [Tên tính năng 2]

[Lặp lại như trên]

---

## 📊 Performance & Metrics

| Metric | Value | Target |
|--------|-------|--------|
| RTT | 10ms | <50ms |
| Throughput | 2.5 Mbps | >1 Mbps |
| Packet loss | 0.1% | <1% |
| CPU usage | 15% | <50% |

---

## 🐛 Bugs & Issues đã fix

### Bug 1: [Tên bug]
**Triệu chứng:** [Mô tả lỗi]  
**Nguyên nhân:** [Tại sao bị lỗi]  
**Fix:** [Đã sửa như thế nào]

---

## 🧪 Testing Process

### Test Setup:
```bash
# Commands để setup môi trường test
```

### Test Cases:

| Test Case | Input | Expected Output | Status |
|-----------|-------|-----------------|--------|
| TC1 | ... | ... | ✅ Pass |
| TC2 | ... | ... | ✅ Pass |

### Test với Network Conditions:

**Localhost:**
- RTT: ~5ms
- Loss: 0%
- Result: ✅ Works perfectly

**LAN (2 máy khác nhau):**
- RTT: ~20ms
- Loss: 0.1%
- Result: ✅ Works well

**Throttled (Chrome DevTools - Slow 3G):**
- RTT: ~400ms
- Loss: 5%
- Result: ⚠️  Quality degraded but functional

---

## 📖 API Documentation

### Function: `example_function()`

**Signature:**
```python
async def example_function(self, param1: str, param2: int) -> dict:
```

**Parameters:**
- `param1` (str): Mô tả parameter
- `param2` (int): Mô tả parameter

**Returns:**
- `dict`: Mô tả return value

**Example:**
```python
result = await handler.example_function("test", 123)
```

**Network behavior:**
[Giải thích function này làm gì với network: gửi packet, receive data, etc.]

---

## 🔍 Packet Format / Protocol Specification

[Nếu bạn tạo custom protocol, vẽ diagram format]

```
Offset  Size  Field       Description
------  ----  -----       -----------
0       1     type        ...
1       4     length      ...
...
```

**Example packet (hex):**
```
01 00 00 00 0A 48 65 6C 6C 6F
^  ^--------^ ^-----------^
|      |            |
type  length    "Hello" (UTF-8)
```

---

## 🎯 Challenges & Solutions

### Challenge 1: [Tên vấn đề]
**Vấn đề:** [Mô tả vấn đề gặp phải]  
**Giải pháp:** [Đã giải quyết như thế nào]  
**Lesson learned:** [Bài học rút ra]

---

## 📚 References

- [Link 1] - Mô tả
- [Link 2] - Mô tả
- [RFC xxx] - Protocol specification

---

## 🎬 Demo

**Screenshot:**
[Paste screenshot nếu có]

**Video:**
[Link video demo nếu có]

**How to reproduce:**
```bash
# Step by step commands
```

---

## 📝 Code Statistics

```bash
# Lines of code added/modified
git diff main --stat
```

**Files changed:**
- `file1.py`: +150 lines
- `file2.js`: +80 lines
- Total: +230 lines

---

## ✅ Checklist

- [ ] Code works as expected
- [ ] All tests pass
- [ ] Documentation complete
- [ ] Code reviewed by teammate
- [ ] No linter errors
- [ ] Network programming clearly demonstrated
- [ ] Performance meets requirements

---

## 🤝 Integration với modules khác

**Với module A:**  
[Giải thích cách module của bạn kết nối với module A]

**Với module B:**  
[Giải thích cách module của bạn kết nối với module B]

---

## 💡 Future Improvements

1. [Tính năng có thể thêm trong tương lai]
2. [Optimization có thể làm]
3. [Bug còn tồn đọng (nếu có)]

---

**Tổng kết:**  
[Paragraph ngắn gọn tổng kết công việc đã làm và đóng góp vào dự án]

