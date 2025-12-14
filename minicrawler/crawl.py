# ###########################################
# Name: Shayene Johnson
# Assignment: Final Project
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
    pages_yielded = 0

    if max_pages < MIN_PAGES_ALLOWED:
        return

    if depth < MIN_DEPTH:
        depth = MIN_DEPTH
    if depth > MAX_DEPTH:
        depth = MAX_DEPTH

    seed_normalized = _normalize_url(seed)
    seed_host = urlparse(seed_normalized).netloc

    queue: deque[Tuple[str, int]] = deque()
    queue.append((seed_normalized, 0))
    seen_urls: Set[str] = set()
    seen_urls.add(seed_normalized)

    has_made_request = False
    queue_has_items = len(queue) > 0

    while queue_has_items and pages_yielded < max_pages:
        current_url, level = queue[0]
        queue.popleft()

        if has_made_request:
            sleep_delay = max(SLEEP_MIN_DELAY, delay)
            time.sleep(sleep_delay)

        logging.info("Fetching url=%s level=%d", current_url, level)
        status, final_url, html = http_get(
            current_url,
            timeout=timeout,
            retries=retries,
        )
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

            if level < depth - 1:
                new_links: List[str] = []
                link_index = 0
                total_links = len(internal_links)
                while link_index < total_links:
                    link_url = internal_links[link_index]
                    if link_url not in seen_urls:
                        seen_urls.add(link_url)
                        new_links.append(link_url)
                    link_index = link_index + 1

                for new_url in new_links:
                    queue.append((new_url, level + 1))

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
        pages_yielded = pages_yielded + 1
        queue_has_items = len(queue) > 0

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
    for page_info in _crawl_pages(
            seed=seed,
            max_pages=max_pages,
            delay=delay,
            timeout=timeout,
            retries=retries,
            depth=depth,
    ):
        internal_links = page_info["internal_links"]
        limited_links = internal_links[:INTERNAL_LINK_LIMIT]

        row = {
            "url": page_info["url"],
            "status": page_info["status"],
            "title": page_info["title"],
            "n_internal_links": len(limited_links),
            "links": limited_links,
            "level": page_info["level"],
            "external_links": page_info["external_links"],
            "n_external_links": len(page_info["external_links"]),
            "emails": page_info["emails"],
            "n_emails": len(page_info["emails"]),
            "images": page_info["images"],
            "n_images": len(page_info["images"]),
        }
        yield row

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
    seen_emails: Set[str] = set()
    seen_offsite: Set[str] = set()
    seen_images: Set[str] = set()

    for page_info in _crawl_pages(
            seed=seed,
            max_pages=max_pages,
            delay=delay,
            timeout=timeout,
            retries=retries,
            depth=depth,
    ):
        page_url = page_info["url"]
        if target == "emails":
            emails = page_info["emails"]
            for email in emails:
                if email not in seen_emails:
                    seen_emails.add(email)
                    row = {
                        "kind": "email",
                        "value": email,
                        "source_url": page_url,
                    }
                    yield row
        elif target == "offsite":
            external_links = page_info["external_links"]
            for link in external_links:
                if link not in seen_offsite:
                    seen_offsite.add(link)
                    row = {
                        "kind": "offsite_link",
                        "value": link,
                        "source_url": page_url,
                    }
                    yield row

        elif target == "images":
            images = page_info["images"]

            for img_url in images:
                if img_url not in seen_images:
                    seen_images.add(img_url)
                    row = {
                        "kind": "image",
                        "value": img_url,
                        "source_url": page_url,
                    }
                    yield row