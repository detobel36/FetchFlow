# Transformations Pipeline

## Overview

After raw text or attribute values are extracted from HTML, Jexflow allows running them through a chain of string transformers specified in `transform`.

Transformations are configured as an ordered array of transformer keywords or parameter objects.

---

## Built-In Transformers

### 1. Simple Keyword Transformers

- **`trim`**: Removes leading and trailing whitespace.
  - *Example:* `"   hello world  "` &rarr; `"hello world"`
- **`lower`**: Converts text to lowercase.
  - *Example:* `"Hello World"` &rarr; `"hello world"`
- **`upper`**: Converts text to uppercase.
  - *Example:* `"hello world"` &rarr; `"HELLO WORLD"`
- **`url_encode`** / **`urlencode`**: Encodes text for inclusion in URLs.
  - *Example:* `"hello world & foo=bar"` &rarr; `"hello%20world%20%26%20foo%3Dbar"`
- **`urldecode`**: Decodes URL-encoded text.
  - *Example:* `"hello%20world"` &rarr; `"hello world"`
- **`base64_encode`**: Encodes string into Base64 format.
  - *Example:* `"hello"` &rarr; `"aGVsbG8="`
- **`base64_decode`**: Decodes Base64-encoded string.
  - *Example:* `"aGVsbG8="` &rarr; `"hello"`
- **`html_decode`**: Decodes HTML entities to plain text.
  - *Example:* `"foo &amp; bar"` &rarr; `"foo & bar"`
- **`html_encode`**: Encodes special characters to HTML entities.
  - *Example:* `"foo & bar"` &rarr; `"foo &amp; bar"`
- **`space_to_dash`**: Replaces spaces with dashes.
  - *Example:* `"like this for exemple"` &rarr; `"like-this-for-exemple"`

### 2. Parameterized Transformers

- **`urljoin`**: Resolves a relative URL against a base URL.
  - **Parameter:** base URL string.
  - *Config:* `{"urljoin": "https://example.com/docs/"}`
  - *Example:* `"page.html"` &rarr; `"https://example.com/docs/page.html"`
- **`parse_url`**: Parses a URL and extracts a specific component (e.g., `scheme`, `netloc`, `path`, `query`).
  - **Parameter:** URL component name.
  - *Config:* `{"parse_url": "netloc"}`
  - *Example:* `"https://example.com/path"` &rarr; `"example.com"`
- **`query_param`**: Extracts the value of a specific query parameter from a URL or query string.
  - **Parameter:** query parameter name.
  - *Config:* `{"query_param": "id"}`
  - *Example:* `"https://example.com/item?id=123"` &rarr; `"123"`

- **`replace`**: Replaces occurrences of a string with another.
  - **Parameters:** `from` (string to search), `to` (replacement string).
  - *Config:* `{"replace": {"from": "$", "to": ""}}`
  - *Example:* `"$19.99"` &rarr; `"19.99"`
- **`split`**: Splits a string into a list of strings by a delimiter.
  - **Parameter:** delimiter string.
  - *Config:* `{"split": ","}`
  - *Example:* `"apple,banana,orange"` &rarr; `["apple", "banana", "orange"]`
- **`regex`**: Extracts matching pattern or capture group.
  - **Parameter:** regex pattern string.
  - *Config:* `{"regex": "([0-9.]+)"}`
  - *Example:* `"Price: 29.95 USD"` &rarr; `"29.95"`

---

## JSON Pipeline Example

```json
{
  "id": "transform_example",
  "request": { "url": "https://example.com/products" },
  "extract": { "selector": ".product" },
  "fields": {
    "clean_price": {
      "extract": { "selector": ".price-tag" },
      "type": "text",
      "transform": [
        "trim",
        { "replace": { "from": "USD", "to": "" } },
        { "regex": "([0-9.]+)" }
      ]
    }
  }
}
```

---

## Extending with Custom Transformers (Python API)

Developers can register custom transformation functions using `TransformerRegistry`:

```python
from jexflow.transforms import BaseTransformer, TransformerRegistry

class ReverseTransformer(BaseTransformer):
    def transform_single(self, value: str) -> str:
        return value[::-1]

# Register custom transformer with keyword 'reverse'
TransformerRegistry.register("reverse", ReverseTransformer)
```

Once registered in Python, the custom keyword can be used directly in JSON configs:

```json
"transform": ["trim", "reverse"]
```

---

**Next:** Learn about [Workflows & Loops](workflows-and-loops.md).
