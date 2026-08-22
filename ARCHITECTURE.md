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

## 3. Future Evolution Roadmap

The system is designed so future features (e.g. XML documents, GraphQL, or custom protocols) can be added without modifying the core workflow engine by registering new document parsers and selector engines.
