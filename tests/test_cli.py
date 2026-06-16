# ###########################################
# Name: Shayene Johnson
# Purpose: Tester for cli.py
#          parser + main dispatch
#          for crawl/scrape/summary/instagram
# ###########################################

import contextlib
import io
import pytest

from minicrawler.cli import _build_parser, main

def test_build_parser_requires_subcommand() -> None:
    """
    This function tests that
    the CLI requires a subcommand.

    :param na: na
    :return None: na
    :exception na: na
    :note argparse raises SystemExit on parse failure
    """
    parser = _build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_crawl_requires_seed() -> None:
    """
    This function tests that
    the crawl subcommand requires --seed.

    :param na: na
    :return None: na
    :exception na: na
    :note argparse raises SystemExit on missing required args
    """
    parser = _build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["crawl"])


def test_scrape_requires_target_and_seed() -> None:
    """
    This function tests that
    the scrape subcommand requires --seed and --target.

    :param na: na
    :return None: na
    :exception na: na
    :note argparse raises SystemExit on missing required args
    """
    parser = _build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["scrape", "--seed", "https://example.com/"])
    with pytest.raises(SystemExit):
        parser.parse_args(["scrape", "--target", "emails"])


def test_main_crawl_writes_rows_and_passes_args(mocker) -> None:
    """
    This function tests that
    main() dispatches to crawl.run,
    passes CLI args through, and writes
    each yielded row using persist.write_row.

    :param mocker: pytest mocker fixture
    :return None: na
    :exception na: na
    :note mocks run/open_writer/write_row to avoid IO and network
    """
    fake_rows = [
        {"url": "https://example.com/", "status": 200},
        {"url": "https://example.com/about", "status": 200},
    ]

    mocked_run = mocker.patch(
        "minicrawler.cli.run",
        return_value=iter(fake_rows),
    )

    writer_obj = mocker.Mock()

    @contextlib.contextmanager
    def fake_open_writer(_path):
        yield writer_obj

    mocked_open_writer = mocker.patch(
        "minicrawler.cli.open_writer",
        side_effect=fake_open_writer,
    )
    mocked_write_row = mocker.patch("minicrawler.cli.write_row")

    argv = [
        "crawl",
        "--seed",
        "https://example.com/",
        "--out",
        "out.ndjson",
        "--max-pages",
        "7",
        "--delay",
        "0.3",
        "--timeout",
        "9",
        "--retries",
        "2",
        "--depth",
        "2",
        "--log-level",
        "DEBUG",
    ]

    status = main(argv)

    assert status == 0

    mocked_run.assert_called_once_with(
        seed="https://example.com/",
        max_pages=7,
        delay=0.3,
        timeout=9,
        retries=2,
        depth=2,
    )
    mocked_open_writer.assert_called_once_with("out.ndjson")
    assert mocked_write_row.call_count == 2
    mocked_write_row.assert_any_call(writer_obj, fake_rows[0])
    mocked_write_row.assert_any_call(writer_obj, fake_rows[1])


def test_main_scrape_writes_rows_and_passes_args(mocker) -> None:
    """
    This function tests that
    main() dispatches to crawl.scrape_run,
    passes CLI args through, and writes
    each yielded row.

    :param mocker: pytest mocker fixture
    :return None: na
    :exception na: na
    :note mocks scrape_run/open_writer/write_row
    """
    fake_rows = [
        {"kind": "email", "value": "a@example.com", "source_url": "https://example.com/"},
        {"kind": "email", "value": "b@example.com", "source_url": "https://example.com/"},
    ]

    mocked_scrape_run = mocker.patch(
        "minicrawler.cli.scrape_run",
        return_value=iter(fake_rows),
    )

    writer_obj = mocker.Mock()

    @contextlib.contextmanager
    def fake_open_writer(_path):
        yield writer_obj

    mocked_open_writer = mocker.patch(
        "minicrawler.cli.open_writer",
        side_effect=fake_open_writer,
    )
    mocked_write_row = mocker.patch("minicrawler.cli.write_row")

    argv = [
        "scrape",
        "--seed",
        "https://example.com/",
        "--target",
        "emails",
        "--out",
        "scrape.ndjson",
        "--max-pages",
        "5",
        "--delay",
        "0.1",
        "--timeout",
        "4",
        "--retries",
        "1",
        "--depth",
        "3",
    ]

    status = main(argv)

    assert status == 0

    mocked_scrape_run.assert_called_once_with(
        seed="https://example.com/",
        max_pages=5,
        delay=0.1,
        timeout=4,
        retries=1,
        depth=3,
        target="emails",
    )
    mocked_open_writer.assert_called_once_with("scrape.ndjson")
    assert mocked_write_row.call_count == 2


def test_main_summary_prints_expected_lines(mocker) -> None:
    """
    This function tests that
    main() dispatches to persist.summarize_file
    and prints the expected summary lines.

    :param mocker: pytest mocker fixture
    :return None: na
    :exception na: na
    :note captures stdout
    """
    summary = {
        "total_rows": 3,
        "unique_urls": 2,
        "status_2xx": 2,
        "status_3xx": 0,
        "status_4xx": 1,
        "status_5xx": 0,
        "total_internal_links": 10,
        "total_external_links": 4,
        "total_emails": 1,
        "total_images": 2,
    }

    mocker.patch("minicrawler.cli.summarize_file", return_value=summary)

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        status = main(["summary", "--file", "data.ndjson"])

    assert status == 0
    out = buf.getvalue()
    assert "Summary for:" in out
    assert "data.ndjson" in out
    assert "Total rows: 3" in out
    assert "Unique URLs: 2" in out
    assert "4xx statuses: 1" in out
    assert "Total images: 2" in out


def test_main_instagram_fetch_failure_does_not_write(mocker) -> None:
    """
    This function tests that
    when instagram fetch fails (status 0 or html None),
    main() does not write output.

    :param mocker: pytest mocker fixture
    :return None: na
    :exception na: na
    """
    mocker.patch("minicrawler.cli.http_get", return_value=(0, "https://x", None))
    mocked_open_writer = mocker.patch("minicrawler.cli.open_writer")
    mocked_write_row = mocker.patch("minicrawler.cli.write_row")
    mocker.patch("minicrawler.cli.parse_instagram_post")

    status = main(["instagram", "--url", "https://www.instagram.com/p/test/"])

    assert status == 0
    mocked_open_writer.assert_not_called()
    mocked_write_row.assert_not_called()


def test_main_instagram_success_writes_one_row(mocker) -> None:
    """
    This function tests that
    when instagram fetch succeeds,
    main() parses the post and writes exactly one row.

    :param mocker: pytest mocker fixture
    :return None: na
    :exception na: na
    """
    html = "<html><head><title>Instagram</title></head><body></body></html>"
    mocker.patch(
        "minicrawler.cli.http_get",
        return_value=(200, "https://www.instagram.com/p/test/", html),
    )

    post_info = {"kind": "instagram_post", "url": "x", "status": 200}
    mocked_parse = mocker.patch(
        "minicrawler.cli.parse_instagram_post",
        return_value=post_info,
    )

    writer_obj = mocker.Mock()

    @contextlib.contextmanager
    def fake_open_writer(_path):
        yield writer_obj

    mocked_open_writer = mocker.patch(
        "minicrawler.cli.open_writer",
        side_effect=fake_open_writer,
    )
    mocked_write_row = mocker.patch("minicrawler.cli.write_row")

    status = main(["instagram", "--url", "https://www.instagram.com/p/test/", "--out", "insta.ndjson"])

    assert status == 0
    mocked_parse.assert_called_once()
    mocked_open_writer.assert_called_once_with("insta.ndjson")
    mocked_write_row.assert_called_once_with(writer_obj, post_info)


def test_summary_requires_file() -> None:
    """
    This function tests that
    the summary subcommand requires --file.

    :param na: na
    :return None: na
    :exception na: na
    :note argparse raises SystemExit on missing required args
    """
    parser = _build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["summary"])


def test_instagram_requires_url() -> None:
    """
    This function tests that
    the instagram subcommand requires --url.

    :param na: na
    :return None: na
    :exception na: na
    :note argparse raises SystemExit on missing required args
    """
    parser = _build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["instagram"])


def test_main_summary_requires_file_and_exits(mocker) -> None:
    """
    This function tests that
    main() exits when summary is missing --file.

    :param mocker: pytest mocker fixture
    :return None: na
    :exception na: na
    :note argparse triggers SystemExit before summarize_file is called
    """
    mocker.patch("minicrawler.cli.summarize_file")
    with pytest.raises(SystemExit):
        main(["summary"])


def test_main_instagram_requires_url_and_exits(mocker) -> None:
    """
    This function tests that
    main() exits when instagram is missing --url.

    :param mocker: pytest mocker fixture
    :return None: na
    :exception na: na
    :note argparse triggers SystemExit before http_get is called
    """
    mocker.patch("minicrawler.cli.http_get")
    with pytest.raises(SystemExit):
        main(["instagram"])


def test_build_parser_rejects_invalid_scrape_target() -> None:
    """
    This function tests that
    scrape --target rejects invalid values.

    :param na: na
    :return None: na
    :exception na: na
    :note argparse raises SystemExit for invalid choice
    """
    parser = _build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["scrape", "--seed", "https://example.com/", "--target", "bad"])


def test_build_parser_rejects_invalid_depth_choice() -> None:
    """
    This function tests that
    crawl/scrape depth choices reject invalid values.

    :param na: na
    :return None: na
    :exception na: na
    :note argparse raises SystemExit for invalid choice
    """
    parser = _build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["crawl", "--seed", "https://example.com/", "--depth", "99"])
    with pytest.raises(SystemExit):
        parser.parse_args(["scrape", "--seed", "https://example.com/", "--target", "emails", "--depth", "0"])
