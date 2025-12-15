# ###########################################
# Name: Shayene Johnson
# Assignment: Final Project
# Purpose: Persistence module for the web crawler
#          Saves crawl results to a JSON file
#          and provides NDJSON summary
# ###########################################

import json
from typing import Dict, Any, Iterator
from contextlib import contextmanager

INITIAL_COUNT = 0
INCREMENT_BY_ONE = 1

STATUS_2XX_MIN = 200
STATUS_2XX_MAX = 299
STATUS_3XX_MIN = 300
STATUS_3XX_MAX = 399
STATUS_4XX_MIN = 400
STATUS_4XX_MAX = 499
STATUS_5XX_MIN = 500
STATUS_5XX_MAX = 599

class _NDJSONWriter:

    # **********************
    # Constructors/Destructor
    # **********************

    def __init__(self, fh) -> None:
        """
        Initializes the NDJSON writer
        with an
        already-open file handle for output.

        :param fh: object
        :return None : na
        :exception na : na
        :note na
        """
        self._fh = fh

    # **********************
    # Printing Methods
    # **********************

    def write_row(self, row: Dict[str, Any]) -> None:
        """
        This function writes a
        single dictionary as a
        JSON object
        on one line of the
        NDJSON output file.

        :param row: Dict[str, Any]
        :return None : na
        :exception na : na
        :note na
        """
        self._fh.write(json.dumps(row, ensure_ascii=False) + "\n")

@contextmanager
def open_writer(path: str) -> Iterator[object]:
    """
    This function is a context manager
    that opens a file for NDJSON output
    and yields an NDJSON writer object
    with a write_row(row: dict) method.

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
    This function is a thin wrapper that
    writes a row using the provided writer,
    without requiring the caller to depend
    on the concrete writer class.

    :param object writer:
    :param Dict[str, Any] row:
    :return None : na
    :exception na : na
    :note na
    """
    if hasattr(writer, "write_row"):
        writer.write_row(row)
    else:
        raise TypeError("Writer does not support write_row(row).")

def summarize_file(path: str) -> Dict[str, int]:
    """
    This function reads an
    NDJSON output file produced by
    crawl and scrape modes
    and returns a summary of:
    total rows, unique source URLs,
    status buckets, and aggregate
    counts for links, emails, and images.

    It supports both crawl rows
    (url/status/title/links)
    and scrape rows
    (kind/value/source_url).

    :param str path:
    :return Dict[str, int] : summary_info
    :exception na : na
    :note na
    """
    state = _init_summary_state()

    with open(path, "r", encoding="utf-8") as f:
        line = f.readline()

        while line:
            cleaned_line = line.strip()

            if cleaned_line:
                _process_ndjson_line(cleaned_line, state)

            line = f.readline()

    unique_urls = state["unique_urls"]

    summary_info = {
        "total_rows": state["total_rows"],
        "unique_urls": len(unique_urls),
        "status_2xx": state["status_2xx"],
        "status_3xx": state["status_3xx"],
        "status_4xx": state["status_4xx"],
        "status_5xx": state["status_5xx"],
        "total_internal_links": state["total_internal_links"],
        "total_external_links": state["total_external_links"],
        "total_emails": state["total_emails"],
        "total_images": state["total_images"],
    }
    return summary_info

def _process_scrape_row(row: Dict[str, Any], state: Dict[str, object]) -> None:
    """
    This function updates summary
    totals using a scrape row.
    It counts unique source URLs
    and increments totals based
    on the scrape kind.

    :param Dict[str, Any] row:
    :param Dict[str, object] state:
    :return None : na
    :exception na : na
    :note na
    """
    kind = row.get("kind")
    source_url = row.get("source_url")
    value = row.get("value")

    if source_url:
        unique_urls = state["unique_urls"]
        unique_urls.add(source_url)

    if value and kind:
        if kind == "email":
            state["total_emails"] = state["total_emails"] + INCREMENT_BY_ONE
        elif kind == "offsite_link":
            state["total_external_links"] = state["total_external_links"] + INCREMENT_BY_ONE
        elif kind == "image":
            state["total_images"] = state["total_images"] + INCREMENT_BY_ONE

    return


def _process_ndjson_line(line: str, state: Dict[str, object]) -> None:
    """
    This function parses one
    NDJSON line and updates
    the summary state using
    either scrape-row logic
    or crawl-row logic.

    :param str line:
    :param Dict[str, object] state:
    :return None : na
    :exception na : na
    :note na
    """
    state["total_rows"] = state["total_rows"] + INCREMENT_BY_ONE

    row = json.loads(line)
    kind = row.get("kind")

    is_scrape_row = kind in ("email", "offsite_link", "image")
    if is_scrape_row:
        _process_scrape_row(row, state)
    else:
        _process_crawl_row(row, state)

    return


def _process_crawl_row(row: Dict[str, Any], state: Dict[str, object]) -> None:
    """
    This function updates summary
    totals using a crawl row.
    It tracks unique URLs, buckets
    HTTP status codes, and
    aggregates totals for
    internal links, external links,
    emails, and images.

    :param Dict[str, Any] row:
    :param Dict[str, object] state:
    :return None : na
    :exception na : na
    :note na
    """
    url = row.get("url")
    if url:
        unique_urls = state["unique_urls"]
        unique_urls.add(url)

    status = row.get("status")
    _update_status_bucket(status, state)

    _add_internal_links_count(row, state)
    _add_external_links_count(row, state)
    _add_list_count(row, "emails", "total_emails", state)
    _add_list_count(row, "images", "total_images", state)

    kind = row.get("kind")
    image_url = row.get("image_url")
    has_instagram_image = kind == "instagram_post" and bool(image_url)
    if has_instagram_image:
        state["total_images"] = state["total_images"] + INCREMENT_BY_ONE

    return

# ********************************************
#            Helper functions
# ********************************************

def _init_summary_state() -> Dict[str, object]:
    """
    This function initializes
    and returns the mutable
    summary state used while
    scanning an NDJSON file.

    :return Dict[str, object] : state
    :exception na : na
    :note na
    """
    state: Dict[str, object] = {
        "total_rows": INITIAL_COUNT,
        "unique_urls": set(),
        "status_2xx": INITIAL_COUNT,
        "status_3xx": INITIAL_COUNT,
        "status_4xx": INITIAL_COUNT,
        "status_5xx": INITIAL_COUNT,
        "total_internal_links": INITIAL_COUNT,
        "total_external_links": INITIAL_COUNT,
        "total_emails": INITIAL_COUNT,
        "total_images": INITIAL_COUNT,
    }
    return state

def _update_status_bucket(status: Any, state: Dict[str, object]) -> None:
    """
    This function increments
    exactly one status bucket
    when the status is a valid integer.

    :param Any status:
    :param Dict[str, object] state:
    :return None : na
    :exception na : na
    :note na
    """
    if isinstance(status, int):
        if STATUS_2XX_MIN <= status <= STATUS_2XX_MAX:
            state["status_2xx"] = state["status_2xx"] + INCREMENT_BY_ONE
        elif STATUS_3XX_MIN <= status <= STATUS_3XX_MAX:
            state["status_3xx"] = state["status_3xx"] + INCREMENT_BY_ONE
        elif STATUS_4XX_MIN <= status <= STATUS_4XX_MAX:
            state["status_4xx"] = state["status_4xx"] + INCREMENT_BY_ONE
        elif STATUS_5XX_MIN <= status <= STATUS_5XX_MAX:
            state["status_5xx"] = state["status_5xx"] + INCREMENT_BY_ONE

    return


def _add_internal_links_count(row: Dict[str, Any], state: Dict[str, object]) -> None:
    """
    This function adds to
    total_internal_links using any of:
    - internal_links (list)
    - n_internal_links (int)
    - links (list) as a fallback

    :param Dict[str, Any] row:
    :param Dict[str, object] state:
    :return None : na
    :exception na : na
    :note na
    """
    internal_links = row.get("internal_links")
    if isinstance(internal_links, list):
        state["total_internal_links"] = state["total_internal_links"] + len(internal_links)
    else:
        n_internal_links = row.get("n_internal_links")
        if isinstance(n_internal_links, int):
            state["total_internal_links"] = state["total_internal_links"] + n_internal_links
        else:
            links = row.get("links")
            if isinstance(links, list):
                state["total_internal_links"] = state["total_internal_links"] + len(links)

    return


def _add_external_links_count(row: Dict[str, Any], state: Dict[str, object]) -> None:
    """
    This function adds to
    total_external_links
    using external_links (list),
    when present.

    :param Dict[str, Any] row:
    :param Dict[str, object] state:
    :return None : na
    :exception na : na
    :note na
    """
    external_links = row.get("external_links")
    if isinstance(external_links, list):
        state["total_external_links"] = state["total_external_links"] + len(external_links)

    return

def _add_list_count(
        row: Dict[str, Any],
        field_name: str,
        total_key: str,
        state: Dict[str, object],
) -> None:
    """
    This function adds
    len(row[field_name])
    into state[total_key]
    when row[field_name] is a list.

    :param Dict[str, Any] row:
    :param str field_name:
    :param str total_key:
    :param Dict[str, object] state:
    :return None : na
    :exception na : na
    :note na
    """
    values = row.get(field_name)
    if isinstance(values, list):
        state[total_key] = state[total_key] + len(values)

    return