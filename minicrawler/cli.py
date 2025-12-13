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
from .crawl import run, scrape_run
from .fetch import http_get
from .parse import parse_instagram_post
from .persist import open_writer, write_row, summarize_file

DEFAULT_MAX_PAGES = 50
DEFAULT_DELAY_SECONDS = 0.2
DEFAULT_TIMEOUT_SECONDS = 5
DEFAULT_RETRIES_COUNT = 1
DEFAULT_DEPTH = 1

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
        description="A tiny, polite web crawler and scraper.",
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
    crawl.add_argument(
        "--depth",
        type=int,
        default=DEFAULT_DEPTH,
        choices=[1, 2, 3],
        help="Maximum crawl depth (1, 2, or 3; default: 1)",
    )
    scrape = subparsers.add_parser(
        "scrape",
        help="Scrape emails, offsite links, or images up to a given depth.",
    )
    scrape.add_argument(
        "--seed",
        required=True,
        help="Seed URL, e.g. https://example.com/",
    )
    scrape.add_argument(
        "--out",
        default="scrape.ndjson",
        help="Output file (default: scrape.ndjson)",
    )
    scrape.add_argument(
        "--max-pages",
        type=int,
        default=DEFAULT_MAX_PAGES,
        help="Total pages including seed (default: 50)",
    )
    scrape.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_DELAY_SECONDS,
        help="Delay seconds between requests (default: 0.2)",
    )
    scrape.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="HTTP timeout seconds (default: 5)",
    )
    scrape.add_argument(
        "--retries",
        type=int,
        default=DEFAULT_RETRIES_COUNT,
        help="Retries on timeout/5xx (default: 1)",
    )
    scrape.add_argument(
        "--depth",
        type=int,
        default=DEFAULT_DEPTH,
        choices=[1, 2, 3],
        help="Maximum crawl depth (1, 2, or 3; default: 1)",
    )
    scrape.add_argument(
        "--target",
        required=True,
        choices=["emails", "offsite", "images"],
        help="Scrape target: emails, offsite, or images.",
    )
    scrape.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR)",
    )

    summary = subparsers.add_parser(
        "summary",
        help="Print a summary for an NDJSON file produced by this application.",
    )
    summary.add_argument(
        "--file",
        required=True,
        help="Path to NDJSON file to summarize.",
    )
    summary.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR)",
    )

    instagram = subparsers.add_parser(
        "instagram",
        help="Fetch primary image and metadata from an Instagram post URL.",
    )
    instagram.add_argument(
        "--url",
        required=True,
        help="Instagram post URL (https://www.instagram.com/p/.../).",
    )
    instagram.add_argument(
        "--out",
        default="instagram.ndjson",
        help="Output file (default: instagram.ndjson)",
    )
    instagram.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="HTTP timeout seconds (default: 5)",
    )
    instagram.add_argument(
        "--retries",
        type=int,
        default=DEFAULT_RETRIES_COUNT,
        help="Retries on timeout/5xx (default: 1)",
    )
    instagram.add_argument(
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

    status_code = 0

    if args.cmd == "crawl":
        logging.info(
            "Starting crawl seed=%s max_pages=%d depth=%d",
            args.seed,
            args.max_pages,
            args.depth,
        )
        count = 0
        with open_writer(args.out) as writer:
            for row in run(
                    seed=args.seed,
                    max_pages=args.max_pages,
                    delay=args.delay,
                    timeout=args.timeout,
                    retries=args.retries,
                    depth=args.depth,
            ):
                write_row(writer, row)
                count += 1
        logging.info("Done crawl. Wrote %d rows to %s", count, args.out)

    elif args.cmd == "scrape":
        logging.info(
            "Starting scrape seed=%s target=%s max_pages=%d depth=%d",
            args.seed,
            args.target,
            args.max_pages,
            args.depth,
        )
        count = 0
        with open_writer(args.out) as writer:
            for row in scrape_run(
                    seed=args.seed,
                    max_pages=args.max_pages,
                    delay=args.delay,
                    timeout=args.timeout,
                    retries=args.retries,
                    depth=args.depth,
                    target=args.target,
            ):
                write_row(writer, row)
                count += 1
        logging.info("Done scrape. Wrote %d rows to %s", count, args.out)


    elif args.cmd == "summary":
        summary_info = summarize_file(args.file)
        print("Summary for:", args.file)
        print("Total rows:", summary_info["total_rows"])
        print("Unique URLs:", summary_info["unique_urls"])
        print("2xx statuses:", summary_info["status_2xx"])
        print("3xx statuses:", summary_info["status_3xx"])
        print("4xx statuses:", summary_info["status_4xx"])
        print("5xx statuses:", summary_info["status_5xx"])
        print("Total internal links:", summary_info["total_internal_links"])
        print("Total external links:", summary_info["total_external_links"])
        print("Total emails:", summary_info["total_emails"])
        print("Total images:", summary_info["total_images"])

    elif args.cmd == "instagram":
        logging.info("Fetching Instagram post image from %s", args.url)
        status, final_url, html = http_get(
            args.url,
            timeout=args.timeout,
            retries=args.retries,
        )
        if status == 0 or html is None:
            logging.error("Failed to fetch Instagram post from %s", args.url)
        else:
            post_info = parse_instagram_post(html, final_url, status)
            with open_writer(args.out) as writer:
                write_row(writer, post_info)
            logging.info("Done instagram. Wrote 1 row to %s", args.out)



    return status_code


if __name__ == "__main__":
    main()