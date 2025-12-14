# ###########################################
# Name: Shayene Johnson
# Assignment: Final Project
# Purpose: Tester for crawl.py
#          run, scrape_run, and _crawl_pages
# ###########################################

import typing as t

from minicrawler.crawl import (
    run,
    scrape_run,
    _crawl_pages,
)

def test_run_zero_max_pages_produces_no_results_and_no_requests(mocker) -> None:
    """
    This function tests that
    the crawl.run function
    produces no results and does not
    make HTTP requests
    when max_pages is less than
    the minimum allowed value.

    :param mocker: pytest mocker fixture
    :return None: na
    :exception na: na
    :note uses http_get mock to ensure no network calls
    """
    mocked_get = mocker.patch("minicrawler.crawl.http_get")

    rows: t.List[dict] = list(
        run(
            seed="https://example.com",
            max_pages=0,
            delay=0.0,
            timeout=1,
            retries=0,
            depth=1,
        )
    )

    assert rows == []
    mocked_get.assert_not_called()


def test_run_summarizes_page_info_and_limits_internal_links(mocker) -> None:
    """
    This function tests that
    crawl.run summarizes page info
    from _crawl_pages and limits
    the number of internal links
    to the configured limit.

    :param mocker: pytest mocker fixture
    :return None: na
    :exception na: na
    :note tests mapping from page_info to NDJSON row
    """
    fake_pages = [
        {
            "url": "https://example.com/",
            "status": 200,
            "title": "Home",
            "internal_links": [
                "https://example.com/a",
                "https://example.com/b",
                "https://example.com/c",
                "https://example.com/d",
                "https://example.com/e",
                "https://example.com/f",
            ],
            "external_links": ["https://other.com/"],
            "emails": [],
            "images": [],
            "level": 0,
        },
        {
            "url": "https://example.com/about",
            "status": 200,
            "title": "About",
            "internal_links": ["https://example.com/"],
            "external_links": [],
            "emails": [],
            "images": [],
            "level": 1,
        },
    ]

    mocker.patch(
        "minicrawler.crawl._crawl_pages",
        return_value=iter(fake_pages),
    )

    rows: t.List[dict] = list(
        run(
            seed="https://example.com/",
            max_pages=10,
            delay=0.0,
            timeout=1,
            retries=0,
            depth=3,
        )
    )

    assert len(rows) == 2

    first = rows[0]
    assert first["url"] == "https://example.com/"
    assert first["status"] == 200
    assert first["title"] == "Home"
    # links limited to 5 even though 6 internal_links exist
    assert len(first["links"]) == 5
    assert first["n_internal_links"] == 5
    assert first["level"] == 0
    assert first["external_links"] == ["https://other.com/"]

    second = rows[1]
    assert second["url"] == "https://example.com/about"
    assert second["status"] == 200
    assert second["title"] == "About"
    assert second["links"] == ["https://example.com/"]
    assert second["n_internal_links"] == 1
    assert second["level"] == 1
    assert second["external_links"] == []


def test_crawl_pages_respects_depth_and_avoids_duplicate_enqueues(mocker) -> None:
    """
    This function tests that
    _crawl_pages performs a breadth-first crawl,
    respects the depth limit,
    and does not enqueue duplicate URLs.

    :param mocker: pytest mocker fixture
    :return None: na
    :exception na: na
    :note tests BFS, depth, and dedup logic
    """
    seed = "https://example.com/"

    def fake_http_get(url: str, timeout: int, retries: int):
        return 200, url, "<html>dummy</html>"

    def fake_parse_page(html: str, final_url: str, seed_host: str) -> dict:
        if final_url == "https://example.com/":
            return {
                "title": "Home",
                "internal_links": [
                    "https://example.com/a",
                    "https://example.com/a",  # duplicate
                    "https://example.com/b",
                    "https://other.com/",     # offsite
                ],
                "external_links": ["https://other.com/"],
                "emails": [],
                "images": [],
            }
        if final_url == "https://example.com/a":
            return {
                "title": "A",
                "internal_links": ["https://example.com/c"],
                "external_links": [],
                "emails": [],
                "images": [],
            }
        if final_url == "https://example.com/b":
            return {
                "title": "B",
                "internal_links": [],
                "external_links": [],
                "emails": [],
                "images": [],
            }
        if final_url == "https://example.com/c":
            return {
                "title": "C",
                "internal_links": [],
                "external_links": [],
                "emails": [],
                "images": [],
            }
        return {
            "title": None,
            "internal_links": [],
            "external_links": [],
            "emails": [],
            "images": [],
        }

    mocker.patch("minicrawler.crawl.http_get", side_effect=fake_http_get)
    mocker.patch("minicrawler.crawl.parse_page", side_effect=fake_parse_page)

    pages: t.List[dict] = list(
        _crawl_pages(
            seed=seed,
            max_pages=10,
            delay=0.0,
            timeout=1,
            retries=0,
            depth=2,
        )
    )

    urls = [p["url"] for p in pages]
    levels = [p["level"] for p in pages]

    # depth=2 => only levels 0 and 1; "c" should not be visited
    assert "https://example.com/" in urls
    assert "https://example.com/a" in urls
    assert "https://example.com/b" in urls
    assert "https://example.com/c" not in urls
    assert max(levels) == 1
    # BFS order: seed, then its immediate children
    assert urls[0] == "https://example.com/"


def test_scrape_run_emails_deduplicates_across_pages(mocker) -> None:
    """
    This function tests that
    scrape_run with target 'emails'
    yields each email only once,
    even if it appears on multiple pages.

    :param mocker: pytest mocker fixture
    :return None: na
    :exception na: na
    :note tests email scraping and de-duplication
    """
    fake_pages = [
        {
            "url": "https://example.com/",
            "status": 200,
            "title": "Home",
            "internal_links": [],
            "external_links": [],
            "emails": ["a@example.com", "b@example.com"],
            "images": [],
            "level": 0,
        },
        {
            "url": "https://example.com/about",
            "status": 200,
            "title": "About",
            "internal_links": [],
            "external_links": [],
            "emails": ["b@example.com", "c@example.com"],
            "images": [],
            "level": 1,
        },
    ]

    mocker.patch(
        "minicrawler.crawl._crawl_pages",
        return_value=iter(fake_pages),
    )

    rows: t.List[dict] = list(
        scrape_run(
            seed="https://example.com/",
            max_pages=10,
            delay=0.0,
            timeout=1,
            retries=0,
            depth=3,
            target="emails",
        )
    )

    values = [row["value"] for row in rows]
    assert values == ["a@example.com", "b@example.com", "c@example.com"]

    kinds = {row["kind"] for row in rows}
    assert kinds == {"email"}

    mapping = {row["value"]: row["source_url"] for row in rows}
    assert mapping["a@example.com"] == "https://example.com/"
    assert mapping["b@example.com"] == "https://example.com/"
    assert mapping["c@example.com"] == "https://example.com/about"

def test_scrape_run_offsite_deduplicates_across_pages(mocker) -> None:
    """
    This function tests that
    scrape_run with target 'offsite'
    yields each external link only once,
    even if it appears on multiple pages.

    :param mocker: pytest mocker fixture
    :return None: na
    :exception na: na
    :note tests offsite link scraping and de-duplication
    """
    fake_pages = [
        {
            "url": "https://example.com/",
            "status": 200,
            "title": "Home",
            "internal_links": [],
            "external_links": ["https://other.com/a", "https://other.com/b"],
            "emails": [],
            "images": [],
            "level": 0,
        },
        {
            "url": "https://example.com/next",
            "status": 200,
            "title": "Next",
            "internal_links": [],
            "external_links": ["https://other.com/b", "https://other.com/c"],
            "emails": [],
            "images": [],
            "level": 1,
        },
    ]

    mocker.patch(
        "minicrawler.crawl._crawl_pages",
        return_value=iter(fake_pages),
    )

    rows: t.List[dict] = list(
        scrape_run(
            seed="https://example.com/",
            max_pages=10,
            delay=0.0,
            timeout=1,
            retries=0,
            depth=3,
            target="offsite",
        )
    )

    values = [row["value"] for row in rows]
    assert values == [
        "https://other.com/a",
        "https://other.com/b",
        "https://other.com/c",
    ]

    kinds = {row["kind"] for row in rows}
    assert kinds == {"offsite_link"}


def test_scrape_run_images_deduplicates_across_pages(mocker) -> None:
    """
    This function tests that
    scrape_run with target 'images'
    yields each image URL only once,
    even if it appears on multiple pages.

    :param mocker: pytest mocker fixture
    :return None: na
    :exception na: na
    :note tests image scraping and de-duplication
    """
    fake_pages = [
        {
            "url": "https://example.com/",
            "status": 200,
            "title": "Home",
            "internal_links": [],
            "external_links": [],
            "emails": [],
            "images": ["https://example.com/a.png", "https://example.com/b.png"],
            "level": 0,
        },
        {
            "url": "https://example.com/next",
            "status": 200,
            "title": "Next",
            "internal_links": [],
            "external_links": [],
            "emails": [],
            "images": ["https://example.com/b.png", "https://example.com/c.png"],
            "level": 1,
        },
    ]

    mocker.patch(
        "minicrawler.crawl._crawl_pages",
        return_value=iter(fake_pages),
    )

    rows: t.List[dict] = list(
        scrape_run(
            seed="https://example.com/",
            max_pages=10,
            delay=0.0,
            timeout=1,
            retries=0,
            depth=3,
            target="images",
        )
    )

    values = [row["value"] for row in rows]
    assert values == [
        "https://example.com/a.png",
        "https://example.com/b.png",
        "https://example.com/c.png",
    ]

    kinds = {row["kind"] for row in rows}
    assert kinds == {"image"}


def test_scrape_run_unknown_target_yields_no_rows(mocker) -> None:
    """
    This function tests that
    scrape_run yields no rows
    when the target is not recognized.

    :param mocker: pytest mocker fixture
    :return None: na
    :exception na: na
    :note tests default path for invalid target
    """
    fake_pages = [
        {
            "url": "https://example.com/",
            "status": 200,
            "title": "Home",
            "internal_links": [],
            "external_links": ["https://other.com/"],
            "emails": ["a@example.com"],
            "images": ["https://example.com/a.png"],
            "level": 0,
        },
    ]

    mocker.patch(
        "minicrawler.crawl._crawl_pages",
        return_value=iter(fake_pages),
    )

    rows: t.List[dict] = list(
        scrape_run(
            seed="https://example.com/",
            max_pages=10,
            delay=0.0,
            timeout=1,
            retries=0,
            depth=3,
            target="unknown",
        )
    )

    assert rows == []

def test_scrape_run_offsite_rows_include_kind_value_and_source_url(mocker) -> None:
    fake_pages = [
        {
            "url": "https://example.com/",
            "status": 200,
            "title": "Home",
            "internal_links": [],
            "external_links": ["https://other.com/a"],
            "emails": [],
            "images": [],
            "level": 0,
        },
    ]

    mocker.patch("minicrawler.crawl._crawl_pages", return_value=iter(fake_pages))

    rows = list(
        scrape_run(
            seed="https://example.com/",
            max_pages=10,
            delay=0.0,
            timeout=1,
            retries=0,
            depth=2,
            target="offsite",
        )
    )

    assert len(rows) == 1
    row = rows[0]
    assert row["kind"] == "offsite_link"
    assert row["value"] == "https://other.com/a"
    assert row["source_url"] == "https://example.com/"