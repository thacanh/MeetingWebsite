# tests/test_connections.py
import socket
import time

def test_connection_timeout():
    # Test idle timeout
    sock = socket.socket()
    sock.connect(('localhost', 8080))
    
    # Send incomplete request
    sock.send(b"GET / HTTP/1.1\r\n")
    
    # Wait and see if server closes
    time.sleep(35)  # Should timeout after 30s
    
    try:
        sock.send(b"\r\n")
    except BrokenPipeError:
        print("✓ Timeout works")

test_connection_timeout()