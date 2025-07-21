# core/checker.py

import logging
from requests.exceptions import Timeout, ProxyError, SSLError, RequestException
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

logger = logging.getLogger(__name__)
# Suppress urllib3 retry warnings by default
urllib3_logger = logging.getLogger("urllib3.connectionpool")
urllib3_logger.setLevel(logging.ERROR)  # Suppress retry warnings

# Retry policy for handling transient HTTP errors
RETRY_STRATEGY = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    raise_on_status=False,
    raise_on_redirect=False,
)

# Reusable HTTP adapter with retry logic
RETRY_ADAPTER = HTTPAdapter(max_retries=RETRY_STRATEGY)

def check_email(email, session, token, proxies, headers, timeout=20):
    """
    Check whether the specified email is registered on GitHub.

    This function simulates a form submission to GitHub to determine whether
    an email address is already associated with an account. It uses a session
    with retry logic and proxy support to avoid transient network issues.

    Args:
        email (str): The email address to verify.
        session (requests.Session): An HTTP session configured with headers, cookies, etc.
        token (str): CSRF authenticity token required by GitHub for form validation.
        proxies (dict): Proxy configuration for the request, e.g., {"http": "...", "https": "..."}.
        headers (dict): HTTP headers to include in the POST request.
        timeout (int): Maximum time (in seconds) to wait for a response.

    Returns:
        tuple: (email, "Registered" | "Not registered" | "Unclear")
               If the request succeeds and a result can be inferred.

        None:
            Returned in the following cases:
              - Request is rate-limited (HTTP 429)
              - Request is blocked (HTTP 403, 401)
              - Redirect likely to CAPTCHA challenge (HTTP 301, 302)
              - Network or SSL errors (e.g., Timeout, ProxyError, SSLError)
              - Any unexpected exception during the request or response parsing

    Notes:
        - CAPTCHAs are indirectly detected via redirect status codes (301/302).
        - This function disables SSL verification (verify=False); use with caution in production.
        - Retry logic is applied for transient failures (e.g., 429, 500s) using urllib3 Retry.
    """

    # Apply retry policy to the session
    session.mount("https://", RETRY_ADAPTER)
    session.mount("http://", RETRY_ADAPTER)

    try:
        payload = {
            "authenticity_token": token,
            "value": email,
        }

        response = session.post(
            "https://github.com/email_validity_checks",
            headers=headers,
            data=payload,
            proxies=proxies,
            timeout=timeout,
            verify=False  # NOTE: For production, it's safer to enable SSL verification
        )

        # Handle known blocking or error status codes
        if response.status_code == 429:
            logger.info(f"[!] Rate limited while checking {email} (429)")
            return None
        if response.status_code == 403:
            logger.info(f"[!] Access forbidden while checking {email} (403)")
            return None
        if response.status_code == 401:
            logger.info(f"[!] Unauthorized session for {email} (401)")
            return None
        if response.status_code in (301, 302):
            logger.info(f"[!] Redirected (likely CAPTCHA) while checking {email} ({response.status_code})")
            return None

        # Analyze HTML content to infer registration status
        body = response.text
        if 'already associated with an account' in body:
            return (email, "Registered")
        elif 'is available' in body or 'looks good' in body:
            return (email, "Not registered")
        else:
            return (email, "Unclear")

    except Timeout:
        logger.error(f"[!] Timeout occurred while checking {email}")
    except ProxyError as e:
        logger.error(f"[!] Proxy error while checking {email}: {e}")
    except SSLError as e:
        logger.error(f"[!] SSL error while checking {email}: {e}")
    except RequestException as e:
        logger.error(f"[!] Request exception while checking {email}: {e}")
    except Exception as e:
        root = e.__cause__ or e
        logger.exception(f"[!] Unexpected exception for {email}: {type(root).__name__}: {root}")

    return None