# ###########################################
# Name: Shayene Johnson
# Assignment: Final Project
# Purpose: Fetch module for the web crawler
#          Provides HTTP GET
#          with retry and filtering
# ###########################################

import logging
import requests

from typing import Optional, Tuple

HTML_MIME_PREFIXES = ("text/html", "application/xhtml+xml")

DEFAULT_RETRIES_COUNT = 1
DEFAULT_TIMEOUT_SECONDS = 5

STATUS_MIN_SUCCESS = 200
STATUS_MAX_SUCCESS = 299
STATUS_MIN_SERVER_ERROR = 500
STATUS_MAX_SERVER_ERROR = 599
STATUS_NONE = 0

def _is_html(content_type: Optional[str]) -> bool:
    """
    This function checks whether the provided Content-Type header value
    indicates that the HTTP response is HTML content.

    :param Optional[str] content_type:
    :return bool : is_html
    :exception na : na
    :note na
    """
    is_html = False
    if content_type:
        content_type_lower = content_type.lower()
        main_type = content_type_lower.split(";")[0].strip()
        is_html = any(
            main_type.startswith(prefix) for prefix in HTML_MIME_PREFIXES
        )
    return is_html

def http_get(
        url: str,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
        retries: int = DEFAULT_RETRIES_COUNT,
        user_agent: str = "MiniCrawler/0.1", ) -> Tuple[int, str, Optional[str]]:
    """
    This function performs an HTTP GET request
    for the given URL, following redirects
    and returning only HTML content in the 2xx range.
    It also retries on timeouts and 5xx responses
    up to the specified number of retries.

    :param str url: The URL to fetch.
    :param int timeout: Timeout in seconds.
    :param int retries: Number of retries.
    :param str user_agent: User-Agent header value.
    :return Tuple[int, str, Optional[str]] : status, final_url, html
    :exception na : na
    :note na
    """
    attempt = 0
    status = STATUS_NONE
    final_url = url
    html = None
    max_attempts = retries + 1
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    }

    should_continue = True

    while attempt < max_attempts and should_continue:
        attempt += 1
        try:
            resp = requests.get(url, timeout=timeout, headers=headers)
            status = resp.status_code
            final_url = str(resp.url)
            content_type_header = resp.headers.get("Content-Type")
            is_html_response = _is_html(content_type_header)
            is_success = (
                    STATUS_MIN_SUCCESS
                    <= status
                    <= STATUS_MAX_SUCCESS
            )
            is_server_error = (
                    STATUS_MIN_SERVER_ERROR
                    <= status
                    <= STATUS_MAX_SERVER_ERROR
            )

            if is_success and is_html_response:
                html = resp.text
                should_continue = False
            elif is_server_error and attempt < max_attempts:
                logging.debug(
                    "5xx (%d) for %s; retrying (%d/%d)",
                    status,
                    url,
                    attempt,
                    max_attempts,
                )
            else:
                should_continue = False

        except (requests.Timeout, requests.ConnectionError) as exc:
            if attempt < max_attempts:
                logging.debug(
                    "Network error for %s; retrying (%d/%d)",
                    url,
                    attempt,
                    max_attempts,
                )
            else:
                logging.warning(
                    "Network failure for %s after retries: %s",
                    url,
                    repr(exc),
                )

    return status, final_url, html
