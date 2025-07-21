# core/csrf_token.py

"""
Module: csrf_token
------------------

This module handles retrieval and parsing of the CSRF authenticity token required 
for submitting forms on GitHub's signup page. It ensures robust and fault-tolerant 
HTTP communication through retries, proxy support, and graceful error handling.

Main Function:
- get_csrf_token(session, proxies, headers): 
    Makes an HTTP GET request to GitHub's signup page using a provided session,
    extracts the CSRF token from the HTML response, and returns it.

Features:
- Retry strategy for network/server issues (e.g., 429 Too Many Requests, 5xx errors).
- Handles common failure scenarios: timeouts, proxy/SSL errors, redirects, and CAPTCHAs.
- Uses BeautifulSoup to safely parse the CSRF token from the HTML.

Usage:
    from core.csrf_token import get_csrf_token
    token = get_csrf_token(session, proxies, headers)
"""

import logging
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from requests.exceptions import Timeout, ProxyError, SSLError, RequestException
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

# Configure logging level for urllib3 (suppress warnings from retries)
urllib3_logger = logging.getLogger("urllib3.connectionpool")
urllib3_logger.setLevel(logging.ERROR)

# Define retry policy for transient errors
retries = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    raise_on_status=False,
    raise_on_redirect=False,
)

# Prepare an HTTPAdapter with retry capability
adapter = HTTPAdapter(max_retries=retries)


def get_csrf_token(session, proxies, headers):
    """
    Retrieves the CSRF token from GitHub's signup page.

    Args:
        session (requests.Session): Reusable session object, optionally preconfigured with cookies/proxies.
        proxies (dict): Proxy configuration for 'http' and 'https' schemes.
        headers (dict): HTTP headers to include in the request.

    Returns:
        str | None: CSRF token if extracted successfully, None otherwise.

    Raises:
        RuntimeError: If the CSRF token is not found or if parsing fails.
    """

    # Attach the retry-enabled adapter to the session
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    try:
        logger.debug("[*] Requesting GitHub signup page to extract CSRF token...")

        response = session.get(
            'https://github.com/signup?ref_cta=Sign+up&ref_loc=header+logged+out&ref_page=%2F&source=header-home',
            headers=headers,
            proxies=proxies,
            timeout=20,
            verify=False  # Warning: disabling SSL verification is insecure
        )

        # Handle known response scenarios
        if response.status_code == 429:
            logger.info("[!] Rate limited (HTTP 429).")
            return None

        if response.status_code == 403:
            logger.info("[!] Access forbidden (HTTP 403). Possible CAPTCHA or IP block.")
            return None

        if response.status_code == 401:
            logger.info("[!] Unauthorized (HTTP 401). Session might be expired or blocked.")
            return None

        if response.status_code in (301, 302):
            logger.info("[!] Redirected (HTTP 30x). Possibly redirected to CAPTCHA or auth wall.")
            return None

        response.raise_for_status()

    except Timeout:
        logger.error("[!] Request timed out.")
        return None
    except ProxyError as e:
        logger.error(f"[!] Proxy error: {e}")
        return None
    except SSLError as e:
        logger.error(f"[!] SSL error: {e}")
        return None
    except RequestException as e:
        logger.error(f"[!] General request error: {e}")
        return None
    except Exception as e:
        root_cause = e.__cause__ or e
        logger.error(f"[!] Unexpected error ({type(e).__name__}): {root_cause}")
        logger.exception("Stack trace:")
        return None

    # Attempt to extract the CSRF token from the HTML
    try:
        soup = BeautifulSoup(response.text, 'html.parser')

        auto_check = soup.find('auto-check', {'src': '/email_validity_checks'})
        csrf_input = auto_check.find('input', {'type': 'hidden', 'data-csrf': 'true'}) if auto_check else None
        token = csrf_input['value'] if csrf_input else None

        if not token:
            logger.error("[!] CSRF token not found in the page.")
            raise RuntimeError("CSRF token not found in the signup page.")

        logger.debug(f"[+] Extracted CSRF token: {token[:10]}...")  # Show partial token for logging
        return token

    except Exception as e:
        logger.exception("[!] Error while parsing CSRF token from response HTML.")
        raise RuntimeError("Failed to parse CSRF token.") from e