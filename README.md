# Web-Scraping-Tool-PoC
This tool is a web scraping proof-of-concept (PoC) designed for reconnaissance and automation purposes. Its primary objective is to check large volumes of user email addresses and determine their registration status on a given platform — in this case, GitHub — using only publicly accessible information.


##  Assumptions & Goals

- The goal is to verify the **existence of user accounts on GitHub**, based solely on email addresses.
- The script assumes **no API access**, and relies on **GitHub's public web registration interface**.
- Target use case: quickly verify large sets of emails (e.g., 5,000+) for reconnaissance/research.
- Network identity is masked through **proxy rotation**, simulating organic behavior.

- ---

##  Challenges Solved

###  1. **Rate Limiting & Blocking**
- Solved by generating a new session and proxy for every N emails per thread.
- Uses rotating proxies from **Decodo**, with each session expected to return a **unique IP address**.

###  2. **Captcha Handling**
- GitHub may show a CAPTCHA challenge after several requests from the same IP.
- The script detects CAPTCHA presence by analyzing response content.
- When a CAPTCHA is detected, the session is **dropped**, and the proxy is rotated automatically.

###  3. **Timeouts & Network Errors**
- Each request has a configurable timeout.
- Failed emails are typically re-queued for retry when appropriate, ensuring thorough processing.

###  4. **Concurrency**
- Uses ThreadPoolExecutor to process many emails concurrently (default: 10 threads; configurable via CLI).
- Each worker processes a configurable batch of emails (emails_per_session) using the same session, proxy, and CSRF token. After processing the batch, the worker rotates to a fresh session and proxy to avoid rate limiting or blocking.
Note: If a session is reused more than ~130 times, the IP tends to hit rate limits, captchas, or gets blocked, so this parameter is adjustable via CLI to optimize throughput and avoid detection.

---

## How It Works

1. Loads email addresses from a file (one per line).
2. Launches multiple threads using a shared queue.
3. Each worker thread:
   - Pulls a small batch of emails.
   - Generates a new session + proxy (via `generate_session_and_proxy()`).
   - Generates header section with random User-Agents
   - Makes GET request to extract cookies and token
   - Makes a POST request to GitHub’s registration endpoint.
   - Checks for clues in the HTML response to determine registration status.
   - Logs and stores the result.

---
## Usage Instructions

1. Clone or download this project.
   
3. Install dependencies. Most are standard Python packages, except for Beautiful Soup, which you can install with:
```bash
pip install beautifulsoup4
```

3. Add your proxy provider (sticky or rotating proxies) to proxy_session_manager.py. For this project I use DECODO residential proxies.

<pre>
  # Credentials for authenticated proxy access via Decodo
        username = 'user-username-sessionduration-1'
        password = 'password'
</pre>

5. Generate random emails, and maybe add some real ones to the generated emails .txt file.

```bash
python3 generateEmails.py
```

5. Run the proxy module test to check your proxy rotates. (Returns new IP for every request).

```bash
python3 tests/test_session_manager.py
```
   
6. Run the script using the default number of workers (10) threads and (3) emails processed per one proxy session (One GET and 3xPOST).
**(NOT RECOMMENDED — TOO SLOW)**

```bash
python3 run.py 5k_random_emails.txt
```

To scale up and process emails faster, increase the number of worker threads (-w) and the number of emails processed per session (-n):

1. **-w 40** — sets 40 concurrent worker threads.
2. **-n 20** — makes each worker process 20 emails before rotating its session and proxy.

```bash
python3 run.py 5k_random_emails.txt -w 40 -n 20
```

To capture the console output and logs into a separate file for easier inspection, you can redirect both stdout and stderr:

1. **-o results.json tells the script to save the results in a JSON file called results.json.
2. **-2>&1 | tee console.log redirects both standard output and error streams to the terminal and writes them into console.log simultaneously.

**(RECOMMENDED)**
```bash
python3 run.py 5k_random_emails.txt -w 40 -n 20 -o results.json 2>&1 | tee console.log
```
___

## Estimated Runtime

- **Estimated for 5,000 emails**: 82.29 seconds  (-w 40 -n 20)
  (Varies depending on GitHub rate limits, proxy speed, number of threads)

### Optimizations:
- Adjust `emails_per_worker` (emails per session) and `max_workers` to tune performance.
- Use high-quality residential proxies for best speed.
___


Project Modules Overview

1. CLI Argument Parsing and Logging Setup (cli/main.py)

Handles command-line argument parsing and logging configuration.
	•	Parses required and optional parameters such as:
	•	Input file path with emails to check
	•	Number of worker threads
	•	Emails processed per worker before rotating sessions
	•	Logging verbosity level
	•	Optional JSON output file for results
	•	Sets up structured logging with timestamps, thread names, and log levels.


2. Email Producer (core/email_loader.py)

Reads email addresses line-by-line from the provided input file and enqueues them into a thread-safe queue for processing by worker threads.


3. HTTP Headers Generator (core/get_headers.py)

Generates realistic, rotating HTTP request headers to mimic genuine browser behavior.
	•	Maintains a list of user-agent strings from various browsers and platforms
	•	Provides separate header sets optimized for GET and POST requests to reduce detection during web scraping and automation.


4. Proxy Session Generator (core/proxy_session_manager.py)

Establishes a fresh requests.Session configured with a rotating Decodo proxy.
	•	Supports sticky IP sessions with a unique session ID and randomized port on each call
	•	Enables IP rotation to avoid rate limits, distribute load, and boost scraping reliability
	•	Returns a session, proxy config, and session ID
	•	Automatically logs and raises errors if proxy generation fails

Used to maintain anonymity and ensure each worker uses a distinct IP identity when checking emails.


5. CSRF Token Extractor (core/csrf_token.py)

Fetches and parses the CSRF authenticity token from GitHub’s signup page using a retry-capable session.
	•	Uses requests + BeautifulSoup to retrieve and extract the CSRF token from HTML
	•	Supports rotating proxies and custom headers
	•	Implements robust error handling (timeouts, proxy/SSL issues, rate limiting)
	•	Retries on transient errors (429, 5xx) with configurable backoff
	•	Logs meaningful status messages and suppresses noisy retry warnings

Used to enable session-based POST requests to GitHub signup endpoints.


6. Email Registration Checker (core/email_checker.py)

Sends a simulated form submission to GitHub’s internal validation endpoint to check whether an email is already registered.
	•	Uses a persistent session with retry support (429, 5xx, etc.)
	•	Supports proxies, headers, CSRF tokens, and custom timeouts
	•	Detects likely CAPTCHA challenges via HTTP 301/302 redirects
	•	Analyzes response content to classify the email as:
	•	"Registered"
	•	"Not registered"
	•	"Unclear" (fallback when HTML isn’t conclusive)

Returns None for blocked, rate-limited, redirected, or errored requests (retrying email with new proxy).


7. Concurrent Email Verification Worker (core/worker.py)

This module implements the core routine for multi-threaded email verification against GitHub.

Each worker thread:
	•	Manages its own HTTP session, proxy, headers, and CSRF token.
	•	Processes a fixed number of emails before rotating the session to avoid bans or rate limits.
	•	Stores results in a shared dictionary, protected by a thread-safe lock.
	•	Gracefully handles timeouts, invalid sessions, and transient network errors.

  Key Features
	•	Session Rotation:
   Workers initialize fresh sessions and rotate them periodically or after errors. If session setup fails repeatedly, the worker exits cleanly.
	•	Parallel Email Processing:
   Emails are fetched from a shared queue and verified concurrently using the check_email() function.
	•	Resilience and Fault Tolerance:
   Failed email checks are re-queued to be retried by the same or another worker with a new session.
	•	Thread-Safe Results Collection:
   All results are safely stored in a shared dictionary using a threading lock.


8. Email Verification Orchestrator (run.py)

This is the central entry point of the email verification tool. It coordinates the entire workflow from CLI parsing to multithreaded email checking and optional result export.

 Responsibilities
	•	Parse command-line arguments using the cli module.
	•	Spawn a producer thread to read email addresses from a file into a shared queue.
	•	Launch a pool of worker threads to verify emails concurrently using independent sessions and proxies.
	•	Manage thread lifecycles, synchronize the queue, and handle graceful shutdown.
	•	Optionally export the final results to a JSON file.

 Workflow Overview
	1.	Parse CLI Arguments:
Accepts options like input file, number of workers, verbosity, and output path.
	2.	Email Producer:
A separate thread feeds email addresses from the input file into a bounded queue.
	3.	Worker Pool Execution:
Each worker processes a batch of emails with its own session, proxy, and CSRF token, saving results in a thread-safe dictionary.
	4.	Queue & Worker Coordination:
Waits for the queue to fully drain (queue.join()), then ensures all threads have completed (as_completed()).
	5.	Reporting & Export:
Prints runtime stats and optionally saves results to disk in JSON format.

 Module Dependencies
	•	cli.main.parse_args and setup_logging — for user configuration and logging.
	•	core.email_producer — for feeding emails into the queue.
	•	core.worker — for concurrent email verification logic.

 Output
	•	Standard output: Total emails processed and runtime stats.
	•	Optional: JSON file containing a dictionary of {email: status} pairs.

---

### 📦 Requirements

- Python 3.8+
- `requests`, `concurrent.futures`, `logging`, `argparse`
