# ###########################################
# Name: Shayene Johnson
# Assignment: Final Project
# Purpose: Instagram helper module
#          Extracts primary image from
#          a public Instagram post URL
# ###########################################

from typing import Dict

from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from minicrawler.parse import _extract_title, extract_description_content, parse_instagram_post


def _is_instagram_post_url(url: str) -> bool:
    """
    This function checks whether a URL
    appears to be an Instagram post URL
    of the form /p/<id>/.

    :param str url:
    :return bool : is_post
    :exception na : na
    :note na
    """
    parsed = urlparse(url)
    netloc = parsed.netloc.lower()
    path = parsed.path.strip("/")

    first_segment = ""

    if path:
        first_segment = path.split("/", 1)[0]

    is_post = netloc.endswith("instagram.com") and path != "" and first_segment == "p"

    return is_post

def fetch_instagram_post_image(url: str, timeout: float = 10.0) -> Dict[str, object]:
    """
    This function fetches an
    Instagram post URL
    and tries to extract a
    primary image URL.

    On success:
      {
        "kind": "instagram_post",
        "url": "<url>",
        "status": 200,
        "title": "...",
        "description": "...",
        "image_url": "https://..."
      }

    On failure (non-post URL,
    private/deleted, no image, etc.),
    it returns a dictionary with
    an "error" message.

    :param str url:
    :param float timeout:
    :return Dict[str, object] : info
    :exception na : na
    :note na
    """
    result: Dict[str, object] = {
        "kind": "instagram_post",
        "url": url,
    }

    error_message: str = ""

    is_post_url = _is_instagram_post_url(url)
    if not is_post_url:
        error_message = "URL is not a recognized Instagram post URL (/p/<id>/)."
    else:
        response = None
        fetch_failed = False

        try:
            response = requests.get(url, timeout=timeout)
        except Exception as exc:
            fetch_failed = True
            error_message = f"Unable to fetch URL: {exc}"

        if not fetch_failed and response is not None:
            status = response.status_code
            result["status"] = status

            if status != 200:
                error_message = (
                    "Page not accessible (it may be private, removed, or require login)."
                )
            else:
                html = response.text
                soup = BeautifulSoup(html, "html.parser")

                title = _extract_title(soup)
                if title is not None:
                    result["title"] = title

                description = extract_description_content(html)
                if description is not None:
                    result["description"] = description

                primary_image = parse_instagram_post(soup, url)
                if primary_image is None:
                    error_message = (
                        "No public image found in the HTML. "
                        "The post may be private or loaded only via JavaScript."
                    )
                else:
                    result["image_url"] = primary_image

    if error_message:
        result["error"] = error_message

    return result