# Web-Scraping-Tool-PoC
This tool is a web scraping proof-of-concept (PoC) designed for reconnaissance and automation purposes. Its primary objective is to check large volumes of user email addresses and determine their registration status on a given platform — in this case, GitHub — using only publicly accessible information.


## 🧠 Assumptions & Goals

- The goal is to verify the **existence of user accounts on GitHub**, based solely on email addresses.
- The script assumes **no API access**, and relies on **GitHub's public web registration interface**.
- Target use case: quickly verify large sets of emails (e.g., 5,000+) for reconnaissance or research.
- Network identity is masked through **proxy rotation**, simulating organic behavior.

- ---

## 🧩 Challenges Solved

### ✅ 1. **Rate Limiting & Blocking**
- Solved by generating a new session and proxy for every N emails per thread.
- Uses rotating proxies from **Decodo**, with each session expected to return a **unique IP address**.

### ✅ 2. **Captcha Handling**
- GitHub may show a CAPTCHA challenge after several requests from the same IP.
- The script detects CAPTCHA presence by analyzing response content.
- When a CAPTCHA is detected, the session is **dropped**, and the proxy is rotated automatically.

### ✅ 3. **Timeouts & Network Errors**
- Each request has a configurable timeout.
- Errors are logged, and the worker skips to the next email rather than halting.

### ✅ 4. **Concurrency**
- Uses `ThreadPoolExecutor` to process many emails concurrently (default: 40 threads).
- Each worker processes a small batch before rotating the session and proxy.

---

## ⚙️ How It Works

1. Loads email addresses from a file (one per line).
2. Launches multiple threads using a shared queue.
3. Each worker thread:
   - Pulls a small batch of emails.
   - Generates a new session + proxy (via `generate_session_and_proxy()`).
   - Makes a POST request to GitHub’s registration endpoint.
   - Checks for clues in the HTML response to determine registration status.
   - Logs and stores the result.

---

## 🚫 Error & Captcha Handling

| Situation              | Behavior                                                                 |
|------------------------|--------------------------------------------------------------------------|
| Invalid proxy          | Logs the error and generates a new session                               |
| Timeout                | Skips email after a warning log                                          |
| Captcha encountered    | Detects based on HTML content and triggers session/proxy rotation        |
| Unexpected response    | Logs full response and retries with a new session                        |

---

## ⏱ Estimated Runtime

- **Estimated for 5,000 emails**: ~8–15 minutes  
  (Varies depending on GitHub rate limits, proxy speed, number of threads)

### Optimizations:
- Adjust `emails_per_worker` (emails per session) and `max_workers` to tune performance.
- Use high-quality residential or datacenter proxies for best speed and least CAPTCHA detection.

---

## 📝 Usage Instructions

### 📦 Requirements

- Python 3.8+
- `requests`, `concurrent.futures`, `logging`, `argparse`

### 📁 File Structure
