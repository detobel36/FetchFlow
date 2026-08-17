# Transformations Pipeline

## Overview

After raw text or attribute values are extracted from HTML, FetchFlow allows running them through a chain of string transformers specified in `transform`.

Transformations are configured as an ordered array of transformer names (strings) or parameter objects.

```json
"transform": [
  "trim",
  "lower",
  { "replace": { "from": "$", "to": "" } }
]
```

---

## Built-In Transformers

### 1. `trim`
Removes leading and trailing whitespace from strings.
- **Config**: `"trim"`

### 2. `lower`
Converts text to lowercase.
- **Config**: `"lower"`

### 3. `upper`
Converts text to uppercase.
- **Config**: `"upper"`

### 4. `replace`
Replaces substring matches with a new substring.
- **Config**: `{"replace": {"from": "old_string", "to": "new_string"}}`

### 5. `split`
Splits a string by a delimiter into a list of strings (1-to-N expansion).
- **Config**: `{"split": ","}`

### 6. `regex`
Applies a regular expression pattern. If the regex contains capture groups, it extracts the captured group string.
- **Config**: `{"regex": "([0-9,.]+)"}`

---

## JSON Transformation Pipeline Example

```json
{
  "id": "transform_example",
  "request": { "url": "https://example.com/products" },
  "extract": { "selector": ".product" },
  "fields": {
    "clean_price": {
      "selector": ".price-tag",
      "type": "text",
      "transform": [
        "trim",
        { "replace": { "from": "USD", "to": "" } },
        { "regex": "([0-9.]+)" }
      ]
    },
    "tags": {
      "selector": ".tags",
      "type": "text",
      "transform": [
        "trim",
        "lower",
        { "split": "," }
      ]
    }
  }
}
```
