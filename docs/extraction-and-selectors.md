# Extraction and Selectors

## Overview

FetchFlow parses HTML responses using `lxml` and supports both **CSS selectors** and **XPath expressions**.

Extraction occurs in two distinct stages:
1. **Container Extraction (`extract`)**: Identifies repeating HTML block/container elements on a page (e.g. product cards).
2. **Field Extraction (`fields`)**: Extracts specific text or attribute values within each container element.

---

## HTML Structural Example & Extraction Scope

Consider the following HTML document:

```html
<div class="item-card">
  <h2 class="title">Item 1</h2>
</div>
<div class="item-card">
  <h2 class="title">Item 2</h2>
  <h2>Another title</h2>
</div>
<h2 class="title">Sub section</h2>
```

### Understanding `extract` vs `fields`

If you specify `extract` with selector `.item-card`:
- FetchFlow scopes extraction strictly to elements inside each `<div class="item-card">`.
- The standalone `<h2 class="title">Sub section</h2>` is ignored because it is outside `.item-card`.
- Inside the second `.item-card`, `<h2>Another title</h2>` does not match `h2.title`, so only `Item 2` is extracted for `title`.

**JSON Configuration for this HTML:**

```json
{
  "id": "items_step",
  "request": {
    "url": "https://example.com/catalog"
  },
  "extract": {
    "selector": ".item-card",
    "selector_type": "css"
  },
  "fields": {
    "item_title": {
      "selector": "h2.title",
      "selector_type": "css",
      "type": "text"
    }
  }
}
```

**Result Output:**

```json
[
  { "item_title": "Item 1" },
  { "item_title": "Item 2" }
]
```

---

## Field Extraction Properties

| Property | Type | Default | Description |
| --- | --- | --- | --- |
| `selector` | string | *Required* | CSS selector or XPath query relative to the container element. |
| `selector_type` | string | `"css"` | `"css"` or `"xpath"`. |
| `type` | string | `"text"` | `"text"` to extract element text, or `"attribute"` for an HTML attribute value. |
| `attribute` | string | Required if `type="attribute"` | Name of the HTML attribute to extract (e.g. `"href"`, `"data-id"`). |
| `transform` | array | `[]` | Pipeline of transformations to apply to extracted value(s). |

---

## Selector Types: CSS vs XPath

### CSS Selectors
Use standard CSS selector syntax:
```json
"title": {
  "selector": "h2.title",
  "selector_type": "css",
  "type": "text"
}
```

### XPath Queries
Use XPath expressions for advanced selection (e.g. attributes or sub-tree queries):
```json
"link": {
  "selector": ".//a/@href",
  "selector_type": "xpath",
  "type": "attribute",
  "attribute": "href"
}
```

---

**Next:** Learn about the [Transformations Pipeline](transformations.md).
