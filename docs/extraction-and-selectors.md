# Extraction and Selectors

## Overview

Jexflow supports parsing HTML pages using `lxml` (via CSS and XPath) as well as REST API JSON structures (via JSONPath).

Extraction occurs in two distinct stages:
1. **Container Extraction (`extract`)**: Identifies repeating HTML block elements or JSON list items in a response.
2. **Field Extraction (`fields`)**: Extracts specific text, attribute values, or object properties within each container item.

---

## Field Extraction Properties

| Property | Type | Default | Description |
| --- | --- | --- | --- |
| `extract` | object | Optional | Sub-container extraction selector for nested fields, or field element selector object containing `selector` and optional `selector_type`. |
| `type` | string | `"text"` | `"text"` to extract element text/primitive value, or `"attribute"` for an HTML/JSON attribute value. |
| `attribute` | string | Required if `type="attribute"` | Name of the attribute to extract. |
| `transform` | array | `[]` | Pipeline of transformations to apply to extracted value(s). |
| `fields` | object | Optional | Map of sub-fields to extract recursively within each sub-container. |

---

## Selector Types: CSS, XPath, and JSONPath

### CSS Selectors
Use standard CSS selector syntax:
```json
"title": {
  "extract": {
    "selector": "h2.title",
    "selector_type": "css"
  },
  "type": "text"
}
```

### XPath Queries
Use XPath expressions for advanced HTML selection:
```json
"link": {
  "extract": {
    "selector": ".//a/@href",
    "selector_type": "xpath"
  },
  "type": "attribute",
  "attribute": "href"
}
```

### JSONPath Queries
Use JSONPath expressions for REST API JSON responses:
```json
"user_name": {
  "extract": {
    "selector": "$.data.user.name",
    "selector_type": "jsonpath"
  }
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
  "extract": {
    "selector": "ul.items > li:nth-child(3)",
    "selector_type": "css"
  },
  "type": "text"
}
```

### XPath Indexing (`[n]`)

```json
"third_item": {
  "extract": {
    "selector": "//ul[@class='items']/li[3]",
    "selector_type": "xpath"
  },
  "type": "text"
}
```

### JSONPath Array Indexing (`[n]`)

```json
"third_item": {
  "extract": {
    "selector": "$.items[2]",
    "selector_type": "jsonpath"
  }
}
```

---

**Next:** Learn about the [Transformations Pipeline](transformations.md).
