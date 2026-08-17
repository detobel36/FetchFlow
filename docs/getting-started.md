# Getting Started

## Overview

FetchFlow executes web scraping workflows defined entirely in JSON. It requires minimal dependencies and can be run both programmatically in Python or directly via the Command Line Interface (CLI).

## Dependencies

To run FetchFlow, Python dependencies are required. All necessary dependencies are defined in the project's [`requirements.txt`](../requirements.txt) file:

- **httpx**: Fast, full-featured HTTP client.
- **lxml**: High-performance HTML parsing engine.
- **jsonschema**: JSON schema validator for checking configuration syntax.
- **cssselect**: CSS selector support for `lxml`.

### Installing Dependencies

Install all required dependencies using `pip` and `requirements.txt`:

```bash
pip install -r requirements.txt
```

---

## Running Scrapers via CLI (Command-Line Testing)

FetchFlow provides a CLI tool for testing JSON scraping configurations without writing Python code.

### Usage

```bash
python3 -m scraper_engine path/to/config.json
```

### Options

- `config`: Path to a JSON configuration file, or a raw JSON string.
- `-o`, `--output`: Path to write the JSON result (if omitted, output is printed to `stdout`).
- `--indent`: JSON output indentation level (default: `2`).

### CLI Example

Save the following JSON to `my_scraper.json`:

```json
{
  "name": "quick_start",
  "steps": [
    {
      "id": "heading",
      "request": {
        "url": "https://example.com"
      },
      "fields": {
        "title": {
          "selector": "h1",
          "type": "text",
          "transform": ["trim"]
        }
      }
    }
  ]
}
```

Run in command line:

```bash
python3 -m scraper_engine my_scraper.json
```

Output printed to console:

```json
[
  {
    "title": "Example Domain"
  }
]
```

To save output directly to a file:

```bash
python3 -m scraper_engine my_scraper.json -o results.json
```

---

## Using FetchFlow in Python Code

You can also import and execute scrapers within Python applications:

```python
from scraper_engine import Scraper

# Load from file path or JSON string/dict
scraper = Scraper("my_scraper.json")
results = scraper.run()

for item in results:
    print(item)
```
