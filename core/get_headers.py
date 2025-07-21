# email_checker/core/headers.py

"""
This module is responsible for dynamically generating realistic HTTP request headers to simulate genuine browser behavior 
when interacting with web services, such as GitHub’s signup page. It plays a critical role in reducing the likelihood of 
detection or blocking when performing automated HTTP requests as part of email verification or scraping tasks.

Key Features:
    • User-Agent Rotation:
      A predefined list of modern, diverse user-agent strings is maintained to randomly select from, mimicking traffic 
      from various browsers and operating systems (e.g., macOS, Windows, Linux).

    • Header Generation:
      Two separate header sets are generated:
        • headers_get: Optimized for initial GET requests (e.g., loading the signup page).
        • headers_post: Designed for follow-up POST requests (e.g., submitting email checks).

These headers help to replicate the behavior of legitimate browser requests, improving stealth and compatibility 
when interacting with anti-bot-protected endpoints.
"""

import random

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.113 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
    # Add more realistic agents
]

def generate_headers():
    user_agent = random.choice(USER_AGENTS)

    headers_get = {
        "Host": "github.com",
        "Connection": "keep-alive",
        "User-Agent": user_agent,
        "Accept": "*/*",
        "Referer": "https://github.com/",  # optional spoof
        "sec-ch-ua": '"Not.A/Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        "sec-ch-ua-platform": '"macOS"',
        "sec-ch-ua-mobile": "?0",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Dest": "document",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9",
    }

    headers_post = {
        "Host": "github.com",
        "Connection": "keep-alive",
        "sec-ch-ua-platform": '"macOS"',
        "User-Agent": user_agent,
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "*/*",
        "Origin": "https://github.com",
        "Referer": "https://github.com/signup",
        "sec-ch-ua": '"Not.A/Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        "sec-ch-ua-platform": '"macOS"',
        "sec-ch-ua-mobile": "?0",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9",
    }

    return headers_get, headers_post