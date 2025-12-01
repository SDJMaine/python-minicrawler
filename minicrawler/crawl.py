#!.venv/bin/python3
# ###########################################
# Name: Alexander Katrompas
# Assignment: 8
# Purpose: A tiny, polite, depth-1
#          web crawler for a single host.
# ###########################################

import sys
import argparse
import logging
import time
import json
import requests

from typing import Iterator, Dict, Any, Iterable, List, Set, Optional, Tuple
from urllib.parse import urljoin, urlparse, urlunparse
from bs4 import BeautifulSoup
from contextlib import contextmanager

HTML_MIME_PREFIXES = ("text/html", "application/xhtml+xml")

DEFAULT_MAX_PAGES = 50
DEFAULT_DELAY_SECONDS = 0.2
DEFAULT_TIMEOUT_SECONDS = 5
DEFAULT_RETRIES_COUNT = 1

STATUS_MIN_SUCCESS = 200
STATUS_MAX_SUCCESS = 299
STATUS_MIN_SERVER_ERROR = 500
STATUS_MAX_SERVER_ERROR = 599
STATUS_NONE = 0

INTERNAL_LINK_LIMIT = 5
MIN_PAGES_ALLOWED = 1
SLEEP_MIN_DELAY = 0.0

def _build_parser() -> argparse.ArgumentParser:
    """
    This function builds and returns the argument parser
    for the tiny, polite, depth-1 web crawler command line application.

    :param na: na
    :return argparse.ArgumentParser : parser
    :exception na : na
    :note na
    """
    parser = argparse.ArgumentParser(
        prog="crawler",
        description="A tiny, polite, depth-1 web crawler for a single host.",
    )
    subparsers = parser.add_subparsers(dest="cmd", required=True)

    crawl = subparsers.add_parser(
        "crawl",
        help="Crawl a seed page and its first-level internal links.",
    )
    crawl.add_argument(
        "--seed",
        required=True,
        help="Seed URL, e.g. https://example.com/",
    )
    crawl.add_argument(
        "--out",
        default="data.ndjson",
        help="Output file (default: data.ndjson)",
    )
    crawl.add_argument(
        "--max-pages",
        type=int,
        default=DEFAULT_MAX_PAGES,
        help="Total pages including seed (default: 50)",
    )
    crawl.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_DELAY_SECONDS,
        help="Delay seconds between requests (default: 0.2)",
    )
    crawl.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="HTTP timeout seconds (default: 5)",
    )
    crawl.add_argument(
        "--retries",
        type=int,
        default=DEFAULT_RETRIES_COUNT,
        help="Retries on timeout/5xx (default: 1)",
    )
    crawl.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR)",
    )
    return parser


def _is_html(content_type: Optional[str]) -> bool:
    """
    This function checks whether the provided Content-Type header value
    indicates that the HTTP response is HTML content.

    :param content_type: Optional[str]
    :return bool : is_html
    :exception na : na
    :note na
    """
    is_html = False
    if content_type:
        content_type_lower = content_type.lower()
        main_type = content_type_lower.split(";")[0].strip()
        is_html = any(
            main_type.startswith(prefix) for prefix in HTML_MIME_PREFIXES
        )
    return is_html


def http_get(
        url: str,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
        retries: int = DEFAULT_RETRIES_COUNT,
        user_agent: str = "MiniCrawler/0.1",
) -> Tuple[int, str, Optional[str]]:
    """
    This function performs an HTTP GET request for the given URL, following redirects
    and returning only HTML content in the 2xx range. It also retries on timeouts
    and 5xx responses up to the specified number of retries.

    :param url: str
    :return Tuple[int, str, Optional[str]] : status_finalurl_html
    :exception na : na
    :note na
    """
    attempt = 0
    last_exc = None
    status = STATUS_NONE
    final_url = url
    html = None
    max_attempts = retries + 1
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    }

    should_continue = True

    while attempt < max_attempts and should_continue:
        attempt += 1
        try:
            resp = requests.get(url, timeout=timeout, headers=headers)
            status = resp.status_code
            final_url = str(resp.url)
            content_type_header = resp.headers.get("Content-Type")
            is_html_response = _is_html(content_type_header)
            is_success = (
                    STATUS_MIN_SUCCESS
                    <= status
                    <= STATUS_MAX_SUCCESS
            )
            is_server_error = (
                    STATUS_MIN_SERVER_ERROR
                    <= status
                    <= STATUS_MAX_SERVER_ERROR
            )

            if is_success and is_html_response:
                html = resp.text
                should_continue = False
            elif is_server_error and attempt < max_attempts:
                logging.debug(
                    "5xx (%d) for %s; retrying (%d/%d)",
                    status,
                    url,
                    attempt,
                    max_attempts,
                )
            else:
                should_continue = False

        except (requests.Timeout, requests.ConnectionError) as exc:
            last_exc = exc
            if attempt < max_attempts:
                logging.debug(
                    "Network error for %s; retrying (%d/%d)",
                    url,
                    attempt,
                    max_attempts,
                )
            else:
                logging.warning(
                    "Network failure for %s after retries: %s",
                    url,
                    repr(exc),
                )

    return status, final_url, html


class _NDJSONWriter:
    """
    This class provides a simple NDJSON writer that writes
    one JSON object per line to the provided file handle.

    :param na: na
    :return na : na
    :exception na : na
    :note na
    """

    ######################
    # Public and Private
    ######################

    # **********************
    # Constructors/Destructor
    # **********************

    def __init__(self, fh) -> None:
        """
        This function initializes the NDJSON writer with an
        already-open file handle for output.

        :param fh: object
        :return None : na
        :exception na : na
        :note na
        """
        self.fh = fh

    # **********************
    # Getters/Accessors
    # **********************

    # (No explicit getters needed for this simple helper class.)

    # **********************
    # Setters/Mutators
    # **********************

    # (No explicit setters needed for this simple helper class.)

    # **********************
    # Printing Methods
    # **********************

    def write_row(self, row: Dict[str, Any]) -> None:
        """
        This function writes a single dictionary as a JSON object
        on one line of the NDJSON output file.

        :param row: Dict[str, Any]
        :return None : na
        :exception na : na
        :note na
        """
        self.fh.write(json.dumps(row, ensure_ascii=False) + "\n")


@contextmanager
def open_writer(path: str) -> Iterator[object]:
    """
    This function is a context manager that opens a file for NDJSON output
    and yields an NDJSON writer object with a write_row(row: dict) method.

    :param path: str
    :return Iterator[object] : writer_iterator
    :exception na : na
    :note na
    """
    mode = "w"
    encoding = "utf-8"
    newline_setting = ""
    with open(path, mode, encoding=encoding, newline=newline_setting) as fh:
        writer = _NDJSONWriter(fh)
        yield writer


def write_row(writer: object, row: Dict[str, Any]) -> None:
    """
    This function is a thin wrapper that writes a row using the provided writer,
    without requiring the caller to depend on the concrete writer class.

    :param writer: object
    :return None : na
    :exception na : na
    :note na
    """
    if hasattr(writer, "write_row"):
        writer.write_row(row)
    else:
        raise TypeError("Writer does not support write_row(row).")


def _normalize_url(url: str) -> str:
    """
    This function normalizes a URL by dropping fragments, lowercasing the scheme
    and netloc, stripping default ports, and removing trailing slashes when
    appropriate.

    :param url: str
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
    This function checks whether a given URL has the same host
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
    This function extracts and returns the page title from a BeautifulSoup
    HTML document, or None if no usable title is found.

    :param soup: BeautifulSoup
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
    This function parses a single HTML page and returns the page title and
    a list of internal links (same host as the base_url), normalized and deduplicated.

    :param html: str
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


def run(
        seed: str,
        max_pages: int,
        delay: float,
        timeout: int,
        retries: int,
) -> Iterable[Dict[str, object]]:
    """
    This function performs a depth-1 crawl starting from the given seed URL.
    It fetches the seed, discovers internal links, and then fetches those links
    up to the specified maximum number of pages.

    :param seed: str
    :return Iterable[Dict[str, object]] : crawl_rows
    :exception na : na
    :note na
    """
    if max_pages < MIN_PAGES_ALLOWED:
        return

    seed_normalized = _normalize_url(seed)
    seed_host = urlparse(seed_normalized).netloc

    fetched: Set[str] = set()

    logging.info("Fetching seed: %s", seed_normalized)
    status, final_url, html = http_get(
        seed_normalized,
        timeout=timeout,
        retries=retries,
    )
    fetched.add(final_url)

    links: List[str] = []
    title: Optional[str] = None
    candidates: List[str] = []

    if html:
        parsed = parse_page(html, final_url)
        title = parsed["title"]
        internal_links: List[str] = parsed["internal_links"]

        all_internal: List[str] = []
        for internal_url in internal_links:
            internal_host = urlparse(internal_url).netloc
            if internal_host == seed_host:
                all_internal.append(internal_url)

        candidates = []
        seen_candidates: Set[str] = set()
        for candidate_url in all_internal:
            is_new_candidate = (
                    candidate_url not in seen_candidates
                    and candidate_url != final_url
            )
            if is_new_candidate:
                seen_candidates.add(candidate_url)
                candidates.append(candidate_url)

        links = candidates[:INTERNAL_LINK_LIMIT]

    yield {
        "url": final_url,
        "status": status,
        "title": title,
        "n_internal_links": len(links if html else []),
        "links": links if html else [],
    }

    if max_pages > MIN_PAGES_ALLOWED:
        total_allowed = max_pages - MIN_PAGES_ALLOWED
        taken = 0

        for url in candidates:
            can_fetch_more = taken < total_allowed
            is_new_url = url not in fetched

            if can_fetch_more and is_new_url:
                sleep_delay = max(SLEEP_MIN_DELAY, delay)
                time.sleep(sleep_delay)
                logging.info("Fetching: %s", url)
                status, final_url, html = http_get(
                    url,
                    timeout=timeout,
                    retries=retries,
                )

                fetched.add(final_url)
                title = None
                child_links: List[str] = []

                if html:
                    parsed_child = parse_page(html, final_url)
                    title = parsed_child["title"]
                    all_internal_child: List[str] = parsed_child["internal_links"]
                    child_links = all_internal_child[:INTERNAL_LINK_LIMIT]

                yield {
                    "url": final_url,
                    "status": status,
                    "title": title,
                    "n_internal_links": len(child_links),
                    "links": child_links,
                }
                taken += 1


def main(argv: Optional[List[str]] = None) -> int:
    """
    This function is the application driver
    for a tiny, polite, depth-1 web crawler program that writes NDJSON output.

    :param argv: Optional[List[str]]
    :return int : status_code
    :exception na : na
    :note na
    """
    if argv is None:
        argv = sys.argv[1:]

    parser = _build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        format="%(levelname)s %(message)s",
        level=getattr(logging, args.log_level.upper(), logging.INFO),
    )

    logging.info("Starting crawl seed=%s max_pages=%d", args.seed, args.max_pages)
    count = 0

    with open_writer(args.out) as writer:
        for row in run(
                seed=args.seed,
                max_pages=args.max_pages,
                delay=args.delay,
                timeout=args.timeout,
                retries=args.retries,
        ):
            write_row(writer, row)
            count += 1

    logging.info("Done. Wrote %d rows to %s", count, args.out)
    return 0


if __name__ == "__main__":
    main()