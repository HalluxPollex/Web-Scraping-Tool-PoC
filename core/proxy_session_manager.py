"""
    Generates a new `requests.Session` configured with a rotating proxy.

    I use "Decodo" proxy provider, which supports session-based sticky IP rotation. 
    Each time this function is called, it generates a unique session ID and a randomized 
    port to initiate a new proxy session. This setup ensures that a **different IP address** 
    is used for each request batch, which helps to:
    
    - Evade IP-based rate limits and bans
    - Distribute traffic across a wide IP pool
    - Increase anonymity and scraping reliability

    Returns:
        tuple: 
            - session (requests.Session): HTTP session with reused connection pool
            - proxies (dict): Proxy configuration for HTTP/HTTPS
            - session_id (str): Unique identifier used in proxy username

    Raises:
        RuntimeError: If proxy generation or session configuration fails.
    """


import requests
import random
import logging

logger = logging.getLogger(__name__)

# disable SSL warnings (not recommended for production)
requests.packages.urllib3.disable_warnings()

def generate_session_and_proxy():
    
    try:
        session = requests.Session()
        session_id = ''.join(random.choices('abcdef0123456789', k=8))

        # Randomize the port (Decodo supports multiple ports for distribution)
        port = random.randint(10001, 49999)

        # Credentials for authenticated proxy access via Decodo
        username = 'user-spyasdasdasd-sessionduration-1'
        password = 'asdasdasdasdz~'

        # Assemble proxy URL with unique session
        proxy_url = f"http://{username}-session-{session_id}:{password}@gate.decodo.com:{port}"
        
        proxies = {
            "http": proxy_url,
            "https": proxy_url,
        }

        logger.debug(f"Generated session with ID: {session_id}")
        logger.debug(f"Proxy set to: {proxy_url}")

        return session, proxies, session_id

    except Exception as e:
        logger.exception("Failed to generate session and proxy.")
        raise RuntimeError("Proxy session generation failed.") from e