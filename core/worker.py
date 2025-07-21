"""
This module defines the core worker routine used for concurrent email checking in a multi-threaded environment. 
Each worker is responsible for managing its own session, proxy, and CSRF token lifecycle, processing a configured 
number of emails per session before rotating to a new one. 

Purpose:
    Efficiently verify emails in parallel while handling rate limits, session failures, and transient network issues.

Key Features:
    • Session Rotation:
      Each worker attempts to initialize a fresh session (with headers and proxy) and fetch a CSRF token from GitHub.
      If session initialization fails multiple times, the worker exits gracefully.

    • Email Processing:
      Emails are fetched from a shared queue and processed using the `check_email` function. Results are stored 
      in a shared dictionary with thread-safe locking.

    • Fault Tolerance:
      On failure (e.g., timeouts, invalid tokens, request errors), the worker re-queues the email and rotates session 
      to reduce the chance of bans or blocks.

    • Logging:
      Granular logging allows for real-time monitoring and post-analysis of worker performance and errors.
"""

import logging
import queue
import threading
from core import generate_session_and_proxy, generate_headers, get_csrf_token, check_email

logger = logging.getLogger(__name__)

def worker(
    q: queue.Queue,
    worker_id: int,
    emails_per_session: int,
    results: dict[str, str],
    results_lock: threading.Lock,
) -> None:
    """
    Executes the core email verification logic for a single worker thread.

    Args:
        q (queue.Queue): Shared queue of emails to process.
        worker_id (int): Identifier for the worker thread.
        emails_per_session (int): Number of emails to process before rotating the session.
        results (dict): Thread-safe dictionary to store email → status mapping.
        results_lock (threading.Lock): Lock used to protect shared result dict access.
    """
    max_attempts = 10
    processed_total = 0

    while True:
        # Attempt to establish a valid session with CSRF token
        for attempt in range(1, max_attempts + 1):
            try:
                session, proxies, session_id = generate_session_and_proxy()
                headers_get, headers_post = generate_headers()
                token = get_csrf_token(session, proxies, headers_get)
                if token:
                    break
            except Exception as e:
                logger.info(f"[Worker {worker_id}] Session init failed (attempt {attempt}): {e}")
        else:
            logger.info(f"[Worker {worker_id}] Failed to initialize session after {max_attempts} attempts")
            return

        logger.debug(f"[Worker {worker_id}] Using new session: {session_id}")
        processed_in_session = 0

        while processed_in_session < emails_per_session:
            try:
                email = q.get(timeout=5)
            except queue.Empty:
                logger.info(f"[{session_id}] Queue empty — worker exiting")
                return

            try:
                result = check_email(email, session, token, proxies, headers_post, timeout=20)
                if result is None:
                    logger.info(f"[{session_id}] Failed to check email {email} → rotating session")
                    q.put(email)  # Retry with new session
                    break

                _, status = result
                logger.info(f"[{session_id}] {email} → {status}")
                with results_lock:
                    results[email] = status

            except Exception as e:
                logger.error(f"[{session_id}] Unexpected error with {email}: {e}")
                q.put(email)  # Retry later
                break  # rotate session

            finally:
                q.task_done()
                processed_total += 1
                processed_in_session += 1
                logger.debug(f"[{session_id}] Processed {processed_in_session}/{emails_per_session} this session")

        logger.debug(f"[Worker {worker_id}] Rotating session after {processed_in_session} emails")
