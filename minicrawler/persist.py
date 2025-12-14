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
        single dictionary as a JSON object
        on one line of the NDJSON output file.

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
    total_rows = 0
    unique_urls = set()
    status_2xx = 0
    status_3xx = 0
    status_4xx = 0
    status_5xx = 0
    total_internal_links = 0
    total_external_links = 0
    total_emails = 0
    total_images = 0

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if line:
                total_rows += 1
                row = json.loads(line)

                kind = row.get("kind")

                is_scrape_row = kind in ("email", "offsite_link", "image")
                if is_scrape_row:
                    source_url = row.get("source_url")
                    if source_url:
                        unique_urls.add(source_url)

                    value = row.get("value")
                    if value:
                        if kind == "email":
                            total_emails += 1
                        elif kind == "offsite_link":
                            total_external_links += 1
                        elif kind == "image":
                            total_images += 1
                else:
                    url = row.get("url")
                    if url:
                        unique_urls.add(url)

                    status = row.get("status")
                    if isinstance(status, int):
                        if STATUS_2XX_MIN <= status <= STATUS_2XX_MAX:
                            status_2xx += 1
                        elif STATUS_3XX_MIN <= status <= STATUS_3XX_MAX:
                            status_3xx += 1
                        elif STATUS_4XX_MIN <= status <= STATUS_4XX_MAX:
                            status_4xx += 1
                        elif STATUS_5XX_MIN <= status <= STATUS_5XX_MAX:
                            status_5xx += 1

                    internal_links = row.get("internal_links")
                    if isinstance(internal_links, list):
                        total_internal_links += len(internal_links)
                    else:
                        n_internal_links = row.get("n_internal_links")
                        if isinstance(n_internal_links, int):
                            total_internal_links += n_internal_links
                        else:
                            links = row.get("links")
                            if isinstance(links, list):
                                total_internal_links += len(links)

                    external = row.get("external_links")
                    if isinstance(external, list):
                        total_external_links += len(external)

                    emails = row.get("emails")
                    if isinstance(emails, list):
                        total_emails += len(emails)

                    images = row.get("images")
                    if isinstance(images, list):
                        total_images += len(images)

                    if kind == "instagram_post" and row.get("image_url"):
                        total_images += 1

    summary_info = {
        "total_rows": total_rows,
        "unique_urls": len(unique_urls),
        "status_2xx": status_2xx,
        "status_3xx": status_3xx,
        "status_4xx": status_4xx,
        "status_5xx": status_5xx,
        "total_internal_links": total_internal_links,
        "total_external_links": total_external_links,
        "total_emails": total_emails,
        "total_images": total_images,
    }
    return summary_info