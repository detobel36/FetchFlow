# FetchFlow Documentation & Wiki

Welcome to the **FetchFlow** wiki! FetchFlow is a lightweight, configuration-driven web scraping engine written in Python. It allows you to build complete scraping workflows using structured JSON configuration files.

## Wiki Navigation

1. [Getting Started](getting-started.md)
   - Installation and dependencies (`requirements.txt`)
   - CLI usage for testing and execution
   - Basic usage in Python code
2. [Configuration Structure](configuration-structure.md)
   - Top-level JSON schema (`name`, `version`, `variables`, `steps`)
   - Step definitions and execution flow
3. [HTTP Requests](requests.md)
   - Defining HTTP requests (`method`, `url`, `headers`, `params`)
   - Dynamic template placeholders (`{{variable_name}}`)
4. [Extraction and Selectors](extraction-and-selectors.md)
   - Container extraction (`extract`)
   - Field extraction (`fields`)
   - Selectors: CSS vs XPath
   - Extraction types (`text`, `attribute`)
5. [Transformations Pipeline](transformations.md)
   - Field value transformation pipelines
   - Built-in transformers (`trim`, `lower`, `upper`, `replace`, `split`, `regex`)
6. [Workflows & Loops](workflows-and-loops.md)
   - Passing extracted data across sequential steps
   - Iterating over step results with `for_each` loops
   - Variable scope and precedence
7. [Scraper Preview & Debugger](preview-debugger.md)
   - Interactive developer tool overview
   - Launching via CLI (`python -m preview`)
   - Step navigation, element highlighting, and loop iteration debugging
8. [Using FetchFlow as a Python Library](python-library-guide.md)
   - Programmatic workflow execution with `Scraper`
   - Low-level HTML/JSON parsing and BeautifulSoup-style selection
   - Registering custom document parsers and selector engines
