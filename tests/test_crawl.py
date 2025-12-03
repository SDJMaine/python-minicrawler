# ###########################################
# Name: Shayene Johnson
# Assignment: 8
# Purpose: Tester for crawl.py
#          run function
# ###########################################

import typing as t

from minicrawler.crawl import run

def test_run_zero_max_pages_produces_no_results() -> None:
    """
   This function tests that
   the crawl.run function
   produces no results
   when max_pages is less than
   the minimum allowed value.

   :param na: na
   :return None: na
   :exception na: na
   :note na
   """
    rows: t.List[dict] = list(
        run(
            seed="https://example.com",
            max_pages=0,      # below MIN_PAGES_ALLOWED, so no network call
            delay=0.0,
            timeout=1,
            retries=0,
        )
    )
    assert rows == []