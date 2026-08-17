# HTTP Requests

## Overview

The `request` object in a step specifies how to perform HTTP requests. FetchFlow uses `httpx` to execute HTTP calls efficiently and supports both HTML web pages and REST API JSON endpoints.

## Request Properties

| Property | Type | Default | Description |
| --- | --- | --- | --- |
| `url` | string | *Required* | Target URL. Supports dynamic template placeholders (`{{variable_name}}`). |
| `method` | string | `"GET"` | HTTP method (e.g., `GET`, `POST`, `PUT`, `DELETE`). |
| `response_type` | string | Auto-detected | Format of expected response (`"html"`, `"json"`). If omitted, inferred from content-type or structure. |
| `headers` | object | `{}` | Key-value dictionary of HTTP request headers. Supports templating. |
| `params` | object | `{}` | Key-value dictionary of URL query string parameters. Supports templating. |

---

## Dynamic Template Placeholders (`{{var}}`)

Values inside `url`, `headers`, and `params` strings can include dynamic variables enclosed in double curly braces `{{var_name}}`.

Variables are resolved from:
1. Global configuration `variables`
2. Fields extracted in previous steps
3. Iteration item properties in `for_each` loops

---

## Examples

### 1. REST API JSON GET Request

```json
{
  "id": "get_users",
  "request": {
    "method": "GET",
    "url": "https://api.example.com/v1/users",
    "response_type": "json"
  }
}
```

### 2. GET Request with Query Parameters

```json
{
  "id": "search_step",
  "request": {
    "method": "GET",
    "url": "https://api.example.com/search",
    "params": {
      "q": "python",
      "limit": "10"
    }
  }
}
```

### 3. POST Request with Parameters & Dynamic Headers

```json
{
  "id": "post_example",
  "request": {
    "method": "POST",
    "url": "https://api.example.com/items",
    "headers": {
      "Content-Type": "application/x-www-form-urlencoded",
      "Authorization": "Bearer {{user_token}}"
    },
    "params": {
      "action": "create",
      "category": "books"
    }
  }
}
```

---

**Next:** Learn about [Extraction and Selectors](extraction-and-selectors.md).
