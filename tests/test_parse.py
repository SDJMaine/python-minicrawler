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


