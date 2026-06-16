# ###########################################
# Name: Shayene Johnson
# Purpose: A crawl module for the web crawler
#          Performs depth-limited crawling
#          and scrape traversal
# ###########################################

import logging
import time
from collections import deque

from typing import Dict, Iterable, List, Set, Optional, Iterator, Tuple
from urllib.parse import urlparse

from .fetch import http_get
from .parse import parse_page, _normalize_url

# **********************
# Constants (numerical only)
# **********************

START_LEVEL = 0
LEVEL_INCREMENT = 1

INTERNAL_LINK_LIMIT = 5
MIN_PAGES_ALLOWED = 1
SLEEP_MIN_DELAY = 0.0

MIN_DEPTH = 1
MAX_DEPTH = 3

def _crawl_pages(
        seed: str,
        max_pages: int,
        delay: float,
        timeout: int,
        retries: int,
        depth: int,
) -> Iterator[Dict[str, object]]:
    """
    This function performs a breadth-first crawl
    starting from the given seed URL.
    It follows same-host links up to the specified depth
    and yields page metadata and parsed content.

    :param str seed: Seed URL to start crawling.
    :param int max_pages: Maximum number of pages to crawl.
    :param float delay: Delay in seconds between requests.
    :param int timeout: Timeout in seconds for HTTP requests.
    :param int retries: Number of retries for HTTP requests.
    :param int depth: Maximum depth to follow links (1 to 3).
    :return Iterator[Dict[str, object]] : page_info_iterator
    :exception na : na
    :note na
    """
    pages_yielded = START_LEVEL
    should_crawl = True

    depth = _clamp_depth(depth)

    if max_pages < MIN_PAGES_ALLOWED:
        should_crawl = False

    if should_crawl:
        seed_host, queue, seen_urls = _initialize_crawl_state(seed)

        has_made_request = False
        queue_has_items = len(queue) > START_LEVEL

        while queue_has_items and pages_yielded < max_pages:
            current_url, level = queue[START_LEVEL]
            queue.popleft()

            _sleep_between_requests(has_made_request, delay)

            logging.info("Fetching url=%s level=%d", current_url, level)
            status, final_url, html = http_get(current_url, timeout=timeout, retries=retries,)
            has_made_request = True

            title: Optional[str] = None
            internal_links: List[str] = []
            external_links: List[str] = []
            emails: List[str] = []
            images: List[str] = []

            if html:
                parsed = parse_page(html, final_url, seed_host)
                title = parsed["title"]
                internal_links = parsed["internal_links"]
                external_links = parsed["external_links"]
                emails = parsed["emails"]
                images = parsed["images"]

                _enqueue_children_if_allowed(
                    level=level,
                    depth=depth,
                    internal_links=internal_links,
                    seen_urls=seen_urls,
                    queue=queue,
                )

            page_info = {
                "url": final_url,
                "status": status,
                "title": title,
                "internal_links": internal_links,
                "external_links": external_links,
                "emails": emails,
                "images": images,
                "level": level,
            }
            yield page_info

            pages_yielded = pages_yielded + LEVEL_INCREMENT
            queue_has_items = len(queue) > START_LEVEL

    return


def run(
        seed: str,
        max_pages: int,
        delay: float,
        timeout: int,
        retries: int,
        depth: int,
) -> Iterable[Dict[str, object]]:
    """
    This function performs a depth-limited crawl
    starting from the given seed URL.
    It fetches pages and yields summary rows
    suitable for NDJSON output.

    :param str seed: The seed URL to start crawling.
    :param int max_pages: Maximum number of pages to crawl.
    :param float delay: Delay in seconds between requests.
    :param int timeout: Timeout in seconds for HTTP requests.
    :param int retries: Number of retries for HTTP requests.
    :param int depth: Maximum depth to follow links.
    :return Iterable[Dict[str, object]] : crawl_rows
    :exception na : na
    :note na
    """
    page_iter = _crawl_pages(
        seed=seed,
        max_pages=max_pages,
        delay=delay,
        timeout=timeout,
        retries=retries,
        depth=depth,
    )

    for page_info in page_iter:
        internal_links = page_info["internal_links"]
        limited_links = internal_links[:INTERNAL_LINK_LIMIT]

        external_links = page_info["external_links"]
        emails = page_info["emails"]
        images = page_info["images"]

        row = {
            "url": page_info["url"],
            "status": page_info["status"],
            "title": page_info["title"],
            "n_internal_links": len(limited_links),
            "links": limited_links,
            "level": page_info["level"],
            "external_links": external_links,
            "n_external_links": len(external_links),
            "emails": emails,
            "n_emails": len(emails),
            "images": images,
            "n_images": len(images),
        }
        yield row

    return


def scrape_run(
        seed: str,
        max_pages: int,
        delay: float,
        timeout: int,
        retries: int,
        depth: int,
        target: str,
) -> Iterable[Dict[str, object]]:
    """
    This function performs a depth-limited crawl
    and yields scraped items based on the target:
    emails, offsite links, or images.

    :param str seed: Seed URL to start scraping from.
    :param int max_pages: Maximum number of pages to crawl.
    :param float delay: Delay in seconds between requests.
    :param int timeout: Timeout in seconds for HTTP requests.
    :param int retries: Number of retries for HTTP requests.
    :param int depth: Maximum depth to follow links.
    :param str target: Scrape target: emails, offsite, or images.
    :return Iterable[Dict[str, object]] : scrape_rows
    :exception na : na
    :note na
    """
    kind = ""
    values_key = ""
    seen_values: Set[str] = set()

    if target == "emails":
        kind = "email"
        values_key = "emails"
    elif target == "offsite":
        kind = "offsite_link"
        values_key = "external_links"
    elif target == "images":
        kind = "image"
        values_key = "images"

    page_iter = _crawl_pages(
        seed=seed,
        max_pages=max_pages,
        delay=delay,
        timeout=timeout,
        retries=retries,
        depth=depth,
    )

    for page_info in page_iter:
        if kind and values_key:
            page_url = page_info["url"]
            values = page_info[values_key]

            row_iter = _yield_unique_scrape_rows(
                kind=kind,
                values=values,
                seen_values=seen_values,
                source_url=page_url,
            )

            for row in row_iter:
                yield row

    return

# ********************************************
#            Helper functions
# ********************************************
def _initialize_crawl_state(seed: str) -> Tuple[str, deque[Tuple[str, int]], Set[str]]:
    """
    This function initializes crawl state:
    normalizes the seed, extracts the host,
    and prepares the BFS queue and seen set.

    :param str seed:
    :return Tuple[str, deque, Set[str]] : seed_host, queue, seen_urls
    :exception na : na
    :note na
    """
    seed_normalized = _normalize_url(seed)
    seed_host = urlparse(seed_normalized).netloc

    queue: deque[Tuple[str, int]] = deque()
    queue.append((seed_normalized, START_LEVEL))

    seen_urls: Set[str] = set()
    seen_urls.add(seed_normalized)

    return seed_host, queue, seen_urls


def _clamp_depth(depth: int) -> int:
    """
    This function clamps a
    requested crawl depth
    to the allowed range.

    :param int depth:
    :return int : clamped_depth
    :exception na : na
    :note na
    """
    clamped_depth = depth

    if clamped_depth < MIN_DEPTH:
        clamped_depth = MIN_DEPTH

    if clamped_depth > MAX_DEPTH:
        clamped_depth = MAX_DEPTH

    return clamped_depth


def _sleep_between_requests(has_made_request: bool, delay: float) -> None:
    """
    This function sleeps between
    HTTP requests after the first
    request has been made.

    :param bool has_made_request:
    :param float delay:
    :return None : na
    :exception na : na
    :note na
    """
    if has_made_request:
        sleep_delay = max(SLEEP_MIN_DELAY, delay)
        time.sleep(sleep_delay)

    return


def _collect_unseen_links(internal_links: List[str], seen_urls: Set[str]) -> List[str]:
    """
    This function collects
    internal links that have not
    been seen yet and marks them seen.

    :param List[str] internal_links:
    :param Set[str] seen_urls:
    :return List[str] : new_links
    :exception na : na
    :note na
    """
    new_links: List[str] = []

    for link_url in internal_links:
        if link_url not in seen_urls:
            seen_urls.add(link_url)
            new_links.append(link_url)

    return new_links

def _enqueue_children_if_allowed(
        level: int,
        depth: int,
        internal_links: List[str],
        seen_urls: Set[str],
        queue: deque[Tuple[str, int]],
) -> None:
    """
    This function enqueues
    child links when the
    current level is allowed
    to expand under the depth limit.

    :param int level:
    :param int depth:
    :param List[str] internal_links:
    :param Set[str] seen_urls:
    :param deque queue:
    :return None : na
    :exception na : na
    :note na
    """
    can_expand = level < (depth - LEVEL_INCREMENT)

    if can_expand:
        new_links = _collect_unseen_links(internal_links, seen_urls)
        next_level = level + LEVEL_INCREMENT
        for new_url in new_links:
            queue.append((new_url, next_level))

    return


def _yield_unique_scrape_rows(
        kind: str,
        values: List[str],
        seen_values: Set[str],
        source_url: str,
) -> Iterator[Dict[str, object]]:
    """
    This function yields
    scrape rows for unseen values
    and deduplicates across pages.

    :param str kind:
    :param List[str] values:
    :param Set[str] seen_values:
    :param str source_url:
    :return Iterator[Dict[str, object]] : row_iter
    :exception na : na
    :note na
    """
    index = START_LEVEL
    total = len(values)

    while index < total:
        value = values[index]
        if value not in seen_values:
            seen_values.add(value)
            row = {
                "kind": kind,
                "value": value,
                "source_url": source_url,
            }
            yield row
        index = index + LEVEL_INCREMENT

    return