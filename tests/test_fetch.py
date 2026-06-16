# ###########################################
# Name: Shayene Johnson
# Purpose: Tester for fetch.py
#           functions
# ###########################################

import requests

from minicrawler.fetch import (
    _is_html,
    http_get,
    STATUS_NONE,
)


def test_is_html_recognizes_html_content_type() -> None:
    """
    This function tests that
    _is_html correctly identifies
    HTML Content-Type header values
    and rejects non-HTML
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


def test_http_get_returns_html_for_success_html_response(mocker) -> None:
    """
    This function tests that
    http_get returns status, final_url,
    and HTML text when the response
    is a 2xx HTML page.

    :param mocker: pytest mocker fixture
    :return None: na
    :exception na: na
    :note tests the basic 2xx HTML success path
    """
    url = "https://example.com/"
    html_text = "<html><head><title>Test</title></head><body>OK</body></html>"

    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.url = url
    mock_response.headers = {"Content-Type": "text/html; charset=utf-8"}
    mock_response.text = html_text

    mocked_get = mocker.patch(
        "minicrawler.fetch.requests.get",
        return_value=mock_response,
    )

    status, final_url, html = http_get(url)

    assert status == 200
    assert final_url == url
    assert html == html_text
    assert mocked_get.call_count == 1


def test_http_get_filters_out_non_html_success_response(mocker) -> None:
    """
    This function tests that
    http_get does not return HTML
    when the response is 2xx but
    the Content-Type is non-HTML.

    :param mocker: pytest mocker fixture
    :return None: na
    :exception na: na
    :note tests non-HTML 2xx path
    """
    url = "https://api.example.com/data"

    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.url = url
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.text = '{"key": "value"}'

    mocked_get = mocker.patch(
        "minicrawler.fetch.requests.get",
        return_value=mock_response,
    )

    status, final_url, html = http_get(url)

    assert status == 200
    assert final_url == url
    assert html is None
    assert mocked_get.call_count == 1


def test_http_get_retries_on_5xx_and_succeeds(mocker) -> None:
    """
    This function tests that
    http_get retries when it first
    receives a 5xx response and
    then succeeds on a later attempt.

    :param mocker: pytest mocker fixture
    :return None: na
    :exception na: na
    :note tests retry behavior on 5xx
    """
    url = "https://example.com/"

    first_response = mocker.Mock()
    first_response.status_code = 503
    first_response.url = url
    first_response.headers = {"Content-Type": "text/html"}
    first_response.text = "Service Unavailable"

    second_response = mocker.Mock()
    second_response.status_code = 200
    second_response.url = url
    second_response.headers = {"Content-Type": "text/html"}
    second_response.text = "<html>OK</html>"

    mocked_get = mocker.patch(
        "minicrawler.fetch.requests.get",
        side_effect=[first_response, second_response],
    )

    status, final_url, html = http_get(url, retries=1)

    assert status == 200
    assert final_url == url
    assert html == "<html>OK</html>"
    assert mocked_get.call_count == 2


def test_http_get_retries_on_timeout_and_then_fails(mocker) -> None:
    """
    This function tests that
    http_get retries on network timeouts
    up to the retry limit
    and then returns STATUS_NONE
    with no HTML when all attempts fail.

    :param mocker: pytest mocker fixture
    :return None: na
    :exception na: na
    :note tests timeout retry failure path
    """
    url = "https://example.com/"

    mocked_get = mocker.patch(
        "minicrawler.fetch.requests.get",
        side_effect=requests.Timeout("timeout"),
    )

    retries = 2
    status, final_url, html = http_get(url, retries=retries, timeout=1)

    assert status == STATUS_NONE
    assert final_url == url
    assert html is None
    assert mocked_get.call_count == retries + 1


def test_http_get_sets_expected_headers(mocker) -> None:
    """
    This function tests that
    http_get sends the expected
    User-Agent and Accept headers
    with the HTTP request.

    :param mocker: pytest mocker fixture
    :return None: na
    :exception na : na
    :note tests HTTP request headers
    """
    url = "https://example.com/"
    custom_agent = "MiniCrawlerTest/1.0"

    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.url = url
    mock_response.headers = {"Content-Type": "text/html"}
    mock_response.text = "<html>OK</html>"

    mocked_get = mocker.patch(
        "minicrawler.fetch.requests.get",
        return_value=mock_response,
    )

    status, final_url, html = http_get(
        url,
        user_agent=custom_agent,
    )

    assert status == 200
    assert final_url == url
    assert html == "<html>OK</html>"

    assert mocked_get.call_count == 1
    _, kwargs = mocked_get.call_args
    headers = kwargs.get("headers", {})

    assert headers.get("User-Agent") == custom_agent
    assert "text/html" in headers.get("Accept", "")

def test_is_html_handles_case_and_whitespace() -> None:
    assert _is_html(" Text/HTML ; charset=utf-8 ") is True
    assert _is_html("APPLICATION/XHTML+XML") is True
    assert _is_html(" text/plain ") is False

def test_http_get_does_not_retry_on_4xx(mocker) -> None:
    url = "https://example.com/notfound"

    resp = mocker.Mock()
    resp.status_code = 404
    resp.url = url
    resp.headers = {"Content-Type": "text/html; charset=utf-8"}
    resp.text = "<html>Not Found</html>"

    mocked_get = mocker.patch(
        "minicrawler.fetch.requests.get",
        return_value=resp,
    )

    status, final_url, html = http_get(url, retries=3)

    assert status == 404
    assert final_url == url
    assert html is None
    assert mocked_get.call_count == 1  # no retry on 4xx

def test_http_get_does_not_retry_on_3xx(mocker) -> None:
    url = "https://example.com/redirect"

    resp = mocker.Mock()
    resp.status_code = 302
    resp.url = "https://example.com/new"
    resp.headers = {"Content-Type": "text/html"}
    resp.text = "<html>Redirect</html>"

    mocked_get = mocker.patch(
        "minicrawler.fetch.requests.get",
        return_value=resp,
    )

    status, final_url, html = http_get(url, retries=3)

    assert status == 302
    assert final_url == "https://example.com/new"
    assert html is None
    assert mocked_get.call_count == 1  # no retry on 3xx

def test_http_get_retries_on_connection_error_and_then_succeeds(mocker) -> None:
    url = "https://example.com/"

    ok_resp = mocker.Mock()
    ok_resp.status_code = 200
    ok_resp.url = url
    ok_resp.headers = {"Content-Type": "text/html"}
    ok_resp.text = "<html>OK</html>"

    mocked_get = mocker.patch(
        "minicrawler.fetch.requests.get",
        side_effect=[
            requests.ConnectionError("conn"),
            ok_resp,
        ],
    )

    status, final_url, html = http_get(url, retries=1)

    assert status == 200
    assert final_url == url
    assert html == "<html>OK</html>"
    assert mocked_get.call_count == 2

def test_http_get_no_retries_means_single_attempt(mocker) -> None:
    url = "https://example.com/"

    mocked_get = mocker.patch(
        "minicrawler.fetch.requests.get",
        side_effect=requests.Timeout("timeout"),
    )

    status, final_url, html = http_get(url, retries=0, timeout=1)

    assert status == STATUS_NONE
    assert final_url == url
    assert html is None
    assert mocked_get.call_count == 1

def test_http_get_passes_timeout_value_to_requests(mocker) -> None:
    url = "https://example.com/"
    timeout_val = 17

    resp = mocker.Mock()
    resp.status_code = 200
    resp.url = url
    resp.headers = {"Content-Type": "text/html"}
    resp.text = "<html>OK</html>"

    mocked_get = mocker.patch(
        "minicrawler.fetch.requests.get",
        return_value=resp,
    )

    status, final_url, html = http_get(url, timeout=timeout_val)

    assert status == 200
    assert final_url == url
    assert html == "<html>OK</html>"

    _, kwargs = mocked_get.call_args
    assert kwargs.get("timeout") == timeout_val

def test_http_get_treats_missing_content_type_as_non_html(mocker) -> None:
    url = "https://example.com/"

    resp = mocker.Mock()
    resp.status_code = 200
    resp.url = url
    resp.headers = {}  # missing Content-Type
    resp.text = "<html>OK</html>"

    mocked_get = mocker.patch(
        "minicrawler.fetch.requests.get",
        return_value=resp,
    )

    status, final_url, html = http_get(url)

    assert status == 200
    assert final_url == url
    assert html is None
    assert mocked_get.call_count == 1

