import httpx
from fastapi.testclient import TestClient

from preview.app import app
from preview.html_highlighter import highlight_html_elements
from preview.session import DebugSession
from preview.validation import find_key_line_number, validate_scraper_json
from scraper_engine.http import HTTPXClient


def test_validate_scraper_json_valid():
    raw_json = """{
        "name": "test_scraper",
        "steps": [
            {
                "id": "step1",
                "request": {
                    "method": "GET",
                    "url": "https://example.com"
                }
            }
        ]
    }"""
    res = validate_scraper_json(raw_json)
    assert res["valid"] is True
    assert res["syntax_error"] is None
    assert res["schema_errors"] == []
    assert res["config"]["name"] == "test_scraper"


def test_validate_scraper_json_invalid_syntax():
    raw_json = """{
        "name": "test_scraper",
        "steps": [
    """
    res = validate_scraper_json(raw_json)
    assert res["valid"] is False
    assert res["syntax_error"] is not None
    assert "Invalid JSON at line" in res["syntax_error"]["message"]


def test_validate_scraper_json_invalid_schema():
    raw_json = """{
        "name": "test_scraper"
    }"""
    res = validate_scraper_json(raw_json)
    assert res["valid"] is False
    assert len(res["schema_errors"]) > 0


def test_find_key_line_number():
    raw_json = """{
  "name": "test",
  "steps": [
    {
      "id": "products",
      "request": { "url": "https://example.com" }
    }
  ]
}"""
    line = find_key_line_number(raw_json, ["steps", "products"])
    assert line == 5


def test_highlight_html_elements():
    html_input = """<html>
        <body>
            <div class="product"><span class="price">$10</span></div>
        </body>
    </html>"""

    highlighted = highlight_html_elements(
        html_content=html_input,
        container_selector=".product",
        container_selector_type="css",
        fields_config={"price": {"selector": ".price", "selector_type": "css"}},
    )

    assert 'data-debugger-container="true"' in highlighted
    assert 'data-debugger-selector=".product"' in highlighted
    assert 'data-debugger-field="price"' in highlighted
    assert 'data-debugger-field-selector=".price"' in highlighted
    assert "debugger-preview-styles" in highlighted


def test_debug_session_navigation_and_caching():
    page_html = """
    <html>
        <body>
            <div class="item"><span class="id">1</span></div>
            <div class="item"><span class="id">2</span></div>
        </body>
    </html>
    """

    detail_1 = '<html><body><div class="detail"><span class="val">A</span></div></body></html>'
    detail_2 = '<html><body><div class="detail"><span class="val">B</span></div></body></html>'

    request_count = 0

    def mock_handler(request: httpx.Request):
        nonlocal request_count
        request_count += 1
        url = str(request.url)
        if "items" in url:
            return httpx.Response(200, text=page_html, request=request)
        if "detail/1" in url:
            return httpx.Response(200, text=detail_1, request=request)
        if "detail/2" in url:
            return httpx.Response(200, text=detail_2, request=request)
        return httpx.Response(404, text="Not found", request=request)

    transport = httpx.MockTransport(mock_handler)
    client_wrapper = HTTPXClient(client=httpx.Client(transport=transport))

    config = {
        "name": "session_test",
        "variables": {"base_url": "https://example.com"},
        "steps": [
            {
                "id": "step_items",
                "request": {"method": "GET", "url": "{{base_url}}/items"},
                "extract": {"selector": ".item", "selector_type": "css"},
                "fields": {
                    "id": {"selector": ".id", "type": "text"},
                },
            },
            {
                "id": "step_details",
                "for_each": {"from": "step_items", "field": "id"},
                "request": {"method": "GET", "url": "{{base_url}}/detail/{{id}}"},
                "extract": {"selector": ".detail", "selector_type": "css"},
                "fields": {
                    "val": {"selector": ".val", "type": "text"},
                },
            },
        ],
    }

    session = DebugSession(json_config=config, http_client=client_wrapper)
    state1 = session.start()

    assert state1["current_step_index"] == 0
    assert state1["step_id"] == "step_items"
    assert len(state1["results"]) == 2
    assert request_count == 1

    # Advance to step 2 (iteration 0)
    state2 = session.next()
    assert state2["current_step_index"] == 1
    assert state2["current_iteration_index"] == 0
    assert state2["step_id"] == "step_details"
    assert state2["total_iterations"] == 2
    assert state2["results"][0]["val"] == "A"
    assert request_count == 3  # step_details executed for iteration 0 and 1

    # Advance to iteration 1
    state3 = session.next()
    assert state3["current_step_index"] == 1
    assert state3["current_iteration_index"] == 1
    assert state3["results"][0]["val"] == "B"

    # Go previous (should NOT trigger new HTTP requests due to caching!)
    req_count_before_prev = request_count
    state_prev = session.previous()
    assert state_prev["current_step_index"] == 1
    assert state_prev["current_iteration_index"] == 0
    assert request_count == req_count_before_prev

    # Re-run current step
    state_rerun = session.rerun_current_step()
    assert state_rerun["current_step_index"] == 1
    assert request_count > req_count_before_prev


def test_fastapi_preview_endpoints():
    test_client = TestClient(app)

    config_str = """{
        "name": "fastapi_test",
        "steps": [
            {
                "id": "s1",
                "request": {
                    "method": "GET",
                    "url": "https://example.com"
                }
            }
        ]
    }"""

    # Test config validate
    r_val = test_client.post("/api/config/validate", json={"config_json": config_str})
    assert r_val.status_code == 200
    assert r_val.json()["valid"] is True

    # Test load session
    r_load = test_client.post("/api/session/load", json={"config_json": config_str})
    assert r_load.status_code == 200
    assert r_load.json()["step_id"] == "s1"

    # Test get state
    r_state = test_client.get("/api/session/state")
    assert r_state.status_code == 200
    assert r_state.json()["step_id"] == "s1"

    # Test preview html
    r_html = test_client.get("/api/preview-html")
    assert r_html.status_code == 200
    assert "text/html" in r_html.headers["content-type"]
