# Extraction and Selectors

## Overview

FetchFlow supports parsing HTML pages using `lxml` (via CSS and XPath) as well as REST API JSON structures (via JSONPath).

Extraction occurs in two distinct stages:
1. **Container Extraction (`extract`)**: Identifies repeating HTML block elements or JSON list items in a response.
2. **Field Extraction (`fields`)**: Extracts specific text, attribute values, or object properties within each container item.

---

## Field Extraction Properties

| Property | Type | Default | Description |
| --- | --- | --- | --- |
| `selector` | string | *Required* | CSS selector, XPath, or JSONPath query relative to the container element or root object. |
| `selector_type` | string | `"css"` (or `"jsonpath"` for JSON) | `"css"`, `"xpath"`, `"jsonpath"`, or `"json"`. |
| `type` | string | `"text"` | `"text"` to extract element text/primitive value, or `"attribute"` for an HTML/JSON attribute value. |
| `attribute` | string | Required if `type="attribute"` | Name of the attribute to extract. |
| `transform` | array | `[]` | Pipeline of transformations to apply to extracted value(s). |
| `extract` | object | Optional | Sub-container extraction selector for nested fields. |
| `fields` | object | Optional | Map of sub-fields to extract recursively within each sub-container. |

---

## Selector Types: CSS, XPath, and JSONPath

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
Use XPath expressions for advanced HTML selection:
```json
"link": {
  "selector": ".//a/@href",
  "selector_type": "xpath",
  "type": "attribute",
  "attribute": "href"
}
```

### JSONPath Queries
Use JSONPath expressions for REST API JSON responses:
```json
"user_name": {
  "selector": "$.data.user.name",
  "selector_type": "jsonpath"
}
```

JSONPath syntax supports:
- Dot notation (`$.store.book`)
- List indexing (`[0]`, `[1]`, `[*]`)
- Property wildcards (`*`)
- Recursive descent (`..key`)

---

## Selecting Specific Elements by Position (e.g., 3rd Element)

### CSS Selectors (`:nth-child`)

```json
"third_item": {
  "selector": "ul.items > li:nth-child(3)",
  "selector_type": "css",
  "type": "text"
}
```

### XPath Indexing (`[n]`)

```json
"third_item": {
  "selector": "//ul[@class='items']/li[3]",
  "selector_type": "xpath",
  "type": "text"
}
```

### JSONPath Array Indexing (`[n]`)

```json
"third_item": {
  "selector": "$.items[2]",
  "selector_type": "jsonpath"
}
```

---

**Next:** Learn about the [Transformations Pipeline](transformations.md).
