# Architecture Overview — Config-Driven Python Web Scraping Engine

## 1. High-Level Architecture

The **Config-Driven Python Web Scraping Engine** is a lightweight, embeddable Python library designed to execute web scraping workflows defined entirely in JSON. It is structured for low resource usage and clean extensibility, supporting both HTML documents and REST JSON API endpoints.

```text
               ┌───────────────────────┐
               │   JSON Scraper Config │
               └───────────┬───────────┘
                           │
                   Config Loader & Validator (jsonschema)
                           │
                           ▼
                 ┌──────────────────┐
                 │ Workflow Engine  │
                 └─────────┬────────┘
                           │
       ┌───────────────────┼───────────────────┐
       ▼                   ▼                   ▼
┌──────────────┐   ┌─────────────────┐ ┌─────────────────┐
│ HTTP Client  │   │ Parser & Doc    │ │  Transformers   │
│   (httpx)    │   │ (HTML / JSON)   │ │ (trim, regex..) │
└──────────────┘   └─────────────────┘ └─────────────────┘
```

## 2. Component Design & Abstractions

1. **Config Layer (`jexflow.config`)**:
   - Validates JSON configurations against JSON Schema (`Draft7Validator`). Fails fast with precise field path error messages.

2. **HTTP Layer (`jexflow.http`)**:
   - `HTTPClient` interface with `HTTPXClient` adapter using `httpx`. Reuses connection pools, supports custom headers and parameters.

3. **Templating System (`jexflow.templating`)**:
   - `TemplateRenderer` performs variable substitution (`{{var_name}}`) across strings, dictionary structures, and request parameters.

4. **Parser & Extractor Layer (`jexflow.parser`, `jexflow.extraction`)**:
   - Generic `BaseDocument` interface implemented by `HTMLDocument` (lxml) and `JSONDocument` (JSON).
   - Registries for dynamic parser registration (`register_document_parser`) and selector engines (`register_selector_engine`).
   - `CSSSelectorEngine`, `XPathSelectorEngine`, and `JSONPathSelectorEngine` for CSS, XPath, and JSONPath querying.
   - `ElementExtractor` extracts text, attributes, or JSON primitive fields predictably.

5. **Transformations Pipeline (`jexflow.transforms`)**:
   - Registry-based (`TransformerRegistry`) pipeline supporting `trim`, `lower`, `upper`, `replace`, `split`, and `regex`.

6. **Workflow Executor (`jexflow.workflow`)**:
   - `ExecutionContext` maintains a scope stack for step results, global variables, and loop contexts.
   - `StepExecutor` executes sequential steps and `for_each` loops on both HTML and REST JSON response payloads.

## 3. Architectural Problematic Points & Technical Debt

During system review and auditing, the following architectural problematic points and risk areas were identified:

### 3.1. Security: Server-Side Request Forgery (SSRF) in Preview Proxy (`preview/app.py`)
- **Issue**: The UI preview tool includes a `/api/proxy` endpoint designed to fetch external HTML/assets and bypass browser CORS policies. Previously, this endpoint accepted any `http://` or `https://` target URL without IP/hostname restrictions.
- **Risk**: An attacker or untrusted configuration could force the preview server to send HTTP requests to internal services (e.g. `http://127.0.0.1:8000`, `http://169.254.169.254` AWS metadata endpoint, or internal `10.0.0.0/8` networks), exposing internal infrastructure.
- **Remediation**: Implemented strict host validation in `preview/app.py` blocking loopback, link-local, RFC 1918 private IPv4 addresses, IPv6 private addresses, and cloud metadata IPs.

### 3.2. State Mutation & Variable Context Leaks (`jexflow/workflow`)
- **Issue**: `ExecutionContext` merges dictionaries (`self.global_variables | self.step_results | loop_frame`). When iterating over items in `for_each` loops, shallow dictionary copying or in-place item updates risked polluting variables across loop iterations or leaking child context into sibling steps.
- **Remediation**: Standardized on explicit shallow and deep copy semantics for loop context frames in `StepExecutor` and `ExecutionContext` to guarantee strict isolation between loop iterations.

### 3.3. Unbounded Debug Session Caching in Preview (`preview/session.py`)
- **Issue**: `DebugSession` retains all step iteration execution traces in an in-memory dictionary `self.history[(step_index, iteration_index)]`. For workflows processing thousands of loop items or large HTML documents, this unconstrained history can lead to significant memory consumption.
- **Recommendation**: Introduce a configurable max history size or LRU eviction strategy for large debug sessions in future iterations.

### 3.4. Absence of Explicit Request Timeout & Rate Limiting Controls in Config
- **Issue**: While `HTTPXClient` defaults to a 30-second timeout, individual JSON workflow step configurations cannot specify custom timeouts, retry strategies, or delay intervals between loop iterations.
- **Recommendation**: Extend the JSON Schema and `HTTPRequest` model to support per-step timeout override, retry policy, and inter-request delay settings.

## 4. Future Evolution Roadmap

1. **XML & GraphQL Parser Plugins**: Leverage `register_document_parser` and `register_selector_engine` to add native support for XML feeds and GraphQL endpoints.
2. **Resilient Rate Limiting & Delays**: Add optional rate-limiting / sleep configuration to `for_each` loops to avoid throttling when scraping external targets.
