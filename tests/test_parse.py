# ###########################################
# Name: Shayene Johnson
# Assignment: Final Project
# Purpose: Tester for parse.py
#          helper functions and parse_page
# ###########################################

from typing import List, Set

from bs4 import BeautifulSoup

from minicrawler.parse import (
    _normalize_url,
    _same_host,
    _extract_title,
    _extract_emails,
    _extract_images,
    parse_page,
    extract_description_content,
    parse_instagram_post,
)


def test_normalize_url_lowers_and_strips_default_ports() -> None:
    """
    This function tests that
    _normalize_url lowercases the scheme
    and netloc, strips default ports,
    and removes trailing slashes
    when appropriate.

    :param na: na
    :return None: na
    :exception na: na
    :note na
    """
    url_http = "HTTP://Example.COM:80/SomePath/"
    url_https = "https://Example.COM:443/foo/"
    url_https_non_default = "https://Example.COM:8443/foo/"

    normalized_http = _normalize_url(url_http)
    normalized_https = _normalize_url(url_https)
    normalized_non_default = _normalize_url(url_https_non_default)

    assert normalized_http == "http://example.com/SomePath"
    assert normalized_https == "https://example.com/foo"
    assert normalized_non_default == "https://example.com:8443/foo"


def test_same_host_compares_netloc_case_insensitive() -> None:
    """
    This function tests that
    _same_host returns True when
    the URL host matches the seed host
    regardless of case, and False
    otherwise.

    :param na: na
    :return None: na
    :exception na: na
    :note na
    """
    assert _same_host("https://Example.com/path", "example.com") is True
    assert _same_host("https://sub.example.com/path", "example.com") is False
    assert _same_host("https://other.com/", "example.com") is False

def test_extract_title_returns_clean_title_or_none() -> None:
    """
    This function tests that
    _extract_title returns a stripped
    title string when available
    and None when no usable
    title exists.

    :param na: na
    :return None: na
    :exception na: na
    :note na
    """
    html_with_title = "<html><head><title>  Example Page  </title></head><body></body></html>"
    soup_with_title = BeautifulSoup(html_with_title, "html.parser")
    title = _extract_title(soup_with_title)
    assert title == "Example Page"

    html_empty_title = "<html><head><title>   </title></head><body></body></html>"
    soup_empty = BeautifulSoup(html_empty_title, "html.parser")
    assert _extract_title(soup_empty) is None

    html_no_title = "<html><head></head><body></body></html>"
    soup_none = BeautifulSoup(html_no_title, "html.parser")
    assert _extract_title(soup_none) is None


def test_extract_emails_finds_mailto_and_text_and_deduplicates() -> None:
    """
    This function tests that
    _extract_emails finds email addresses
    both in mailto: links and in text,
    and returns a deduplicated list.

    :param na: na
    :return None: na
    :exception na: na
    :note na
    """
    html = """
    <html>
      <body>
        <a href="mailto:user@example.com">Email me</a>
        <p>Contact: user@example.com, other.user+test@example.org</p>
        <a href="mailto:other.user+test@example.org?subject=Hello">Another</a>
      </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    emails: List[str] = _extract_emails(soup)

    emails_set: Set[str] = set(emails)
    assert "user@example.com" in emails_set
    assert "other.user+test@example.org" in emails_set
    assert len(emails_set) == 2


def test_extract_images_normalizes_and_deduplicates() -> None:
    """
    This function tests that
    _extract_images resolves relative URLs,
    normalizes them, and deduplicates
    repeated image URLs.

    :param na: na
    :return None: na
    :exception na: na
    :note na
    """
    html = """
    <html>
      <body>
        <img src="/img/logo.png" />
        <img src="https://Example.com/img/logo.png" />
        <img src="images/other.png" />
      </body>
    </html>
    """
    base_url = "https://example.com/base/index.html"
    soup = BeautifulSoup(html, "html.parser")
    images: List[str] = _extract_images(soup, base_url)

    images_set: Set[str] = set(images)
    assert "https://example.com/img/logo.png" in images_set
    assert "https://example.com/base/images/other.png" in images_set
    assert len(images_set) == 2


def test_parse_page_extracts_title_links_emails_and_images() -> None:
    """
    This function tests that
    parse_page correctly extracts
    title, internal links, external links,
    emails, and images from HTML,
    including proper host classification,
    and that mailto: and javascript:
    href values are not treated as links.

    :param na: na
    :return None: na
    :exception na: na
    :note na
    """
    html = """
    <html>
      <head>
        <title>Example Page</title>
      </head>
      <body>
        <a href="/about">About</a>
        <a href="https://other.com/">External</a>
        <a href="mailto:user@example.com">Email</a>
        <a href="javascript:doSomething()">JS Link</a>
        <img src="/img/logo.png" />
      </body>
    </html>
    """
    base_url = "https://example.com/index.html"
    seed_netloc = "example.com"

    result = parse_page(html, base_url, seed_netloc)

    # title
    assert result["title"] == "Example Page"

    # internal vs external links
    assert result["internal_links"] == ["https://example.com/about"]
    assert result["external_links"] == ["https://other.com/"]

    # mailto and javascript links should not appear as internal or external URLs
    assert all("mailto:" not in url for url in result["internal_links"])
    assert all("mailto:" not in url for url in result["external_links"])
    assert all(not url.startswith("javascript:") for url in result["internal_links"])
    assert all(not url.startswith("javascript:") for url in result["external_links"])

    # emails
    emails_set = set(result["emails"])
    assert "user@example.com" in emails_set

    # images
    images_set = set(result["images"])
    assert "https://example.com/img/logo.png" in images_set


def test_parse_page_deduplicates_internal_and_external_links() -> None:
    """
    This function tests that
    parse_page deduplicates internal
    and external links even if the same
    URL appears multiple times in anchors.

    :param na: na
    :return None: na
    :exception na: na
    :note na
    """
    html = """
    <html>
      <body>
        <a href="/a">A1</a>
        <a href="/a">A2 duplicate</a>
        <a href="https://other.com/">Ext1</a>
        <a href="https://other.com/">Ext2 duplicate</a>
      </body>
    </html>
    """
    base_url = "https://example.com/index.html"
    seed_netloc = "example.com"

    result = parse_page(html, base_url, seed_netloc)

    assert result["internal_links"] == ["https://example.com/a"]
    assert result["external_links"] == ["https://other.com/"]


