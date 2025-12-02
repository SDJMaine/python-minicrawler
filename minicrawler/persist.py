# ###########################################
# Name: Shayene Johnson
# Assignment: 8
# Purpose: Persistence module for the web crawler
#          Saves crawl results to a JSON file
# ###########################################

import json
from typing import Dict, Any, Iterator
from contextlib import contextmanager

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
        self.fh = fh

    # **********************
    # Printing Methods
    # **********************

    def write_row(self, row: Dict[str, Any]) -> None:
        """
        This function writes a single dictionary as a JSON object
        on one line of the NDJSON output file.

        :param row: Dict[str, Any]
        :return None : na
        :exception na : na
        :note na
        """
        self.fh.write(json.dumps(row, ensure_ascii=False) + "\n")

@contextmanager
def open_writer(path: str) -> Iterator[object]:
    """
    This function is a context manager that opens a file for NDJSON output
    and yields an NDJSON writer object with a write_row(row: dict) method.

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
    This function is a thin wrapper that writes a row using the provided writer,
    without requiring the caller to depend on the concrete writer class.

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