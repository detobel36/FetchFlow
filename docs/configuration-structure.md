# Configuration Structure

## Top-Level JSON Schema

Every scraper configuration is represented as a JSON object containing global settings, global variables, and an array of workflow `steps`.

### Schema Overview

| Key | Type | Required | Description |
| --- | --- | --- | --- |
| `name` | string | **Yes** | A unique name or identifier for the scraper configuration. |
| `version` | string | No | Optional version string for tracking configuration versions (e.g. `"1.0"`). |
| `variables` | object | No | Dictionary of global string key-value pairs accessible across all steps. |
| `steps` | array | **Yes** | An ordered list of step objects executed sequentially. Must contain at least 1 step. |

---

## Complete JSON Configuration Example

```json
{
  "name": "e_commerce_catalog_scraper",
  "version": "1.0",
  "variables": {
    "base_url": "https://example.com",
    "user_agent": "FetchFlow-Scraper/1.0"
  },
  "steps": [
    {
      "id": "category_products",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/category/books",
        "headers": {
          "User-Agent": "{{user_agent}}"
        }
      },
      "extract": {
        "selector": ".product-card",
        "selector_type": "css"
      },
      "fields": {
        "product_id": {
          "selector": "a.product-link",
          "attribute": "data-id",
          "type": "attribute"
        },
        "title": {
          "selector": "h3.title",
          "type": "text",
          "transform": ["trim"]
        }
      }
    }
  ]
}
```

---

## Steps Structure

Each item in the `steps` array defines a single execution unit in the workflow pipeline.

### Step Properties

| Key | Type | Required | Description |
| --- | --- | --- | --- |
| `id` | string | **Yes** | Unique step identifier used to refer to its output in subsequent steps. |
| `for_each` | object | No | Configures iteration over previous step results. |
| `request` | object | No | HTTP request parameters (`url`, `method`, `headers`, `params`). |
| `extract` | object | No | Root element container selector for repeating HTML elements. |
| `fields` | object | No | Dictionary of field definitions to extract from each element container. |
