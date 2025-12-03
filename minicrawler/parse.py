# ###########################################
# Name: Shayene Johnson
# Assignment: 8
# Purpose: Parse module for the web crawler
#          Parses HTML pages
#          to extract links and titles
# ###########################################

from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse, urlunparse
from bs4 import BeautifulSoup

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

    :param url: str
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


def parse_page(html: str, base_url: str) -> Dict[str, object]:
    """
    This function parses a single HTML page
    and returns the page title and
    a list of internal links (same host as the base_url),
    normalized and deduplicated.

    :param str html:
    :param str base_url:
    :return Dict[str, object] : parsed_page_info
    :exception na : na
    :note na
    """
    soup = BeautifulSoup(html, "html.parser")
    title = _extract_title(soup)

    seed_netloc = urlparse(base_url).netloc
    seen: Set[str] = set()
    internal: List[str] = []

    anchors = soup.find_all("a", href=True)
    for anchor in anchors:
        raw = anchor.get("href")
        abs_url = urljoin(base_url, raw)
        normalized_url = _normalize_url(abs_url)
        if _same_host(normalized_url, seed_netloc):
            if normalized_url not in seen:
                seen.add(normalized_url)
                internal.append(normalized_url)

    parsed_page_info = {"title": title, "internal_links": internal}
    return parsed_page_info
