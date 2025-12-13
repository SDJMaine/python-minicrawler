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

    if not netloc.endswith("instagram.com"):
        return False

    if not path:
        return False

    first_segment = path.split("/", 1)[0]
    is_post = first_segment == "p"
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

    # Validate that this looks like an Instagram post URL
    if not _is_instagram_post_url(url):
        result["error"] = "URL is not a recognized Instagram post URL (/p/<id>/)."
        return result

    # Try to fetch the page
    try:
        response = requests.get(url, timeout=timeout)
    except Exception as exc:
        result["error"] = f"Unable to fetch URL: {exc}"
        return result

    status = response.status_code
    result["status"] = status

    # Non-200 often means private / removed / login-only
    if status != 200:
        result["error"] = (
            "Page not accessible (it may be private, removed, or require login)."
        )
        return result

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
        result["error"] = (
            "No public image found in the HTML. "
            "The post may be private or loaded only via JavaScript."
        )
        return result

    result["image_url"] = primary_image
    return result