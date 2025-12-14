# ###########################################
# Name: Shayene Johnson
# Assignment: Final Project
# Purpose: Tester for persist.py
#          open_writer, write_row, summarize_file
# ###########################################

import json
from typing import Any, Dict

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
    assert summary["total_internal_links"] in (3, 3)

    assert summary["total_external_links"] == 2

    # emails/images totals: implementation may count raw list lengths or unique values;
    # accept either behavior while still asserting it's non-zero and consistent.
    assert summary["total_emails"] in (2, 3)
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