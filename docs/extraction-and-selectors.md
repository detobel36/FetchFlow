# Extraction and Selectors

## Overview

FetchFlow parses HTML responses using `lxml` and supports both **CSS selectors** and **XPath expressions**.

Extraction happens in two levels:
1. **Container Extraction (`extract`)**: Identifies repeated HTML block elements on a page (e.g. list items or product cards).
2. **Field Extraction (`fields`)**: Extracts specific text or attribute values inside each container element.

---

## Container Extraction (`extract`)

If `extract` is specified, the step iterates over all matching HTML nodes and extracts fields relative to each matching container node. If omitted, field selectors run against the entire document root.

### Properties

| Property | Type | Default | Description |
| --- | --- | --- | --- |
| `selector` | string | *Required* | CSS selector or XPath query matching container elements. |
| `selector_type` | string | `"css"` | Selector syntax: `"css"` or `"xpath"`. |

```json
"extract": {
  "selector": "ul.product-list > li.item",
  "selector_type": "css"
}
```

---

## Field Extraction (`fields`)

The `fields` object defines a map of field names to field extraction rules.

### Field Properties

| Property | Type | Default | Description |
| --- | --- | --- | --- |
| `selector` | string | *Required* | CSS selector or XPath query relative to the container element. |
| `selector_type` | string | `"css"` | `"css"` or `"xpath"`. |
| `type` | string | `"text"` | `"text"` to extract element text context, or `"attribute"` to extract an HTML attribute value. |
| `attribute` | string | Required if `type="attribute"` | Name of the HTML attribute to extract (e.g., `"href"`, `"src"`, `"data-id"`). |
| `transform` | array | `[]` | Pipeline of transformations to apply to extracted string value(s). |

---

## CSS vs XPath Examples

### 1. Using CSS Selectors

```json
{
  "id": "css_example",
  "request": { "url": "https://example.com/items" },
  "extract": {
    "selector": ".item-card",
    "selector_type": "css"
  },
  "fields": {
    "title": {
      "selector": "h2.title",
      "selector_type": "css",
      "type": "text"
    },
    "link": {
      "selector": "a.more-info",
      "selector_type": "css",
      "type": "attribute",
      "attribute": "href"
    }
  }
}
```

### 2. Using XPath Queries

XPath allows advanced queries such as selecting attributes directly or searching by text content.

```json
{
  "id": "xpath_example",
  "request": { "url": "https://example.com/items" },
  "extract": {
    "selector": "//div[contains(@class, 'item-card')]",
    "selector_type": "xpath"
  },
  "fields": {
    "title": {
      "selector": ".//h2/text()",
      "selector_type": "xpath",
      "type": "text"
    },
    "link": {
      "selector": ".//a/@href",
      "selector_type": "xpath",
      "type": "attribute",
      "attribute": "href"
    }
  }
}
```
