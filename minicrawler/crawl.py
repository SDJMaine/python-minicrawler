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
        "crawl", help="Crawl a seed page and its first-level internal links."
    )
    crawl.add_argument(
        "--seed", required=True, help="Seed URL, e.g. https://example.com/"
    )
    crawl.add_argument(
        "--out", default="data.ndjson", help="Output file (default: data.ndjson)"
    )
    crawl.add_argument(
        "--max-pages",
        type=int,
        default=50,
        help="Total pages including seed (default: 50)",
    )
    crawl.add_argument(
        "--delay",
        type=float,
        default=0.2,
        help="Delay seconds between requests (default: 0.2)",
    )
    crawl.add_argument(
        "--timeout",
        type=int,
        default=5,
        help="HTTP timeout seconds (default: 5)",
    )
    crawl.add_argument(
        "--retries",
        type=int,
        default=1,
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
    if not content_type:
        return False
    ct = content_type.lower().split(";")[0].strip()
    return any(ct.startswith(prefix) for prefix in HTML_MIME_PREFIXES)


def http_get(
        url: str,
        timeout: int = 5,
        retries: int = 1,
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
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    }

    while True:
        attempt += 1
        try:
            resp = requests.get(url, timeout=timeout, headers=headers)
            status = resp.status_code
            final_url = str(resp.url)

            if 500 <= status <= 599 and attempt <= retries + 1:
                logging.debug(
                    "5xx (%d) for %s; retrying (%d/%d)",
                    status,
                    url,
                    attempt,
                    retries + 1,
                    )
                continue

            if 200 <= status <= 299 and _is_html(resp.headers.get("Content-Type")):
                return status, final_url, resp.text

            # Non-HTML or non-2xx: return status and final URL, html=None
            return status, final_url, None

        except (requests.Timeout, requests.ConnectionError) as exc:
            last_exc = exc
            if attempt <= retries + 1:
                logging.debug(
                    "Network error for %s; retrying (%d/%d)",
                    url,
                    attempt,
                    retries + 1,
                    )
                continue
            logging.warning(
                "Network failure for %s after retries: %s", url, repr(exc)
            )
            break

    # Exhausted
    return 0, url, None


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
    with open(path, mode, encoding=encoding, newline="") as fh:
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

    # strip default ports
    if (scheme == "http" and netloc.endswith(":80")) or (
            scheme == "https" and netloc.endswith(":443")
    ):
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
    return urlparse(url).netloc.lower() == seed_netloc.lower()


def _extract_title(soup: BeautifulSoup) -> Optional[str]:
    """
    This function extracts and returns the page title from a BeautifulSoup
    HTML document, or None if no usable title is found.

    :param soup: BeautifulSoup
    :return Optional[str] : title
    :exception na : na
    :note na
    """
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
        return title or None
    return None


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

    for anchor in soup.find_all("a", href=True):
        raw = anchor.get("href")
        abs_url = urljoin(base_url, raw)
        abs_url = _normalize_url(abs_url)
        if _same_host(abs_url, seed_netloc):
            if abs_url not in seen:
                seen.add(abs_url)
                internal.append(abs_url)

    return {"title": title, "internal_links": internal}


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
    if max_pages < 1:
        return

    seed = _normalize_url(seed)
    seed_host = urlparse(seed).netloc

    fetched: Set[str] = set()

    logging.info("Fetching seed: %s", seed)
    status, final_url, html = http_get(seed, timeout=timeout, retries=retries)
    fetched.add(final_url)

    links: List[str] = []
    title: Optional[str] = None

    if html:
        parsed = parse_page(html, final_url)
        title = parsed["title"]
        all_internal = [
            url for url in parsed["internal_links"] if urlparse(url).netloc == seed_host
        ]
        candidates: List[str] = []
        seen: Set[str] = set()
        for url in all_internal:
            if url not in seen and url != final_url:
                seen.add(url)
                candidates.append(url)
        links = candidates[:5]
    else:
        candidates = []

    yield {
        "url": final_url,
        "status": status,
        "title": title,
        "n_internal_links": len(links if html else []),
        "links": links if html else [],
    }

    if max_pages == 1:
        return

    total_allowed = max_pages - 1
    taken = 0

    for url in candidates:
        if taken >= total_allowed:
            break
        if url in fetched:
            continue

        time.sleep(max(0.0, delay))
        logging.info("Fetching: %s", url)
        status, final_url, html = http_get(url, timeout=timeout, retries=retries)

        fetched.add(final_url)
        title = None
        child_links: List[str] = []

        if html:
            parsed = parse_page(html, final_url)
            title = parsed["title"]
            all_internal = parsed["internal_links"]
            child_links = all_internal[:5]

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
    sys.exit(main())