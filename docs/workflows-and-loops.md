# Workflows and Loops

## Sequential Execution & Scope

Steps in FetchFlow execute sequentially. Output from each step is stored under its `id` and can be passed to subsequent steps.

---

## `for_each` Sequence Diagram

The following sequence diagram illustrates how a two-step workflow with a `for_each` loop operates:

```mermaid
sequenceDiagram
    autonumber
    participant Engine as WorkflowEngine
    participant Site as Target Website
    participant Context as ExecutionContext

    Note over Engine, Context: Step 1: Extract List
    Engine->>Site: GET /products
    Site-->>Engine: HTML List Page
    Engine->>Context: Save list items as "list_step"

    Note over Engine, Context: Step 2: for_each Loop over "list_step"
    loop For each item in "list_step"
        Engine->>Context: Push loop item context (item_id)
        Engine->>Site: GET /product/{{item_id}}/details
        Site-->>Engine: HTML Detail Page
        Engine->>Context: Merge extracted details with item context
        Engine->>Context: Pop loop item context
    end
```

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

---

**Next:** Return to the [Wiki Overview](INDEX.md).
