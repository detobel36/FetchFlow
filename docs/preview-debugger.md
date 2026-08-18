# Scraper Preview & Debugger

The **Scraper Preview & Debugger** is an interactive, web-based visual development tool built for developing, testing, and debugging JSON web scraper configurations.

It runs locally and uses the real Python `scraper_engine` library under the hood to execute requests and extract data.

---

## Why the Scraper Preview & Debugger Exists

Developing web scraping configurations purely in JSON can be challenging when testing complex CSS/XPath selectors or multi-step `for_each` loops.

The debugger solves this by answering three questions at every point in workflow execution:

1. **What is the scraper doing?** (Active step, active loop iteration, variable context, active JSON lines).
2. **What did the scraper receive?** (Actual HTTP request parameters, response status, duration, and sandboxed HTML rendering).
3. **What did the scraper extract?** (Container element match counts, highlighted DOM elements, extracted field values, and transformation pipeline steps).

---

## How to Start the Preview Tool

Ensure repository dependencies are installed:

```bash
pip install -r requirements.txt
```

Launch the preview server using the Python module entrypoint:

```bash
python -m preview
```

By default, the preview application starts locally at:
`http://127.0.0.1:8000`

### Command-Line Options

You can optionally pass an initial JSON configuration file and custom host/port flags:

```bash
# Load an initial JSON config on startup
python -m preview examples/ecommerce_scraper.json

# Specify custom host or port
python -m preview examples/ecommerce_scraper.json --host 0.0.0.0 --port 8080
```

---

## Key Features & Workflow

### 1. Two-Panel Interface
- **Left Panel (JSON Configuration Editor)**: Live CodeMirror editor with syntax highlighting, line numbers, JSON syntax validation error banners, schema validation, and automatic scrolling/highlighting of active workflow step lines.
- **Right Panel (Results & Response Preview)**:
  - **🌐 HTML Preview**: Sandboxed rendering of captured HTML with visual CSS outlines around matching container elements and field elements, plus hover tooltips showing selector metadata.
  - **📊 Extracted Data**: JSON view of extracted fields and records for the active step/iteration.
  - **📤 Request**: Method, rendered URL, headers, and query parameters.
  - **📥 Response**: HTTP status code, duration (ms), content size, content-type, headers, and raw response body.
  - **⚡ Transforms**: Pipeline trace inspection (`raw_value` ➔ `transformer` ➔ `final_value`).

### 2. Step & Loop Navigation
- **`Run` / `Start`**: Validates JSON configuration and executes the first step.
- **`Next Step →`**: Executes the next operation using the real scraping engine.
- **`← Previous Step`**: Restores the previously captured execution state from memory without repeating HTTP network requests.
- **`⚡ Re-run Step`**: Re-executes the current active step using updated selectors from the editor without repeating earlier steps.
- **`🔄 Restart`**: Resets the debug session and starts over from step 1.
- **Iteration Controls**: When stepping through `for_each` loops, navigate between individual iterations (`1 / 12`, `2 / 12`, ...) and inspect loop variable contexts (`id = "101"`).

---

## Architecture Note

The preview application resides in the `/preview` directory and is completely independent from the core `scraper_engine` library runtime. The core library does not depend on web frameworks or frontend tools and can run in lightweight or embedded Python environments without the preview tool.
