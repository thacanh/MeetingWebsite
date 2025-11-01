import requests
import time

def test_http_server():
    base = "http://localhost:8080"
    
    # Test 1: GET index
    r = requests.get(f"{base}/")
    assert r.status_code == 200
    print("✓ GET / works")
    
    # Test 2: Cache headers
    r = requests.get(f"{base}/js/app.js")
    print(f"Cache-Control: {r.headers.get('Cache-Control')}")
    print(f"ETag: {r.headers.get('ETag')}")
    
    # Test 3: Concurrent requests
    import concurrent.futures
    def fetch():
        return requests.get(f"{base}/").status_code
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch) for _ in range(100)]
        results = [f.result() for f in futures]
    
    print(f"✓ {len([r for r in results if r == 200])}/100 requests OK")
    
    # Test 4: Stats endpoint (nếu implement)
    r = requests.get(f"{base}/stats")
    if r.status_code == 200:
        print(f"Stats: {r.json()}")

test_http_server()