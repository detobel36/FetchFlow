# Architecture Overview — Config-Driven Python Web Scraping Engine

## 1. High-Level Architecture

The **Config-Driven Python Web Scraping Engine** is a lightweight, embeddable Python library designed to execute web scraping workflows defined entirely in JSON. It is structured for low resource usage and clean extensibility, making it suitable for low-memory environments such as Kodi addons on Raspberry Pi.

```text
               ┌───────────────────────┐
               │   JSON Scraper Config  │
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
┌──────────────┐   ┌──────────────┐   ┌─────────────────┐
│ HTTP Client  │   │ HTML Parser  │   │  Transformers   │
│   (httpx)    │   │   (lxml)     │   │ (trim, regex..) │
└──────────────┘   └──────────────┘   └─────────────────┘
```

## 2. Component Design & Abstractions

1. **Config Layer (`scraper_engine.config`)**:
   - Validates JSON configurations against JSON Schema (`Draft7Validator`). Fails fast with precise field path error messages.

2. **HTTP Layer (`scraper_engine.http`)**:
   - `HTTPClient` interface with `HTTPXClient` adapter using `httpx`. Reuses connection pools, supports custom headers and parameters, and is easily replaceable.

3. **Templating System (`scraper_engine.templating`)**:
   - `TemplateRenderer` performs variable substitution (`{{var_name}}`) across strings, dictionary structures, and request parameters. Supports nested context lookup.

4. **Parser & Extractor Layer (`scraper_engine.parser`, `scraper_engine.extraction`)**:
   - `HTMLDocument` wraps `lxml.html`.
   - `CSSSelectorEngine` and `XPathSelectorEngine` provide CSS/XPath support.
   - `ElementExtractor` extracts text or attribute values, returning predictable string lists.

5. **Transformations Pipeline (`scraper_engine.transforms`)**:
   - Registry-based (`TransformerRegistry`) pipeline supporting `trim`, `lower`, `upper`, `replace`, `split`, and `regex`. Handles 1-to-N value expansion seamlessly.

6. **Workflow Executor (`scraper_engine.workflow`)**:
   - `ExecutionContext` maintains a scope stack for step results, global variables, and loop contexts.
   - `StepExecutor` executes sequential steps and `for_each` loops.

## 3. Future Evolution Roadmap

The system is designed so future features can be added without modifying the core workflow engine:

- **Methods & Auth**: Add POST/PUT/DELETE, headers, cookies, basic/bearer auth in `HTTPClient` / schema.
- **Parsers & Selectors**: Register `JSONPathSelectorEngine` for JSON APIs alongside CSS/XPath.
- **Nested Loops & Pagination**: Extend loop context stack in `ExecutionContext`.
- **Concurrency & Rate Limiting**: Introduce task pools in `WorkflowEngine` or `HTTPClient`.
- **Browser Automation**: Add optional Playwright/Chromium driver as an alternate `HTTPClient` implementation.
