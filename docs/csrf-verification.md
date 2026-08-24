# CSRF Token Verification & Bypass Guide

## Overview

Cross-Site Request Forgery (CSRF) protection is a standard security mechanism used by web applications to prevent unauthorized commands from being executed on behalf of an authenticated user. Sites protected by CSRF mechanisms require requests (especially state-changing methods like `POST`, `PUT`, or `DELETE`) to include a unique, unpredictable secret token.

In web scraping workflows, accessing protected endpoints requires fetching a valid CSRF token from the target frontend/login page before submitting requests to backend endpoints.

---

## The Principle of CSRF Bypass

The fundamental process for handling CSRF verification in scraping workflows consists of two main steps:

1. **Frontend Token Retrieval**: Execute an HTTP request (typically `GET`) to the frontend URL (such as a form, login page, or meta tag endpoint) that serves the HTML containing the CSRF token. Extract the token value from the response HTML element (e.g., an `<input type="hidden" name="csrf_token">` or `<meta name="csrf-token">`).
2. **Backend Submission**: Include the extracted token value in the subsequent HTTP request (e.g., `POST`) sent to the backend endpoint, passed either as a form/query parameter or an HTTP header (such as `X-CSRF-Token`).

---

## Manual Solution VS Optimised Solution

Jexflow supports two ways of handling CSRF verification:
- **Manual Multi-Step Solution**: Manually define a dedicated step to fetch the page and extract the token, then pass it as a template variable to the next step.
- **Optimised `csrf_token` Single-Step Solution**: Define `csrf_token` configuration directly inside the `request` block. Jexflow will automatically handle token retrieval and parameter/header injection in a single step.

---

### Comparison Matrix

| Feature | Manual Solution | Optimised Solution |
| --- | --- | --- |
| **Step Count** | Requires 2 steps (Fetch step + Action step) | Single step (`request.csrf_token` block) |
| **Token Extraction** | Requires explicit `extract` and `fields` in step 1 | Configured declaratively inside `request.csrf_token` |
| **Injection Mechanism** | Manual dynamic template reference (`{{csrf_token}}`) | Automatic injection via `param_name` and/or `header_name` |
| **Configuration Clarity** | Verbose workflow JSON | Clean and concise workflow JSON |

---

### 1. Manual Multi-Step Solution Example

```json
{
  "name": "manual_csrf_example",
  "variables": {
    "base_url": "https://example.com"
  },
  "steps": [
    {
      "id": "fetch_csrf_page",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/login"
      },
      "extract": {
        "selector": "form#login-form"
      },
      "fields": {
        "csrf_token": {
          "extract": {
            "selector": "input[name='_csrf_token']"
          },
          "type": "attribute",
          "attribute": "value"
        }
      }
    },
    {
      "id": "submit_backend_form",
      "request": {
        "method": "POST",
        "url": "{{base_url}}/api/submit",
        "headers": {
          "X-CSRF-Token": "{{csrf_token}}"
        },
        "params": {
          "data": "sample_value",
          "_csrf_token": "{{csrf_token}}"
        }
      },
      "extract": {
        "selector": ".response-card"
      },
      "fields": {
        "status": {
          "extract": {
            "selector": ".status-message"
          },
          "type": "text"
        }
      }
    }
  ]
}
```

---

### 2. Optimised Solution Example (`csrf_token` block)

With the optimised solution, you no longer need a preliminary extraction step. The request definition contains a `csrf_token` object specifying where to fetch the token from, how to extract it, and where to inject it (`param_name` or `header_name`).

```json
{
  "name": "optimised_csrf_example",
  "variables": {
    "base_url": "https://example.com"
  },
  "steps": [
    {
      "id": "submit_backend_form",
      "request": {
        "method": "POST",
        "url": "{{base_url}}/api/submit",
        "params": {
          "data": "sample_value"
        },
        "csrf_token": {
          "url": "{{base_url}}/login",
          "method": "GET",
          "extract": {
            "selector": "input[name='_csrf_token']"
          },
          "type": "attribute",
          "attribute": "value",
          "header_name": "X-CSRF-Token",
          "param_name": "_csrf_token"
        }
      },
      "extract": {
        "selector": ".response-card"
      },
      "fields": {
        "status": {
          "extract": {
            "selector": ".status-message"
          },
          "type": "text"
        }
      }
    }
  ]
}
```

---

### `csrf_token` Schema Reference

| Property | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `url` | string | **Yes** | - | Frontend URL serving the HTML/JSON page containing the CSRF token. |
| `method` | string | No | `"GET"` | HTTP method to retrieve the token page. |
| `extract` | object | **Yes** | - | Extraction selector configuration (`selector`, optional `selector_type`). |
| `type` | string | No | `"text"` | Field type (`"text"` or `"attribute"`). |
| `attribute` | string | No | `null` | Target attribute name when `type` is `"attribute"` (e.g. `value` or `content`). |
| `header_name` | string | No | `null` | HTTP header name into which the token is automatically injected (e.g. `X-CSRF-Token`). |
| `param_name` | string | No | `null` | Query or form parameter into which the token is automatically injected. |

---

**Next:** Return to the [Wiki Overview](INDEX.md).
