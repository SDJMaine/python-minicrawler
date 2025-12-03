# ###########################################
# Name: Shayene Johnson
# Assignment: 8
# Purpose: A tiny, polite, depth-1
#          web crawler for a single host.
# ###########################################

import logging
import time

from typing import Dict, Any, Iterable, List, Set, Optional
from urllib.parse import urlparse

from .fetch import http_get
from .parse import parse_page, _normalize_url

INTERNAL_LINK_LIMIT = 5
MIN_PAGES_ALLOWED = 1
SLEEP_MIN_DELAY = 0.0

def run(
        seed: str,
        max_pages: int,
        delay: float,
        timeout: int,
        retries: int, ) -> Iterable[Dict[str, object]]:
    """
    This function performs a depth-1 crawl
     starting from the given seed URL.
    It fetches the seed, discovers internal links,
     and then fetches those links
    up to the specified maximum number of pages.

    :param str seed: The seed URL to start crawling.
    :param int max_pages: Maximum number of pages to crawl.
    :param float delay: Delay in seconds between requests.
    :param int timeout: Timeout in seconds for HTTP requests.
    :param int retries: Number of retries for HTTP requests.
    :return Iterable[Dict[str, object]] : crawl_rows
    :exception na : na
    :note : Yield mostly replaces the need for a return statement here.
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
