# 🕸️ MiniCrawler

A tiny, polite, **depth-limited (1–3)** web crawler and scraper written in Python.

MiniCrawler starts from a seed URL, crawls same-host pages only, extracts page metadata (title and links), and writes results to NDJSON. It also supports scraping emails, offsite links, and images, printing a summary of an NDJSON file, and a special Instagram extractor.
All commands are run from the **project root** (where `README.md` and `requirements.txt` live).

---

## 🚀 Features

### Crawler
- Same-host crawling only (does not crawl external domains)
- Depth-limited crawl (`--depth` = 1, 2, or 3)
- Respects a delay between requests
- Retries failed connections / on 5xx (configurable)
- Extracts per page:
    - URL (Final URL)
    - HTTP status code
    - Page title (if present)
    - Internal links (same host)
    - Count of internal links written
    - External links (offsite)
    - Crawl Level
- Saves output as **NDJSON**, one JSON object per line

### Scraper 
- Crawls **same-host pages only** (same crawl rules as `crawl`)
- Emits **deduplicated values across all visited pages**:
    - `scrape --target emails` → unique emails
    - `scrape --target offsite` → unique external (offsite) links
    - `scrape --target images` → unique image URLs
- Writes one scraped record per line as **NDJSON**

### Summary
`summary` prints aggregated counts for NDJSON produced by `crawl`, `scrape`, or `instagram`

### Instagram
- `instagram` fetches a post URL and extracts available metadata (title/description/image_url/username)
- Writes one record as **NDJSON**
---

## 🧠 Concepts Demonstrated

This project exercises a range of practical software-engineering concepts:

- **Command-line interface design** — `argparse` with subcommands (`crawl`, `scrape`, `summary`, `instagram`) and per-command options
- **HTTP networking** — fetching pages with configurable timeouts and retry on timeout/5xx
- **HTML parsing** — extracting titles, links, emails, and images with BeautifulSoup and regular expressions
- **Graph traversal** — queue-based, depth-limited crawl of same-host pages
- **Deduplication** — emitting unique values across all visited pages
- **File I/O** — streaming results to NDJSON (one JSON object per line) and summarizing existing files
- **Error handling & logging** — graceful failure handling with the `logging` module
- **Unit testing** — a pytest suite using `pytest-mock` to mock network calls

---

## 🧭 Usage

All commands below are run from the **project root** (where `README.md` and `requirements.txt` live)

### 1️⃣ Crawl
```bash
python -m minicrawler.cli crawl --seed https://example.com/ --depth 1
```

This will:
- Start crawling `https://example.com`
- Visit the seed page and crawl internal links up to --depth (default: 1), stopping at --max-pages.
- Save results to `data.ndjson` in the current folder

### 2️⃣ Scrape
```bash
python -m minicrawler.cli scrape --seed https://example.com/ --target emails --depth 1
python -m minicrawler.cli scrape --seed https://example.com/ --target offsite --depth 1
python -m minicrawler.cli scrape --seed https://example.com/ --target images --depth 1
```

This will:
- Start scraping `https://example.com`
- Emits unique emails, offsite links, or image URLs (depending on --target).
- Visit the seed page and scrape up to --depth (default: 1) (same host only)
- Save results to `scrape.ndjson` in the current folder

### 3️⃣ Summary (enhancement)
```bash
python -m minicrawler.cli summary --file data.ndjson
```

This will:
- Output to console a summary of `data.ndjson`
- Display counts for total rows, unique URLs, status buckets (2xx–5xx), and totals for internal links, external links, emails, and images

### 4️⃣ Instagram (special extractor)
```bash
python -m minicrawler.cli instagram --url https://www.instagram.com/p/POST_ID/ --out instagram.ndjson
```

This will:
- Attempt to extract `https://www.instagram.com/p/POST_ID/`
- Fetch and extract metadata from a public/available Instagram post
- Save results to `instagram.ndjson` in the current folder

---

## 📋Common options

### Crawl Options (`crawl`)
| Option        | Description                                        | Default       |
|---------------|----------------------------------------------------|---------------|
| `--seed`      | The starting URL (required)                        | *none*        |
| `--out`       | Output file name                                   | `data.ndjson` |
| `--max-pages` | Max total pages to crawl (including seed)          | `50`          |
| `--delay`     | Delay between requests (seconds)                   | `0.2`         |
| `--depth`     | Maximum crawl depth (1-3)                          | `1`           |
| `--timeout`   | HTTP timeout in seconds                            | `5`           |
| `--retries`   | Number of retries on timeout or 5xx                | `1`           |
| `--log-level` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `INFO`        |

Example crawl with common options:
```bash
python -m minicrawler.cli crawl --seed https://example.com/ --out data.ndjson --max-pages 20 --delay 0.3 --timeout 10 --retries 2 --depth 2 --log-level DEBUG
```

### Scrape options (`scrape`)
| Option | Description | Default |
|---|---|---|
| `--seed` | The starting URL (required) | *none* |
| `--target` | Scrape target (`emails`, `offsite`, `images`) | *none* |
| `--out` | Output file name | `scrape.ndjson` |
| `--max-pages` | Max total pages to crawl (including seed) | `50` |
| `--delay` | Delay between requests (seconds) | `0.2` |
| `--timeout` | HTTP timeout in seconds | `5` |
| `--retries` | Number of retries on timeout or 5xx | `1` |
| `--depth` | Maximum crawl depth (1–3) | `1` |
| `--log-level` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `INFO` |

Example scrape with common options:
```bash
python -m minicrawler.cli scrape --seed https://example.com/ --target offsite --out scrape.ndjson --max-pages 30 --delay 0.2 --timeout 8 --retries 2 --depth 3 --log-level INFO
```

### Summary options (`summary`)
| Option | Description | Default |
|---|---|---|
| `--file` | NDJSON file path to summarize (required) | *none* |
| `--log-level` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `INFO` |

Example summary with common options:
```bash
python -m minicrawler.cli summary --file data.ndjson --log-level INFO
```

### Instagram options (`instagram`)
| Option | Description | Default |
|---|---|---|
| `--url` | Instagram post URL (required) | *none* |
| `--out` | Output file name | `instagram.ndjson` |
| `--timeout` | HTTP timeout in seconds | `5` |
| `--retries` | Number of retries on timeout or 5xx | `1` |
| `--log-level` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `INFO` |

Example instagram extract with common options:
```bash
python -m minicrawler.cli instagram --url https://www.instagram.com/p/POST_ID/ --out instagram.ndjson --timeout 5 --retries 1 --log-level INFO
```

---

### 3️⃣ Output format (NDJSON)
Each line of the output file is a JSON object.

#### Crawl output
```json
{
  "url": "https://example.com/about",
  "status": 200,
  "title": "About Us",
  "n_internal_links": 2,
  "links": [
    "https://example.com/team",
    "https://example.com/contact"
  ],
  "level": 1,
  "external_links": [
    "https://other.com/"
  ]
}
```

#### Scrape output 
(emails)
```json
{
  "kind":"email",
  "value":"a@example.com",
  "source_url":"https://example.com/"}
```
(offsite)
```json
{
  "kind":"offsite_link",
  "value":"https://other.com/x",
  "source_url":"https://example.com/"}
```
(images)
```json
{
  "kind":"image",
  "value":"https://example.com/img.png",
  "source_url":"https://example.com/"}
```

#### Instagram Output
```json
{
  "kind": "instagram_post",
  "url": "https://www.instagram.com/p/POST_ID/",
  "status": 200,
  "title": "Instagram",
  "description": "…",
  "image_url": "https://…",
  "username": "handle_name"
}
```

---

## ⚙️ Requirements

**Python:** 3.10 or later (build verified on Python 3.12.8)  
**Libraries:** install via pip
- requests
- beautifulsoup4

Optionally, to match the testing environment:
- pytest
- pytest-mock

Other dependencies are listed in `requirements.txt`.
```bash
pip install -r requirements.txt
```
---
## 🧪 Running Tests

Tests live in the tests package and use pytest. 
To run tests, from the project root:

```bash
pytest 
```
or individual files:
```bash
pytest tests/test_crawl.py
pytest tests/test_fetch.py
pytest tests/test_parse.py
pytest tests/test_cli.py
pytest tests/test_persist.py
```

or Run the full test script:
```bash
./run_tests.sh
```

The suite currently contains **79 tests, all passing** (verified with pytest on Python 3.12.8).

---

## 📊 Example Output

Running `summary` against an NDJSON file produced by `crawl` prints aggregated counts to the console:

```text
$ python -m minicrawler.cli summary --file data.ndjson
Summary for: data.ndjson
Total rows: 20
Unique URLs: 20
2xx statuses: 20
3xx statuses: 0
4xx statuses: 0
5xx statuses: 0
Total internal links: 95
Total external links: 153
Total emails: 21
Total images: 94
```

See the [Output format (NDJSON)](#3️⃣-output-format-ndjson) section above for the per-record structure written by each command.

---

## 📄 How It Works

### `crawl`
1. Starts at the given `--seed` URL.
2. Crawls **same-host pages only** up to the chosen `--depth` (1–3), stopping at `--max-pages`.
3. Fetches each page and extracts the title, internal links, and offsite (external) links.
4. Writes one NDJSON row per page as it is processed (with up to 5 internal links in the output row).
5. Logs progress to the console.

---

### `scrape`
1. Starts at the given `--seed` URL.
2. Crawls **same-host pages only** up to the chosen `--depth` (1–3), stopping at `--max-pages`.
3. Extracts only the selected `--target` (`emails`, `offsite`, or `images`) from visited pages.
4. Deduplicates values across all pages (each email/link/image is emitted once).
5. Writes one NDJSON row per scraped value and logs progress.

---

### `summary`
1. Reads an NDJSON file produced by `crawl`, `scrape`, or `instagram`.
2. Counts totals like rows, unique URLs, status buckets, and extracted items (links/emails/images).
3. Prints the summary to the console.

---

### `instagram`
1. Fetches the given Instagram post `--url`.
2. Extracts available metadata (title, description, image URL, username).
3. Writes one NDJSON row (or logs an error if the fetch fails). 

- Tip: Use the browser url link to the post (the normal https://www.instagram.com/p/<POST_ID>/ link) and avoid “share”/tracking parameters or shortened links.
- Note: May fail if Instagram blocks automated requests or the post is not publicly accessible.
---

## ⚠️ Ethical use
- Crawl or Scrape **only public pages** you have permission to access.
- Respect server load — use reasonable delays and limits.
- Do **not** use this crawler for aggressive scraping or automated bulk downloads.

---

## 🧩 File summary and structure
```
minicrawler/     # Main package
  __init__.py     # Package initializer
  cli.py          # Command-line interface
  crawl.py        # Crawler logic
  fetch.py        # HTTP fetching with retries and timeouts
  parse.py        # HTML parsing and link extraction
  persist.py      # NDJSON writing + file summarization
tests/           # Unit tests
  __init__.py      # Test package initializer
  test_cli.py       # Tests for cli.py
  test_crawl.py     # Tests for crawl.py
  test_fetch.py     # Tests for fetch.py
  test_parse.py     # Tests for parse.py
  test_persist.py   # Tests for persist.py
requirements.txt  # Required libraries
README.md         # This file
run_tests.sh      # Script to run all tests
```

---

## 🎓 Academic Context

> This project was originally completed as an academic assignment and has been repackaged for portfolio review. The original implementation and behavior have been preserved.

---

## ⚠️ Limitations

- Crawls a **single host only** — it does not follow links to external domains.
- Crawl depth is limited to **1–3 levels**.
- Fetches and parses **static HTML only** — JavaScript-rendered content is not executed.
- The Instagram extractor depends on publicly available metadata and **may fail** if Instagram blocks automated requests or the post is private.
- The visited set and deduplication are kept **in memory**, so very large crawls are bounded by available memory and the `--max-pages` limit.

---

## 🚧 Possible Future Improvements

These are potential future directions, **not** currently implemented features:

- Honoring `robots.txt` and crawl-delay directives.
- Concurrent or asynchronous fetching for faster crawls.
- Resumable crawls with persisted state.
- A configuration file as an alternative to command-line flags.
- Packaging as an installable console script (e.g. a `pyproject.toml` entry point).

---

## 📌 Status

Academic project — **complete** and repackaged for portfolio review.

---

## 🪪 License
See [LICENSE-NOTICE.md](LICENSE-NOTICE.md): **no license has been selected**, and the code is currently provided for portfolio review.  
Use responsibly. No warranty expressed or implied.
