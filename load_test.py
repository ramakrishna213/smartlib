import requests
import time
import threading
from collections import deque
from statistics import mean

BASE_URL = "http://127.0.0.1:5000"
NUM_USERS = 100
DURATION = 60  # seconds

results = {
    "total": 0,
    "errors": 0,
    "times": deque(maxlen=200000),
    "statuses": {}
}

lock = threading.Lock()

def worker(session, end_time):
    while time.time() < end_time:
        try:
            resp = session.get(f"{BASE_URL}/dashboard", timeout=10)
            with lock:
                results["total"] += 1
                results["times"].append(resp.elapsed.total_seconds())
                results["statuses"][resp.status_code] = results["statuses"].get(resp.status_code, 0) + 1
        except Exception as e:
            with lock:
                results["errors"] += 1

def main():
    print("Logging in to obtain session cookie...")
    session = requests.Session()
    login_page = session.get(f"{BASE_URL}/login")
    csrf_token = ""
    if "csrf_token" in login_page.text:
        import re
        m = re.search(r'name="csrf_token".*?value="([^"]+)"', login_page.text)
        if m:
            csrf_token = m.group(1)

    payload = {
        "email": "alex@example.com",
        "password": "member123",
        "remember": "on"
    }
    if csrf_token:
        payload["csrf_token"] = csrf_token

    resp = session.post(f"{BASE_URL}/login", data=payload, allow_redirects=False)
    if resp.status_code not in (301, 302, 303, 307):
        print(f"Login failed with status {resp.status_code}")
        print(resp.text[:500])
        return

    print("Login successful. Starting load test...")
    print(f"Target: {NUM_USERS} virtual users for {DURATION} seconds against {BASE_URL}/dashboard")

    end_time = time.time() + DURATION
    threads = []
    for _ in range(NUM_USERS):
        s = requests.Session()
        s.cookies.update(session.cookies)
        t = threading.Thread(target=worker, args=(s, end_time))
        t.start()
        threads.append(t)

    start = time.time()
    for t in threads:
        t.join()

    elapsed = time.time() - start
    total = results["total"]
    rps = total / elapsed if elapsed > 0 else 0
    times = list(results["times"])

    print("\n=== Baseline Load Test Results ===")
    print(f"Test duration:   {elapsed:.1f}s")
    print(f"Total requests:  {total}")
    print(f"Requests/sec:    {rps:.1f} req/sec")
    print(f"Errors:          {results['errors']}")
    if times:
        print(f"Avg response:    {mean(times) * 1000:.0f}ms")
        print(f"Min response:    {min(times) * 1000:.0f}ms")
        print(f"Max response:    {max(times) * 1000:.0f}ms")
    print(f"Status codes:    {results['statuses']}")
    print("=" * 40)

if __name__ == "__main__":
    main()
