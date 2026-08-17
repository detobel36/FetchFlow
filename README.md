# Config-Driven Python Web Scraping Engine

A lightweight, configuration-driven web scraping engine in Python designed for low resource usage, fast parsing, and execution in embedded environments (such as Kodi addons on Raspberry Pi).

## Features

- **JSON Configuration-Driven**: Define scraping workflows, URL templates, selectors, and transformations purely in JSON.
- **Low Resource Usage**: Minimal dependencies (`httpx`, `lxml`, `jsonschema`). No browser automation required by default.
- **Unified Extractors**: Supports CSS selectors and XPath for HTML parsing.
- **Flexible Transformations**: Composable transformations (`trim`, `lower`, `upper`, `replace`, `split`, `regex`).
- **Sequential Workflows & Loops**: Pass extracted variables between steps and iterate using `for_each`.

## Quick Start

### Installation

```bash
pip install httpx lxml jsonschema cssselect
```

### Usage

```python
from scraper_engine import Scraper

# Load from JSON file or dictionary
scraper = Scraper("examples/ecommerce_scraper.json")
results = scraper.run()

for item in results:
    print(item)
```

## Creating a Scraper Config (JSON)

Scrapers are defined by a JSON object containing global `variables` and an array of `steps`.

### Simple Example

```json
{
  "name": "example_scraper",
  "variables": {
    "base_url": "https://example.com"
  },
  "steps": [
    {
      "id": "products",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/products"
      },
      "extract": {
        "selector": ".product-item",
        "selector_type": "css"
      },
      "fields": {
        "id": {
          "selector": ".id",
          "selector_type": "css",
          "type": "text",
          "transform": ["trim"]
        },
        "name": {
          "selector": ".name",
          "selector_type": "css",
          "type": "text",
          "transform": ["trim"]
        }
      }
    },
    {
      "id": "details",
      "for_each": {
        "from": "products",
        "field": "id"
      },
      "request": {
        "method": "GET",
        "url": "{{base_url}}/details?id={{id}}"
      },
      "extract": {
        "selector": ".details-card",
        "selector_type": "css"
      },
      "fields": {
        "price": {
          "selector": "//span[@class='price']",
          "selector_type": "xpath",
          "type": "text",
          "transform": [
            "trim",
            { "regex": "([0-9,.]+)" }
          ]
        }
      }
    }
  ]
}
```

### Available Selectors
- `css`: Standard CSS selectors (e.g. `.class-name`, `h1 > a`).
- `xpath`: XPath expressions (e.g. `//div[@class='title']`, `//a/@href`).

### Field Extraction Types
- `text`: Extracts inner text from matching element(s).
- `attribute`: Extracts attribute value specified by `"attribute": "href"`.

### Transformations
- `"trim"`: Removes leading/trailing whitespace.
- `"lower"`: Converts text to lowercase.
- `"upper"`: Converts text to uppercase.
- `{"replace": {"from": "$", "to": ""}}`: Replaces substrings.
- `{"split": ","}`: Splits string into a list of items.
- `{"regex": "([0-9]+)"}`: Applies regex matching / capture group extraction.

## Running Tests

To run all unit and integration tests:

```bash
PYTHONPATH=. pytest
```
