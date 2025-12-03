# ###########################################
# Name: Shayene Johnson
# Assignment: 8
# Purpose: CLI module for the web crawler
#          Provides command-line interface
#          for running the crawler
# ###########################################

import sys
import argparse
import logging

from typing import Optional, List
from .crawl import run
from .persist import open_writer, write_row

DEFAULT_MAX_PAGES = 50
DEFAULT_DELAY_SECONDS = 0.2
DEFAULT_TIMEOUT_SECONDS = 5
DEFAULT_RETRIES_COUNT = 1

def _build_parser() -> argparse.ArgumentParser:
    """
    This function builds and
    returns the argument parser
    for the tiny, polite, depth-1
    web crawler command line application.

    :param na: na
    :return argparse.ArgumentParser : parser
    :exception na : na
    :note na
    """
    parser = argparse.ArgumentParser(
        prog="crawler",
        description="A tiny, polite, depth-1 web crawler for a single host.",
    )
    subparsers = parser.add_subparsers(dest="cmd", required=True)

    crawl = subparsers.add_parser(
        "crawl",
        help="Crawl a seed page and its first-level internal links.",
    )
    crawl.add_argument(
        "--seed",
        required=True,
        help="Seed URL, e.g. https://example.com/",
    )
    crawl.add_argument(
        "--out",
        default="data.ndjson",
        help="Output file (default: data.ndjson)",
    )
    crawl.add_argument(
        "--max-pages",
        type=int,
        default=DEFAULT_MAX_PAGES,
        help="Total pages including seed (default: 50)",
    )
    crawl.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_DELAY_SECONDS,
        help="Delay seconds between requests (default: 0.2)",
    )
    crawl.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="HTTP timeout seconds (default: 5)",
    )
    crawl.add_argument(
        "--retries",
        type=int,
        default=DEFAULT_RETRIES_COUNT,
        help="Retries on timeout/5xx (default: 1)",
    )
    crawl.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR)",
    )
    return parser

def main(argv: Optional[List[str]] = None) -> int:
    """
    This function is the application driver
    for a tiny, polite, depth-1
    web crawler program that writes NDJSON output.

    :param argv: Optional[List[str]]
    :return int : status_code
    :exception na : na
    :note na
    """
    if argv is None:
        argv = sys.argv[1:]

    parser = _build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        format="%(levelname)s %(message)s",
        level=getattr(logging, args.log_level.upper(), logging.INFO),
    )

    logging.info("Starting crawl seed=%s max_pages=%d", args.seed, args.max_pages)
    count = 0

    with open_writer(args.out) as writer:
        for row in run(
                seed=args.seed,
                max_pages=args.max_pages,
                delay=args.delay,
                timeout=args.timeout,
                retries=args.retries,
        ):
            write_row(writer, row)
            count += 1

    logging.info("Done. Wrote %d rows to %s", count, args.out)
    return 0


if __name__ == "__main__":
    main()