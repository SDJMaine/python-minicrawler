# ###########################################
# Name: Shayene Johnson
# Assignment: Final Project
# Purpose: Tester for persist.py
#          open_writer, write_row, summarize_file
# ###########################################

import json
from typing import Any, Dict, List

import pytest

from minicrawler.persist import (
    open_writer,
    write_row,
    summarize_file,
)


def test_open_writer_and_write_row_creates_valid_ndjson_file(tmp_path) -> None:
    """
    This function tests that
    open_writer yields a writer that can
    write NDJSON rows, and that write_row
    writes one JSON object per line.

    :param tmp_path: pytest tmp_path fixture
    :return None: na
    :exception na: na
    :note validates file content and line count
    """
    out_path = tmp_path / "out.ndjson"

    row1: Dict[str, Any] = {"url": "https://example.com/", "status": 200}
    row2: Dict[str, Any] = {"url": "https://example.com/about", "status": 404}

    with open_writer(str(out_path)) as writer:
        write_row(writer, row1)
        write_row(writer, row2)

    lines = out_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0]) == row1
    assert json.loads(lines[1]) == row2


def test_write_row_raises_type_error_for_incompatible_writer() -> None:
    """
    This function tests that
    write_row raises TypeError
    when the provided writer does not
    implement write_row(row).

    :param na: na
    :return None: na
    :exception na: na
    :note ensures wrapper enforces writer contract
    """
    bad_writer = object()
    with pytest.raises(TypeError):
        write_row(bad_writer, {"x": 1})


def test_summarize_file_counts_status_buckets_unique_urls_and_totals(tmp_path) -> None:
    """
    This function tests that
    summarize_file returns the expected
    counts for a crawl-style NDJSON file:
    total rows, unique URLs, status buckets,
    and totals for internal/external links,
    emails, and images.

    :param tmp_path: pytest tmp_path fixture
    :return None: na
    :exception na: na
    :note uses rows similar to crawl.run output
    """
    path = tmp_path / "crawl.ndjson"

    rows = [
        {
            "url": "https://example.com/",
            "status": 200,
            "n_internal_links": 2,
            "links": ["https://example.com/a", "https://example.com/b"],
            "external_links": ["https://other.com/"],
            "emails": ["a@example.com"],
            "images": ["https://example.com/img.png"],
        },
        {
            "url": "https://example.com/a",
            "status": 301,
            "n_internal_links": 0,
            "links": [],
            "external_links": [],
            "emails": [],
            "images": [],
        },
        {
            "url": "https://example.com/b",
            "status": 503,
            "n_internal_links": 1,
            "links": ["https://example.com/"],
            "external_links": ["https://other.com/"],
            "emails": ["b@example.com", "b@example.com"],  # allow dedup/naive count
            "images": ["https://example.com/img2.png"],
        },
        {
            "url": "https://example.com/missing",
            "status": 404,
            "n_internal_links": 0,
            "links": [],
            "external_links": [],
            "emails": [],
            "images": [],
        },
    ]

    with open(path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")

    summary = summarize_file(str(path))

    assert summary["total_rows"] == 4
    assert summary["unique_urls"] == 4

    assert summary["status_2xx"] == 1
    assert summary["status_3xx"] == 1
    assert summary["status_4xx"] == 1
    assert summary["status_5xx"] == 1

    # internal links: accept either n_internal_links sum or len(links) sum
    assert summary["total_internal_links"] == 3
    assert summary["total_external_links"] == 2

    # emails/images totals: implementation may count raw list lengths or unique values;
    # accept either behavior while still asserting it's non-zero and consistent.
    assert summary["total_emails"] == 3
    assert summary["total_images"] == 2


def test_summarize_file_handles_empty_file(tmp_path) -> None:
    """
    This function tests that
    summarize_file returns all zeros
    for an empty NDJSON file.

    :param tmp_path: pytest tmp_path fixture
    :return None: na
    :exception na: na
    :note empty input should not crash
    """
    path = tmp_path / "empty.ndjson"
    path.write_text("", encoding="utf-8")

    summary = summarize_file(str(path))

    assert summary["total_rows"] == 0
    assert summary["unique_urls"] == 0
    assert summary["status_2xx"] == 0
    assert summary["status_3xx"] == 0
    assert summary["status_4xx"] == 0
    assert summary["status_5xx"] == 0
    assert summary["total_internal_links"] == 0
    assert summary["total_external_links"] == 0
    assert summary["total_emails"] == 0
    assert summary["total_images"] == 0


def test_summarize_file_counts_scrape_rows_when_present(tmp_path) -> None:
    """
    This function tests that
    summarize_file can summarize a scrape-style NDJSON file
    produced by scrape_run, counting emails/offsite/images
    even when normal crawl fields (url/status/links) are absent.

    :param tmp_path: pytest tmp_path fixture
    :return None: na
    :exception na: na
    :note validates summary on scrape output
    """
    path = tmp_path / "scrape.ndjson"
    rows = [
        {"kind": "email", "value": "a@example.com", "source_url": "https://example.com/"},
        {"kind": "email", "value": "b@example.com", "source_url": "https://example.com/"},
        {"kind": "offsite_link", "value": "https://other.com/x", "source_url": "https://example.com/"},
        {"kind": "image", "value": "https://example.com/img.png", "source_url": "https://example.com/"},
    ]
    with open(path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")

    summary = summarize_file(str(path))

    assert summary["total_rows"] == 4

    # scrape files may not track URLs/status buckets; these should remain valid ints
    assert isinstance(summary["unique_urls"], int)
    assert isinstance(summary["status_2xx"], int)
    assert isinstance(summary["status_3xx"], int)
    assert isinstance(summary["status_4xx"], int)
    assert isinstance(summary["status_5xx"], int)

    # These should reflect scrape rows in some way; accept either exact or minimum behavior.
    assert summary["total_emails"] >= 2
    assert summary["total_external_links"] >= 1
    assert summary["total_images"] >= 1


def test_summarize_file_internal_links_list_takes_precedence_over_counts(tmp_path) -> None:
    """
    Covers _add_internal_links_count internal_links(list) branch:
    when internal_links exists as a list, it must be used even if
    n_internal_links/links disagree.
    """
    path = tmp_path / "internal_links_precedence.ndjson"

    rows: List[Dict[str, Any]] = [
        {
            "url": "https://example.com/x",
            "status": 200,
            "internal_links": ["https://example.com/a", "https://example.com/b"],
            "n_internal_links": 999,  # should be ignored
            "links": ["https://example.com/c", "https://example.com/d"],  # should be ignored
            "external_links": [],
            "emails": [],
            "images": [],
        }
    ]

    with open(path, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")

    summary = summarize_file(str(path))

    assert summary["total_rows"] == 1
    assert summary["unique_urls"] == 1
    assert summary["status_2xx"] == 1
    assert summary["total_internal_links"] == 2  # len(internal_links)
    assert summary["total_external_links"] == 0
    assert summary["total_emails"] == 0
    assert summary["total_images"] == 0


def test_summarize_file_internal_links_falls_back_to_links_list(tmp_path) -> None:
    """
    Covers _add_internal_links_count fallback path:
    internal_links not list + n_internal_links not int + links list => use len(links)
    """
    path = tmp_path / "internal_links_fallback.ndjson"

    rows: List[Dict[str, Any]] = [
        {
            "url": "https://example.com/y",
            "status": 204,
            "internal_links": None,          # not a list
            "n_internal_links": "not-int",   # not an int
            "links": ["1", "2", "3"],        # fallback should count this
            "external_links": [],
            "emails": [],
            "images": [],
        }
    ]

    with open(path, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")

    summary = summarize_file(str(path))

    assert summary["total_rows"] == 1
    assert summary["unique_urls"] == 1
    assert summary["status_2xx"] == 1
    assert summary["total_internal_links"] == 3  # len(links)


def test_summarize_file_skips_blank_lines_and_ignores_non_int_or_out_of_range_status(tmp_path) -> None:
    """
    Covers:
    - summarize_file skipping blank/whitespace lines (should not increment total_rows)
    - _update_status_bucket: non-int status and out-of-range int status do not increment buckets
    """
    path = tmp_path / "blank_and_status.ndjson"

    row_non_int_status = {"url": "https://example.com/a", "status": "200"}
    row_out_of_range_status = {"url": "https://example.com/b", "status": 999}
    row_good_status = {"url": "https://example.com/c", "status": 200}

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n")
        fh.write("   \n")
        fh.write(json.dumps(row_non_int_status) + "\n")
        fh.write("\n")
        fh.write(json.dumps(row_out_of_range_status) + "\n")
        fh.write(json.dumps(row_good_status) + "\n")

    summary = summarize_file(str(path))

    assert summary["total_rows"] == 3
    assert summary["unique_urls"] == 3

    # only the valid int-in-range status increments a bucket
    assert summary["status_2xx"] == 1
    assert summary["status_3xx"] == 0
    assert summary["status_4xx"] == 0
    assert summary["status_5xx"] == 0


def test_summarize_file_counts_instagram_post_image_url_extra_image(tmp_path) -> None:
    """
    Covers instagram special-case:
    kind == 'instagram_post' and image_url truthy => total_images += 1 extra.
    """
    path = tmp_path / "instagram.ndjson"

    rows: List[Dict[str, Any]] = [
        {
            "kind": "instagram_post",
            "url": "https://instagram.com/p/abc/",
            "status": 200,
            "images": [],  # base images list contributes 0
            "image_url": "https://cdn.example.com/primary.jpg",  # triggers +1
            "external_links": [],
            "emails": [],
            "internal_links": [],
        },
        {
            "kind": "instagram_post",
            "url": "https://instagram.com/p/def/",
            "status": 200,
            "images": [],
            "image_url": "",  # falsy => should NOT trigger +1
            "external_links": [],
            "emails": [],
            "internal_links": [],
        },
    ]

    with open(path, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")

    summary = summarize_file(str(path))

    assert summary["total_rows"] == 2
    assert summary["unique_urls"] == 2
    assert summary["status_2xx"] == 2
    assert summary["total_images"] == 1  # only the first row adds the instagram extra


def test_summarize_file_scrape_rows_missing_fields_do_not_overcount(tmp_path) -> None:
    """
    Covers _process_scrape_row missing/empty source_url/value cases:
    - empty value => no increment for that kind
    - missing/empty source_url => does not contribute to unique_urls
    """
    path = tmp_path / "scrape_missing_fields.ndjson"

    rows: List[Dict[str, Any]] = [
        {"kind": "email", "value": "", "source_url": "https://example.com/"},  # unique_url adds, no email increment
        {"kind": "email", "value": "a@example.com"},                           # email increments, no unique_url add
        {"kind": "image", "value": "https://example.com/i.png", "source_url": ""},  # image increments, no unique_url add
        {"kind": "offsite_link", "value": None, "source_url": "https://example.com/"},  # unique_url adds, no external increment
    ]

    with open(path, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")

    summary = summarize_file(str(path))

    assert summary["total_rows"] == 4

    # unique_urls should only include the non-empty source_url rows (same url twice => 1)
    assert summary["unique_urls"] == 1

    assert summary["total_emails"] == 1
    assert summary["total_images"] == 1
    assert summary["total_external_links"] == 0

    # scrape rows do not update status buckets
    assert summary["status_2xx"] == 0
    assert summary["status_3xx"] == 0
    assert summary["status_4xx"] == 0
    assert summary["status_5xx"] == 0


def test_summarize_file_does_not_count_non_list_fields_for_list_totals(tmp_path) -> None:
    """
    Covers _add_external_links_count and _add_list_count non-list branches:
    external_links/emails/images that are not lists should not affect totals.
    """
    path = tmp_path / "non_list_fields.ndjson"

    rows: List[Dict[str, Any]] = [
        {
            "url": "https://example.com/",
            "status": 200,
            "external_links": "https://other.com/",  # not a list => should not count
            "emails": "a@example.com",               # not a list => should not count
            "images": "https://example.com/i.png",   # not a list => should not count
            "n_internal_links": 0,
            "links": [],
        }
    ]

    with open(path, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")

    summary = summarize_file(str(path))

    assert summary["total_rows"] == 1
    assert summary["unique_urls"] == 1
    assert summary["status_2xx"] == 1
    assert summary["total_external_links"] == 0
    assert summary["total_emails"] == 0
    assert summary["total_images"] == 0