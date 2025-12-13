# ###########################################
# Name: Shayene Johnson
# Assignment: 8
# Purpose: Parse module for the web crawler
#          Parses HTML pages
#          to extract links and titles
# ###########################################

import re

from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse, urlunparse
from bs4 import BeautifulSoup

EMAIL_PATTERN = r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"
EMAIL_REGEX = re.compile(EMAIL_PATTERN)

def _normalize_url(url: str) -> str:
    """
    This function normalizes a URL
    by dropping fragments, lowercasing the scheme
    and netloc, stripping default ports,
    and removing trailing slashes when
    appropriate.

    :param str url:
    :return str : normalized_url
    :exception na : na
    :note na
    """
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()

    is_http_default_port = scheme == "http" and netloc.endswith(":80")
    is_https_default_port = scheme == "https" and netloc.endswith(":443")
    if is_http_default_port or is_https_default_port:
        netloc = netloc.rsplit(":", 1)[0]

    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path[:-1]

    return urlunparse((scheme, netloc, path, "", parsed.query, ""))


def _same_host(url: str, seed_netloc: str) -> bool:
    """
    This function checks whether
    a given URL has the same host
    (netloc) as the provided seed host.

    :param str url :
    :param str seed_netloc :
    :return bool : is_same_host
    :exception na : na
    :note na
    """
    url_netloc = urlparse(url).netloc.lower()
    seed_netloc_lower = seed_netloc.lower()
    is_same_host = url_netloc == seed_netloc_lower
    return is_same_host


def _extract_title(soup: BeautifulSoup) -> Optional[str]:
    """
    This function extracts and returns
     the page title from a BeautifulSoup
    HTML document, or None
    if no usable title is found.

    :param BeautifulSoup soup:
    :return Optional[str] : title
    :exception na : na
    :note na
    """
    title = None
    if soup.title and soup.title.string:
        raw_title = soup.title.string.strip()
        if raw_title:
            title = raw_title
    return title

def _extract_emails(soup: BeautifulSoup) -> List[str]:
    """
    This function extracts and returns
    a list of unique email addresses
    found in the HTML document.

    :param BeautifulSoup soup:
    :return List[str] : emails
    :exception na : na
    :note na
    """
    emails_set: Set[str] = set()

    anchors = soup.find_all("a", href=True)

    for anchor in anchors:
        href_value = anchor.get("href")

        if href_value and href_value.startswith("mailto:"):
            email_part = href_value[len("mailto:"):]
            email_clean = email_part.split("?", 1)[0].strip()

            if email_clean:
                emails_set.add(email_clean)

    text = soup.get_text(" ", strip=True)
    for match in EMAIL_REGEX.findall(text):
        emails_set.add(match)

    emails = list(emails_set)
    return emails

def parse_page(html: str, base_url: str, seed_netloc: str) -> Dict[str, object]:
    """
    This function parses a single HTML page
    and returns the page title and
    lists of internal links, external links,
    and email addresses.

    :param str html:
    :param str base_url:
    :param str seed_netloc:
    :return Dict[str, object] : parsed_page_info
    :exception na : na
    :note na
    """
    soup = BeautifulSoup(html, "html.parser")
    title = _extract_title(soup)

    seen_internal: Set[str] = set()
    seen_external: Set[str] = set()
    internal: List[str] = []
    external: List[str] = []

    anchors = soup.find_all("a", href=True)
    anchor_index = 0
    anchor_count = len(anchors)

    while anchor_index < anchor_count:
        anchor = anchors[anchor_index]
        raw = anchor.get("href")

        # Defensive: skip missing/empty hrefs
        if not raw:
            anchor_index = anchor_index + 1
            continue

        abs_url = urljoin(base_url, raw)
        normalized_url = _normalize_url(abs_url)
        if _same_host(normalized_url, seed_netloc):
            if normalized_url not in seen_internal:
                seen_internal.add(normalized_url)
                internal.append(normalized_url)
        else:
            if normalized_url not in seen_external:
                seen_external.add(normalized_url)
                external.append(normalized_url)
        anchor_index = anchor_index + 1

    emails = _extract_emails(soup)

    parsed_page_info = {
        "title": title,
        "internal_links": internal,
        "external_links": external,
        "emails": emails,
    }
    return parsed_page_info

