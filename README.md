# 🕸️ MiniCrawler

A tiny, polite, single-file **depth-1 web crawler** written in Python.  
MiniCrawler crawls one website starting from a **seed URL**, visits that page and its **first-level internal links**, extracts basic information (title, links, and status), and writes the results to an **NDJSON file** (newline-delimited JSON).

---

## 🚀 Features
- Crawls one host only (no external links)
- Visits seed + direct internal links (depth-1)
- Respects a delay between requests
- Retries failed connections (configurable)
- Extracts:
  - Final URL
  - HTTP status code
  - Page title (if present)
  - Up to 5 internal links per page
- Saves output as **NDJSON**, one JSON object per line
- Simple, command-line interface

---

## 🧭 Usage

### 1️⃣ Basic command
```bash
python crawl.py crawl --seed https://example.com
```

This will:
- Start crawling `https://example.com`
- Visit the seed page and its first-level internal links
- Save results to `data.ndjson` in the current folder

---

### 2️⃣ Common options
| Option | Description | Default |
|---------|--------------|----------|
| `--seed` | The starting URL (required) | *none* |
| `--out` | Output file name | `data.ndjson` |
| `--max-pages` | Max total pages to crawl (including seed) | `50` |
| `--delay` | Delay between requests (seconds) | `0.2` |
| `--timeout` | HTTP timeout in seconds | `5` |
| `--retries` | Number of retries on timeout or 5xx | `1` |
| `--log-level` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `INFO` |

Example with all options:
```bash
python crawl.py crawl   --seed https://example.com   --out results.ndjson   --max-pages 20   --delay 0.3   --timeout 10   --retries 2   --log-level DEBUG
```

---

### 3️⃣ Output format (NDJSON)
Each line of the output file is a JSON object:
```json
{
  "url": "https://example.com/about",
  "status": 200,
  "title": "About Us",
  "n_internal_links": 4,
  "links": [
    "https://example.com/team",
    "https://example.com/contact"
  ]
}
```

---

## ⚙️ Requirements

**Python:** 3.10 or later  
**Libraries:** install via pip

```bash
pip install requests beautifulsoup4
```

Optionally, to match the testing environment:
```bash
pip install pytest responses
```

---

## 📄 How It Works
1. The crawler starts at the given `--seed` URL.
2. It fetches the HTML, extracts the page title and all internal links.
3. It visits each unique internal link (same host) up to the maximum page count.
4. Each result (page) is written to the NDJSON file as soon as it’s processed.
5. The crawler logs progress to the console.

---

## ⚠️ Ethical use
- Crawl **only public pages** you have permission to access.
- Respect server load — use reasonable delays and limits.
- Do **not** use this crawler for aggressive scraping or automated bulk downloads.

---

## 🧩 File summary
```
crawl.py       # Single-file implementation of the crawler
data.ndjson    # Default output (created after running)
```

---

## 🪪 License
This simple version is provided for educational and demonstration purposes.  
Use responsibly. No warranty expressed or implied.
