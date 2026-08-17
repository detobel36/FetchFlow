# Workflows and Loops

## Sequential Execution & Scope

Steps in FetchFlow execute sequentially in the order they are listed in the `steps` array.

Each step's extracted output is stored in the execution context under its step `id`. Subsequent steps can reference extracted values using mustache placeholders `{{step_id.field_name}}` or inside `for_each` loops.

---

## `for_each` Loops

To perform multi-step web scraping (e.g., fetching a list of categories/items first, and then visiting each item page to extract detailed info), use the `for_each` construct.

### `for_each` Schema

| Property | Type | Description |
| --- | --- | --- |
| `from` | string | *Required*. The `id` of a previous step whose extracted items should be iterated over. |
| `field` | string | Optional. Specific field name in the previous step item to expose as `{{value}}`. |

---

## Workflow Loop Example

```json
{
  "name": "multi_step_scraper",
  "variables": {
    "base_url": "https://example.com"
  },
  "steps": [
    {
      "id": "list_step",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/products"
      },
      "extract": {
        "selector": ".product-item"
      },
      "fields": {
        "item_id": {
          "selector": ".id-tag",
          "type": "text",
          "transform": ["trim"]
        },
        "item_title": {
          "selector": ".title",
          "type": "text",
          "transform": ["trim"]
        }
      }
    },
    {
      "id": "detail_step",
      "for_each": {
        "from": "list_step",
        "field": "item_id"
      },
      "request": {
        "method": "GET",
        "url": "{{base_url}}/product/{{value}}/details"
      },
      "extract": {
        "selector": ".details-card"
      },
      "fields": {
        "description": {
          "selector": ".description",
          "type": "text",
          "transform": ["trim"]
        },
        "price": {
          "selector": ".price",
          "type": "text",
          "transform": ["trim"]
        }
      }
    }
  ]
}
```

### Context Merging in Loops

When executing a step inside a `for_each` loop:
1. The request URL rendering can access fields from the item being iterated over (e.g., `{{item_id}}` or `{{value}}`).
2. The final result for the detail step merges the fields extracted in `list_step` with the newly extracted fields from `detail_step`.
