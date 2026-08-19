# Jexflow

[![CC BY-NC-SA 4.0][cc-by-nc-sa-image]][cc-by-nc-sa]

[cc-by-nc-sa]: http://creativecommons.org/licenses/by-nc-sa/4.0/
[cc-by-nc-sa-image]: https://licensebuttons.net/l/by-nc-sa/4.0/88x31.png
[cc-by-nc-sa-shield]: https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg

A lightweight, configuration-driven web scraping engine in Python designed for low resource usage, fast parsing, and execution in embedded environments (such as Kodi addons on Raspberry Pi).

## Features

- **JSON Configuration-Driven**: Define scraping workflows, URL templates, selectors, and transformations purely in JSON.
- **Low Resource Usage**: Minimal dependencies (`httpx`, `lxml`, `jsonschema`, `cssselect`). No browser automation required by default.
- **Unified Extractors**: Supports CSS selectors and XPath for HTML parsing, as well as JSONPath for REST JSON APIs. Extensible for future document formats.
- **Flexible Transformations**: Composable transformations (`trim`, `lower`, `upper`, `replace`, `split`, `regex`).
- **Sequential Workflows & Loops**: Pass extracted variables between steps and iterate using `for_each`.

## Documentation & Wiki

Full feature documentation, JSON schema guides, and examples are available in the [Documentation Wiki](docs/INDEX.md):

- [Getting Started](docs/getting-started.md)
- [Configuration Structure](docs/configuration-structure.md)
- [HTTP Requests](docs/requests.md)
- [Extraction & Selectors](docs/extraction-and-selectors.md)
- [Transformations](docs/transformations.md)
- [Workflows & Loops](docs/workflows-and-loops.md)

## Quick Start

### Installation

Using a Python virtual environment is recommended. Requirements for using the
library are listed in [`requirements.txt`](requirements.txt). Install them using:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### Running from CLI (Command-Line Testing)

You can launch and test scrapers directly from the command line:

```bash
python -m scraper_engine examples/ecommerce_scraper.json
```

Output results to a file:

```bash
python -m scraper_engine examples/ecommerce_scraper.json -o results.json
```

Or execute a REST JSON API scraper workflow:

```bash
python -m scraper_engine examples/rest_api_scraper.json
```

### Usage in Python

```python
from scraper_engine import Scraper

# Load from JSON file or dictionary
scraper = Scraper("examples/ecommerce_scraper.json")
results = scraper.run()

for item in results:
    print(item)
```

## Running Tests

To run all unit and integration tests:

```bash
PYTHONPATH=. .venv/bin/python -m pytest
```

## Code of Conduct

Before contributing, review the [Code of Conduct](CODE_OF_CONDUCT.md) for the
required linting and testing checks.
