import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.proxy_session_manager import generate_session_and_proxy

def test_proxy_connectivity():
    for _ in range(10):
        try:
            session, proxies, session_id = generate_session_and_proxy()
            response = session.get('https://ip.decodo.com/json', proxies=proxies, timeout=10, verify=False)
            data = response.json()

            proxy_ip = data.get("proxy", {}).get("ip", "N/A")
            country = data.get("country", {}).get("name", "Unknown")

            print(f"[{session_id}] IP: {proxy_ip} — Country: {country}")

        except Exception as e:
            print(f"[{session_id}] {e}")

if __name__ == "__main__":
    test_proxy_connectivity()