# Getting Started

## Overview

Jexflow executes web scraping workflows defined entirely in JSON. It requires minimal dependencies and can be run programmatically in Python or via the Command Line Interface (CLI).

## Dependencies

Using a Python virtual environment is recommended for local development.
Python dependencies are listed in [`requirements.txt`](../requirements.txt):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

---

## Running Scrapers via CLI

Jexflow includes a CLI for executing and testing JSON scrapers without writing Python code.

### Usage & Example

You can run an example config from the repository:

```bash
python -m scraper_engine examples/getting_started.json
```

**Options:**
- `config`: Path to a JSON configuration file, or a raw JSON string.
- `-o`, `--output`: Path to write JSON results (if omitted, results print to `stdout`).
- `--indent`: JSON output indentation level (default: `2`).

Save results directly to a file:

```bash
python -m scraper_engine examples/getting_started.json -o results.json
```

---

## Using Jexflow in Python

Execute scrapers inside Python applications:

```python
from scraper_engine import Scraper

scraper = Scraper("examples/getting_started.json")
results = scraper.run()

for item in results:
    print(item)
```

---

**Next:** Proceed to [Configuration Structure](configuration-structure.md) to learn how to structure JSON configurations.
