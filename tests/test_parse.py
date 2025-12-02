from minicrawler.parse import parse_page

def test_parse_page_extracts_title_and_internal_link() -> None:
    """
    This function tests that parse_page correctly extracts
    the page title and same-host internal links from HTML.

    :param na: na
    :return None: na
    :exception na: na
    :note na
    """
    html = """
    <html>
      <head><title>Example Page</title></head>
      <body>
        <a href="/about">About</a>
        <a href="https://other.com/">External</a>
      </body>
    </html>
    """
    base_url = "https://example.com/index.html"

    result = parse_page(html, base_url)

    assert result["title"] == "Example Page"
    assert "https://example.com/about" in result["internal_links"]
    assert all("other.com" not in url for url in result["internal_links"])