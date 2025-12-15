# ###########################################
# Name: Shayene Johnson
# Assignment: Final Project
# Purpose: Parse module for the web crawler
#          Parses HTML pages to extract
#          links, emails, images, and titles
# ###########################################

import re

from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse, urlunparse
from bs4 import BeautifulSoup

DEFAULT_HTTP_PORT = 80
DEFAULT_HTTPS_PORT = 443
SPLIT_ONCE = 1
LAST_INDEX = -1

EMAIL_PATTERN = r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"
EMAIL_REGEX = re.compile(EMAIL_PATTERN)


def parse_page(html: str, base_url: str, seed_netloc: str) -> Dict[str, object]:
    """
    This function parses a
    single HTML page
    and returns the page title
    and lists of internal links,
    external links,
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
    internal_links, external_links = _extract_links(soup, base_url, seed_netloc)
    emails = _extract_emails(soup)
    images = _extract_images(soup, base_url)

    parsed_page_info = {
        "title": title,
        "internal_links": internal_links,
        "external_links": external_links,
        "emails": emails,
        "images": images,
    }
    return parsed_page_info

def parse_instagram_post(html: str, url: str, status: int) -> Dict[str, object]:
    """
    This function parses an
    Instagram post page
    and returns basic information
    including: title, description,
    primary image URL, and
    the poster's username
    when available.

    :param str html:
    :param str url:
    :param int status:
    :return Dict[str, object] : instagram_post_info
    :exception na : na
    :note na
    """
    soup = BeautifulSoup(html, "html.parser")

    title = _extract_title(soup)
    description = _extract_meta_property_content(soup, "og:description")
    image_url = _extract_meta_property_content(soup, "og:image")
    og_title_content = _extract_meta_property_content(soup, "og:title")

    username = _extract_instagram_username(description, og_title_content)

    if title is None:
        title = "Instagram"

    instagram_post_info: Dict[str, object] = {
        "kind": "instagram_post",
        "url": url,
        "status": status,
        "title": title,
        "description": description,
        "image_url": image_url,
        "username": username,
    }
    return instagram_post_info

def _normalize_url(url: str) -> str:
    """
    This function normalizes a URL
    by dropping fragments,
    lowercasing the scheme
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
    netloc = _strip_default_port(scheme, netloc)

    path = _normalize_path(parsed.path)

    normalized_url = urlunparse((scheme, netloc, path, "", parsed.query, ""))
    return normalized_url


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
    _collect_mailto_emails(anchors, emails_set)

    text = soup.get_text(" ", strip=True)
    _collect_text_emails(text, emails_set)

    emails = list(emails_set)
    return emails


def _extract_images(soup: BeautifulSoup, base_url: str) -> List[str]:
    """
    This function extracts and returns
    a list of unique normalized image URLs
    from img tags in the HTML document.

    :param BeautifulSoup soup:
    :param str base_url:
    :return List[str] : image_urls
    :exception na : na
    :note na
    """
    images_set: Set[str] = set()
    img_tags = soup.find_all("img", src=True)

    for img_tag in img_tags:
        src_value = img_tag.get("src")
        if src_value:
            abs_url = urljoin(base_url, src_value)
            normalized_url = _normalize_url(abs_url)
            images_set.add(normalized_url)

    images = list(images_set)
    return images


def extract_description_content(html: str) -> Optional[str]:
    """
    This function extracts a
    special description text
    from the HTML document,
    using the meta description
    tag or the first paragraph
    element.

    :param str html:
    :return Optional[str] : description_text
    :exception na : na
    :note na
    """
    soup = BeautifulSoup(html, "html.parser")

    description_text = _extract_meta_description(soup)
    if description_text is None:
        description_text = _extract_first_paragraph(soup)

    return description_text

# ********************************************
#            Helper functions
# ********************************************

def _strip_default_port(scheme: str, netloc: str) -> str:
    """
    This function strips default
    ports from a netloc
    for http (80) and https (443).

    :param str scheme:
    :param str netloc:
    :return str : cleaned_netloc
    :exception na : na
    :note na
    """
    cleaned_netloc = netloc

    is_http_default = scheme == "http" and netloc.endswith(f":{DEFAULT_HTTP_PORT}")
    is_https_default = scheme == "https" and netloc.endswith(f":{DEFAULT_HTTPS_PORT}")

    if is_http_default or is_https_default:
        cleaned_netloc = netloc.rsplit(":", SPLIT_ONCE)[0]

    return cleaned_netloc


def _normalize_path(path: str) -> str:
    """
    This function normalizes a
    URL path by ensuring
    a root slash exists, and
    trimming a trailing slash
    when the path is not root.

    :param str path:
    :return str : normalized_path
    :exception na : na
    :note na
    """
    normalized_path = path or "/"

    is_root = normalized_path == "/"
    ends_with_slash = normalized_path.endswith("/")

    if not is_root and ends_with_slash:
        normalized_path = normalized_path[:LAST_INDEX]

    return normalized_path


def _collect_mailto_emails(anchors, emails_set: Set[str]) -> None:
    """
    This function collects mailto:
    emails from anchor tags.

    :param object anchors:
    :param Set[str] emails_set:
    :return None : na
    :exception na : na
    :note na
    """
    for anchor in anchors:
        href_value = anchor.get("href")
        if href_value is not None:
            href_lower = href_value.lower()
            if href_lower.startswith("mailto:"):
                email_part = href_value[len("mailto:"):]
                email_clean = email_part.split("?", SPLIT_ONCE)[0].strip()
                if email_clean:
                    emails_set.add(email_clean)


def _collect_text_emails(text: str, emails_set: Set[str]) -> None:
    """
    This function collects
    email addresses from text
    using the configured
    EMAIL_REGEX.

    :param str text:
    :param Set[str] emails_set:
    :return None : na
    :exception na : na
    :note na
    """
    matches = EMAIL_REGEX.findall(text)

    for match in matches:
        emails_set.add(match)


def _extract_meta_description(soup: BeautifulSoup) -> Optional[str]:
    """
    This function extracts
    meta description content
    when available and non-empty.

    :param BeautifulSoup soup:
    :return Optional[str] : description_text
    :exception na : na
    :note na
    """
    description_text = None

    meta_tag = soup.find("meta", attrs={"name": "description"})
    if meta_tag and meta_tag.get("content"):
        content_text = meta_tag.get("content").strip()
        if content_text:
            description_text = content_text

    return description_text


def _extract_first_paragraph(soup: BeautifulSoup) -> Optional[str]:
    """
    This function extracts
    the first paragraph text
    when available and non-empty.

    :param BeautifulSoup soup:
    :return Optional[str] : paragraph_text
    :exception na : na
    :note na
    """
    paragraph_text = None

    first_paragraph = soup.find("p")
    if first_paragraph:
        raw_text = first_paragraph.get_text(strip=True)
        if raw_text:
            paragraph_text = raw_text

    return paragraph_text


def _extract_links(soup: BeautifulSoup, base_url: str, seed_netloc: str) -> Tuple[List[str], List[str]]:
    """
    This function extracts
    internal and external links
    from anchors, using
    same-host classification and
    de-duplication.

    :param BeautifulSoup soup:
    :param str base_url:
    :param str seed_netloc:
    :return Tuple[List[str], List[str]] : internal_links, external_links
    :exception na : na
    :note na
    """
    seen_internal: Set[str] = set()
    seen_external: Set[str] = set()

    internal: List[str] = []
    external: List[str] = []

    anchors = soup.find_all("a", href=True)

    for anchor in anchors:
        raw = anchor.get("href")
        if raw is not None and raw != "":
            raw_lower = raw.lower()

            is_mailto = raw_lower.startswith("mailto:")
            is_javascript = raw_lower.startswith("javascript:")

            if not is_mailto and not is_javascript:
                abs_url = urljoin(base_url, raw)
                normalized_url = _normalize_url(abs_url)

                if _same_host(normalized_url, seed_netloc):
                    _add_unique_link(normalized_url, seen_internal, internal)
                else:
                    _add_unique_link(normalized_url, seen_external, external)

    return internal, external


def _add_unique_link(url: str, seen: Set[str], output: List[str]) -> None:
    """
    This function appends a URL to
    output only if it has not been seen.

    :param str url:
    :param Set[str] seen:
    :param List[str] output:
    :return None : na
    :exception na : na
    :note na
    """
    is_new = url not in seen
    if is_new:
        seen.add(url)
        output.append(url)


def _extract_meta_property_content(soup: BeautifulSoup, prop_value: str) -> Optional[str]:
    """
    This function extracts Open
    Graph meta content
    for a given property.

    :param BeautifulSoup soup:
    :param str prop_value:
    :return Optional[str] : content
    :exception na : na
    :note na
    """
    content = None

    meta_tag = soup.find("meta", attrs={"property": prop_value})
    if meta_tag and meta_tag.get("content"):
        raw = meta_tag.get("content").strip()
        if raw:
            content = raw

    return content


def _extract_instagram_username(description: Optional[str], og_title_content: Optional[str]) -> Optional[str]:
    """
    This function extracts an
    Instagram username using
    og:description patterns first,
    then og:title patterns.

    :param Optional[str] description:
    :param Optional[str] og_title_content:
    :return Optional[str] : username
    :exception na : na
    :note na
    """
    username: Optional[str] = None

    if description:
        match = re.search(r"-\s*([A-Za-z0-9_.]+)\s+on\b", description)
        if match:
            candidate = match.group(1).strip()
            if candidate:
                username = candidate

        if username is None:
            match = re.search(r"^([A-Za-z0-9_.]+)\s+on\b", description)
            if match:
                candidate = match.group(1).strip()
                if candidate:
                    username = candidate

    if username is None and og_title_content:
        paren_match = re.search(r"\(@([A-Za-z0-9_.]+)\)", og_title_content)
        if paren_match:
            username = paren_match.group(1)
        else:
            is_simple_handle = re.fullmatch(r"[A-Za-z0-9_.]+", og_title_content) is not None
            if is_simple_handle:
                username = og_title_content

    return username