# HTTP Requests

## Overview

The `request` object in a step specifies how to perform HTTP requests. FetchFlow uses `httpx` to handle requests efficiently.

## Request Properties

| Property | Type | Default | Description |
| --- | --- | --- | --- |
| `url` | string | *Required* | Target URL. Supports mustache-style template rendering (`{{variable_name}}`). |
| `method` | string | `"GET"` | HTTP method (e.g., `GET`, `POST`, `PUT`, `DELETE`). |
| `headers` | object | `{}` | Key-value dictionary of HTTP request headers. Supports templating. |
| `params` | object | `{}` | Key-value dictionary of URL query string parameters. Supports templating. |

---

## Templating Placeholders (`{{var}}`)

Values inside `url`, `headers`, and `params` strings can include dynamic variables enclosed in double curly braces `{{var_name}}`.

Variables are resolved from:
1. Global configuration `variables`
2. Fields extracted in previous steps
3. Iteration item properties in `for_each` loops

---

## Examples

### 1. Simple GET Request with Query Parameters

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

### 2. Request with Custom Headers & Dynamic Variables

```json
{
  "name": "templated_request_example",
  "variables": {
    "domain": "example.com",
    "api_token": "secret_token_123"
  },
  "steps": [
    {
      "id": "fetch_user_data",
      "request": {
        "method": "GET",
        "url": "https://{{domain}}/api/v1/user",
        "headers": {
          "Authorization": "Bearer {{api_token}}",
          "User-Agent": "FetchFlow-Engine"
        }
      }
    }
  ]
}
```
