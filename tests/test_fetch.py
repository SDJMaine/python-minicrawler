# ###########################################
# Name: Shayene Johnson
# Assignment: 8
# Purpose: Tester for fetch.py
#           function
# ###########################################

from minicrawler.fetch import _is_html, http_get

def test_is_html_recognizes_html_content_type() -> None:
    """
    This function tests that _is_html correctly identifies
    HTML Content-Type header values and rejects non-HTML
    or missing content types.

    :param na: na
    :return None: na
    :exception na: na
    :note tests the _is_html function
    """
    assert _is_html("text/html; charset=utf-8") is True
    assert _is_html("application/xhtml+xml") is True
    assert _is_html("application/json") is False
    assert _is_html(None) is False
