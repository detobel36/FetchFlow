# Using FetchFlow as a Python Library

FetchFlow is not only a CLI tool for running configuration-driven scraping workflows; it can also be used directly as a Python library, similar to libraries like **BeautifulSoup**, **PyQuery**, or **lxml**.

Whether you want to perform quick DOM/JSON queries programmatically, build custom scraping scripts, or extend FetchFlow's document parsing capabilities, FetchFlow provides both low-level and high-level Python APIs.

---

## 1. High-Level Usage: Running Scrapers Programmatically (`Scraper`)

The `Scraper` class is the primary entry point for executing full FetchFlow workflows in Python.

### Loading from File, Dict, or JSON String

```python
from scraper_engine import Scraper

# 1. From a JSON file path
scraper = Scraper("workflow.json")
results = scraper.run()

# 2. From a dictionary
config_dict = {
    "name": "Quick Search",
    "version": "1.0",
    "steps": [
        {
            "name": "fetch_page",
            "request": {"method": "GET", "url": "https://example.com"},
            "extract": {
                "container": "div.article",
                "fields": {
                    "title": {"selector": "h2", "type": "text"}
                }
            }
        }
    ]
}
scraper = Scraper(config_dict)
results = scraper.run()

# 3. From a raw JSON string
raw_json = '{"name": "test", "version": "1.0", "steps": []}'
scraper = Scraper(raw_json)
results = scraper.run()
```

---

## 2. Low-Level Usage: Parsing & Selection (BeautifulSoup-Style)

For quick HTML or JSON parsing without defining full multi-step workflows, FetchFlow offers document wrappers (`HTMLDocument`, `JSONDocument`) and selector engines (`CSSSelectorEngine`, `XPathSelectorEngine`, `JSONPathSelectorEngine`).

### HTML Parsing & Querying

#### BeautifulSoup vs FetchFlow Comparison

**BeautifulSoup:**
```python
from bs4 import BeautifulSoup

html_content = '<div class="product"><h1>Laptop</h1><span class="price">$999</span></div>'
soup = BeautifulSoup(html_content, "html.parser")

# Select title
title = soup.select_one("div.product h1").get_text()
# Select price
price = soup.select_one("span.price").get_text()
```

**FetchFlow:**
```python
from scraper_engine.parser import HTMLDocument, CSSSelectorEngine, XPathSelectorEngine
from scraper_engine.extraction import ElementExtractor

html_content = '<div class="product"><h1 class="title">Laptop</h1><a href="/buy" class="link">Buy Now</a></div>'

# Parse document
doc = HTMLDocument(html_content)

# Option A: Extract field values directly using ElementExtractor
titles = ElementExtractor.extract_field_values(doc, "h1.title", selector_type="css", extraction_type="text")
print(titles)  # ['Laptop']

links = ElementExtractor.extract_field_values(doc, ".//a/@href", selector_type="xpath", extraction_type="attribute", attribute="href")
print(links)   # ['/buy']

# Option B: Use selector engine directly to retrieve lxml nodes
css_engine = CSSSelectorEngine()
nodes = css_engine.select(doc, "h1.title")
print(nodes[0].text_content())  # Laptop
```

### JSON Parsing & Querying with JSONPath

FetchFlow standardizes HTML and JSON extraction with unified selector models.

```python
from scraper_engine.parser import JSONDocument, JSONPathSelectorEngine
from scraper_engine.extraction import ElementExtractor

json_data = '{"store": {"books": [{"title": "Book A", "price": 10}, {"title": "Book B", "price": 15}]}}'

doc = JSONDocument(json_data)

# Extract titles using JSONPath
titles = ElementExtractor.extract_field_values(doc, "$.store.books[*].title", selector_type="jsonpath")
print(titles)  # ['Book A', 'Book B']

# Query nodes directly using JSONPathSelectorEngine
jsonpath_engine = JSONPathSelectorEngine()
book_prices = jsonpath_engine.select(doc, "$.store.books[*].price")
print(book_prices)  # [10, 15]
```

---

## 3. Extending Document Parsers & Selector Engines

FetchFlow is extensible. You can register custom document parsers or selector engines at runtime using `register_document_parser` and `register_selector_engine`.

### Registering a Custom Document Parser

```python
from scraper_engine.parser import BaseDocument, register_document_parser, get_document

class CustomXMLDocument(BaseDocument):
    def __init__(self, content: str):
        self._content = content

    @property
    def raw_content(self):
        return self._content

# Register custom parser factory
register_document_parser("xml", CustomXMLDocument)

# Retrieve document using registered type
doc = get_document("<xml><item>Data</item></xml>", parser_type="xml")
print(isinstance(doc, CustomXMLDocument))  # True
```

### Registering a Custom Selector Engine

```python
from scraper_engine.parser import SelectorEngine, register_selector_engine, get_selector_engine

class RegexSelectorEngine(SelectorEngine):
    import re

    def select(self, root, selector: str) -> list:
        content = root.raw_content if hasattr(root, "raw_content") else str(root)
        import re
        return re.findall(selector, content)

# Register custom selector engine
register_selector_engine("regex", RegexSelectorEngine())

# Use custom selector engine
engine = get_selector_engine("regex")
matches = engine.select("Email: test@example.com", r"[\w\.-]+@[\w\.-]+")
print(matches)  # ['test@example.com']
```

---

## Summary of Python Module Exports

| Module | Purpose | Key Exports |
| --- | --- | --- |
| `scraper_engine` | High-level scraper execution | `Scraper`, `ScraperEngineError` |
| `scraper_engine.parser` | Document parsing & selection | `HTMLDocument`, `JSONDocument`, `CSSSelectorEngine`, `XPathSelectorEngine`, `JSONPathSelectorEngine`, `register_document_parser`, `register_selector_engine`, `get_document`, `get_selector_engine` |
| `scraper_engine.extraction` | Element and field extraction | `ElementExtractor` |
