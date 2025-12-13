# ###########################################
# Name: Shayene Johnson
# Assignment: Final Project
# Purpose: Parse module for the web crawler
#          Parses HTML pages to extract
#          links, emails, images, and titles
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
    This function extracts a special description text
    from the HTML document, using the meta description
    tag or the first paragraph element.

    :param str html:
    :return Optional[str] : description_text
    :exception na : na
    :note na
    """
    soup = BeautifulSoup(html, "html.parser")
    meta_tag = soup.find("meta", attrs={"name": "description"})
    description_text = None

    if meta_tag and meta_tag.get("content"):
        content_text = meta_tag.get("content").strip()
        if content_text:
            description_text = content_text

    if description_text is None:
        first_paragraph = soup.find("p")
        if first_paragraph and first_paragraph.get_text(strip=True):
            description_text = first_paragraph.get_text(strip=True)

    return description_text

def parse_page(html: str, base_url: str, seed_netloc: str) -> Dict[str, object]:
    """
    This function parses a single HTML page
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

    seen_internal: Set[str] = set()
    seen_external: Set[str] = set()
    internal: List[str] = []
    external: List[str] = []

    anchors = soup.find_all("a", href=True)

    for anchor in anchors:
        raw = anchor.get("href")

        is_valid = (
                raw is not None
                and raw != ""
                and not raw.startswith("mailto:")
                and not raw.lower().startswith("javascript:")
        )

        if is_valid:
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

    emails = _extract_emails(soup)
    images = _extract_images(soup, base_url)

    parsed_page_info = {
        "title": title,
        "internal_links": internal,
        "external_links": external,
        "emails": emails,
        "images": images,
    }
    return parsed_page_info

def parse_instagram_post(html: str, url: str, status: int) -> Dict[str, object]:
    """
    This function parses an Instagram post page
    and returns basic information including:
    title, description, primary image URL, and
    the poster's username when available.

    :param str html:
    :param str url:
    :param int status:
    :return Dict[str, object] : instagram_post_info
    :exception na : na
    :note na
    """
    soup = BeautifulSoup(html, "html.parser")

    # Fallback HTML <title> (usually just "Instagram")
    title: Optional[str] = None
    if soup.title and soup.title.string:
        raw_title = soup.title.string.strip()
        if raw_title:
            title = raw_title

    # Description from Open Graph meta (likes + caption, etc.)
    description: Optional[str] = None
    og_desc = soup.find("meta", attrs={"property": "og:description"})
    if og_desc and og_desc.get("content"):
        desc_text = og_desc.get("content").strip()
        if desc_text:
            description = desc_text

    # Main image URL from Open Graph meta
    image_url: Optional[str] = None
    og_img = soup.find("meta", attrs={"property": "og:image"})
    if og_img and og_img.get("content"):
        img_text = og_img.get("content").strip()
        if img_text:
            image_url = img_text

            # Username extraction
    username: Optional[str] = None

    # 1) Prefer extracting the handle from og:description
    #    Patterns:
    #      "..., N comments - handle on <date>: ..."
    #      "handle on <date>: ..."
    if description:
        # pattern with a preceding dash: "- handle on ..."
        match = re.search(r"-\s*([A-Za-z0-9_.]+)\s+on\b", description)
        if match:
            candidate = match.group(1).strip()
            if candidate:
                username = candidate

        # if still None, pattern at the start: "handle on ..."
        if username is None:
            match = re.search(r"^([A-Za-z0-9_.]+)\s+on\b", description)
            if match:
                candidate = match.group(1).strip()
                if candidate:
                    username = candidate

    # 2) If not found in description, fall back to og:title
    og_title = soup.find("meta", attrs={"property": "og:title"})
    og_title_content: Optional[str] = None
    if og_title and og_title.get("content"):
        og_title_content = og_title.get("content").strip()

    if username is None and og_title_content:
        raw_og_title = og_title_content

        # Pattern like "Display Name (@handle) • Instagram photos ..."
        paren_match = re.search(r"\(@([A-Za-z0-9_.]+)\)", raw_og_title)
        if paren_match:
            username = paren_match.group(1)
        else:
            # If og:title is itself a simple handle (no spaces/specials),
            # treat it as the username; otherwise, leave it as None.
            if re.fullmatch(r"[A-Za-z0-9_.]+", raw_og_title):
                username = raw_og_title

                # Last fallback for title, if it remained None
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