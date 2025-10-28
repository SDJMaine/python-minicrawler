#!.venv/bin/python3
"""
A tiny, polite, depth-1 web crawler for a single host.
"""

import sys
import argparse
import logging
from typing import Dict, Iterable, List, Set, Tuple
import logging
import time
from typing import Iterator, Literal, Dict, Any
import json
from urllib.parse import urljoin, urlparse, urlunparse
from bs4 import BeautifulSoup
from typing import Optional, Tuple
from contextlib import contextmanager
import requests

HTML_MIME_PREFIXES = ("text/html", "application/xhtml+xml")

def _build_parser() -> argparse.ArgumentParser:
    """
    Build and return the argument parser.
    :return: argparse.ArgumentParser
    """
    p = argparse.ArgumentParser(
        prog="crawler",
        description="A tiny, polite, depth-1 web crawler for a single host."
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    crawl = sub.add_parser("crawl", help="Crawl a seed page and its first-level internal links.")
    crawl.add_argument("--seed", required=True, help="Seed URL, e.g. https://example.com/")
    crawl.add_argument("--out", default="data.ndjson", help="Output file (default: data.ndjson)")
    crawl.add_argument("--max-pages", type=int, default=50, help="Total pages including seed (default: 50)")
    crawl.add_argument("--delay", type=float, default=0.2, help="Delay seconds between requests (default: 0.2)")
    crawl.add_argument("--timeout", type=int, default=5, help="HTTP timeout seconds (default: 5)")
    crawl.add_argument("--retries", type=int, default=1, help="Retries on timeout/5xx (default: 1)")
    crawl.add_argument("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR)")
    return p

def _is_html(content_type: Optional[str]) -> bool:
    """
    Check if the given Content-Type indicates HTML content.
    :param content_type: Optional[str] - The Content-Type header value.
    :return: bool - True if HTML, False otherwise.
    """
    if not content_type:
        return False
    ct = content_type.lower().split(";")[0].strip()
    return any(ct.startswith(p) for p in HTML_MIME_PREFIXES)

def http_get(url: str, timeout: int = 5, retries: int = 1, user_agent: str = "MiniCrawler/0.1") -> Tuple[int, str, Optional[str]]:
    """
    Return (status, final_url, html or None).
    - Follows redirects (requests default).
    - Only returns HTML in the 2xx range; non-HTML => html=None (status still returned).
    - Retries on timeouts and 5xx up to `retries` times (not on 4xx).
    """
    attempt = 0
    last_exc = None
    headers = {"User-Agent": user_agent, "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8"}

    while True:
        attempt += 1
        try:
            resp = requests.get(url, timeout=timeout, headers=headers)
            status = resp.status_code
            final_url = str(resp.url)

            if 500 <= status <= 599 and attempt <= retries + 1:
                logging.debug("5xx (%d) for %s; retrying (%d/%d)", status, url, attempt, retries + 1)
                continue

            if 200 <= status <= 299 and _is_html(resp.headers.get("Content-Type")):
                return status, final_url, resp.text

            # Non-HTML or non-2xx: return status and final URL, html=None
            return status, final_url, None

        except (requests.Timeout, requests.ConnectionError) as exc:
            last_exc = exc
            if attempt <= retries + 1:
                logging.debug("Network error for %s; retrying (%d/%d)", url, attempt, retries + 1)
                continue
            logging.warning("Network failure for %s after retries: %s", url, repr(exc))
            break

    # Exhausted
    return 0, url, None


class _NDJSONWriter:
    """
    Simple NDJSON writer.
    Writes one JSON object per line.
    """
    def __init__(self, fh):
        self.fh = fh

    def write_row(self, row: Dict[str, Any]) -> None:
        self.fh.write(json.dumps(row, ensure_ascii=False) + "\n")


@contextmanager
def open_writer(path: str) -> Iterator[object]:
    """
    Context manager yielding a writer object with .write_row(row: dict).
    """
    mode = "w"
    encoding = "utf-8"
    with open(path, mode, encoding=encoding, newline="") as fh:
        writer = _NDJSONWriter(fh)
        yield writer

def write_row(writer: object, row: Dict[str, Any]) -> None:
    """
    Thin wrapper so caller doesn't depend on concrete classes.
    """
    if hasattr(writer, "write_row"):
        writer.write_row(row)
    else:
        raise TypeError("Writer does not support write_row(row).")


def _normalize_url(url: str) -> str:
    """
    Basic normalization:
      - drop fragments
      - lowercase scheme/netloc
      - strip default ports
      - remove trailing slash (except for root '/')
    """
    p = urlparse(url)
    scheme = p.scheme.lower()
    netloc = p.netloc.lower()

    # strip default ports
    if (scheme == "http" and netloc.endswith(":80")) or (scheme == "https" and netloc.endswith(":443")):
        netloc = netloc.rsplit(":", 1)[0]

    path = p.path or "/"
    if path != "/" and path.endswith("/"):
        path = path[:-1]

    return urlunparse((scheme, netloc, path, "", p.query, ""))

def _same_host(url: str, seed_netloc: str) -> bool:
    """
    Check if the given URL has the same host as the seed.
    :param url: url to check
    :param seed_netloc: seed netloc to compare against
    :return: bool - True if same host, False otherwise.
    """
    return urlparse(url).netloc.lower() == seed_netloc.lower()

def _extract_title(soup: BeautifulSoup) -> str | None:
    """
    Extract and return the title from the BeautifulSoup object.
    :param soup: BeautifulSoup - The parsed HTML soup.
    :return: Optional[str] - The title string or None if not found.
    """
    if soup.title and soup.title.string:
        t = soup.title.string.strip()
        return t or None
    return None

def parse_page(html: str, base_url: str) -> Dict[str, object]:
    """
    Return {'title': str|None, 'internal_links': List[str]}.
    Only includes same-host links (resolved relative to base_url), normalized and deduped.
    """
    soup = BeautifulSoup(html, "html.parser")
    title = _extract_title(soup)

    seed_netloc = urlparse(base_url).netloc
    seen = set()
    internal: List[str] = []

    for a in soup.find_all("a", href=True):
        raw = a.get("href")
        abs_url = urljoin(base_url, raw)
        # strip fragment + normalize
        abs_url = _normalize_url(abs_url)
        if _same_host(abs_url, seed_netloc):
            if abs_url not in seen:
                seen.add(abs_url)
                internal.append(abs_url)

    return {"title": title, "internal_links": internal}


def run(seed: str, max_pages: int, delay: float, timeout: int, retries: int) -> Iterable[Dict]:
    """
    Depth-1 crawl:
      1) Fetch seed
      2) Parse internal links from seed (same host only)
      3) Fetch those links (unique), stopping at max_pages total (including seed)
    Yields rows: {"url","status","title","n_internal_links","links"} where links is <= 5.
    """
    if max_pages < 1:
        return

    # Normalize seed early (and keep canonical host for filtering)
    seed = _normalize_url(seed)
    seed_host = urlparse(seed).netloc

    fetched: Set[str] = set()

    # --- Fetch seed
    logging.info("Fetching seed: %s", seed)
    status, final_url, html = http_get(seed, timeout=timeout, retries=retries)
    fetched.add(final_url)

    links: List[str] = []
    title = None
    if html:
        parsed = parse_page(html, final_url)
        title = parsed["title"]
        all_internal = [u for u in parsed["internal_links"] if urlparse(u).netloc == seed_host]
        # First-level links we might fetch:
        candidates = []
        seen = set()
        for u in all_internal:
            if u not in seen and u != final_url:
                seen.add(u)
                candidates.append(u)
        # for the row payload, keep only first 5
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

    # --- Fetch first-level pages (breadth-1), respecting max_pages and delay
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
            # Note: depth-1 => we do not follow these further; but record up to 5 internal links
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


######################
# main starts here
######################

# get argv from command line
argv = sys.argv[1:]
parser = _build_parser()
# parse arguments
args = parser.parse_args(argv)

# configure logging
logging.basicConfig(
    format="%(levelname)s %(message)s",
    level=getattr(logging, args.log_level.upper(), logging.INFO),
)

# log start of crawl
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
