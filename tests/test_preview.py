from pathlib import Path

import httpx
from fastapi.testclient import TestClient

from jexflow.http import HTTPXClient
from preview.app import app
from preview.html_highlighter import highlight_html_elements
from preview.session import DebugSession
from preview.validation import find_key_line_number, validate_scraper_json


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
        <head><base href="https://example.com/store/items"></head>
        <body>
            <div class="product"><span class="price">$10</span></div>
            <img src="/image.png">
            <a href="https://other.com/page">Link</a>
        </body>
    </html>"""

    highlighted = highlight_html_elements(
        html_content=html_input,
        container_selector=".product",
        container_selector_type="css",
        fields_config={"price": {"extract": {"selector": ".price", "selector_type": "css"}}},
        base_url="https://example.com/store/items",
    )

    assert 'data-debugger-container="true"' in highlighted
    assert 'data-debugger-selector=".product"' in highlighted
    assert 'data-debugger-field="price"' in highlighted
    assert 'data-debugger-field-selector=".price"' in highlighted
    assert "debugger-preview-styles" in highlighted
    assert "<base" not in highlighted
    assert "/api/proxy?url=https%3A%2F%2Fexample.com%2Fimage.png" in highlighted
    assert "/api/proxy?url=https%3A%2F%2Fother.com%2Fpage" in highlighted


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
                    "id": {"extract": {"selector": ".id"}, "type": "text"},
                },
            },
            {
                "id": "step_details",
                "for_each": {"from": "step_items", "field": "id"},
                "request": {"method": "GET", "url": "{{base_url}}/detail/{{id}}"},
                "extract": {"selector": ".detail", "selector_type": "css"},
                "fields": {
                    "val": {"extract": {"selector": ".val"}, "type": "text"},
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


def test_fastapi_schema_endpoint():
    test_client = TestClient(app)
    r_schema = test_client.get("/api/config/schema")
    assert r_schema.status_code == 200
    schema_data = r_schema.json()
    assert schema_data.get("title") == "ScraperConfig"
    assert "steps" in schema_data.get("required", [])


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


def test_proxy_endpoint_validation():
    test_client = TestClient(app)

    # Test invalid scheme
    r_invalid = test_client.get("/api/proxy?url=ftp://example.com")
    assert r_invalid.status_code == 400
    assert "Invalid URL scheme" in r_invalid.json()["detail"]

    # Test missing url
    r_missing = test_client.get("/api/proxy")
    assert r_missing.status_code == 422

    # Test forbidden private / loopback hosts (SSRF prevention)
    forbidden_urls = [
        "http://localhost/admin",
        "http://127.0.0.1:8000/api/session/state",
        "http://169.254.169.254/latest/meta-data/",
        "http://10.0.0.1/private",
        "http://192.168.1.1/router",
        "http://172.16.0.1/internal",
    ]
    for target in forbidden_urls:
        r_ssrf = test_client.get(f"/api/proxy?url={target}")
        assert r_ssrf.status_code == 400
        assert "forbidden" in r_ssrf.json()["detail"].lower()


def test_debug_session_save_config(tmp_path: Path):
    target_file = tmp_path / "config_save_test.json"
    valid_json = """{
        "name": "save_test_scraper",
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

    session = DebugSession(json_config=valid_json)
    res = session.save_config(valid_json, filepath=target_file)

    assert res["success"] is True
    assert target_file.exists()
    assert target_file.read_text(encoding="utf-8") == valid_json
    assert session.config_path == target_file
    assert session.get_state()["config_path"] == str(target_file.resolve())

    # Attempt saving invalid json
    invalid_json = "{"
    import pytest
    with pytest.raises(ValueError, match="Cannot save configuration due to syntax error"):
        session.save_config(invalid_json, filepath=target_file)


def test_fastapi_export_and_save_endpoints(tmp_path: Path):
    test_client = TestClient(app)

    config_str = """{
        "name": "export_save_test",
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

    # Test export with explicit filename
    r_exp1 = test_client.post("/api/config/export", json={"config_json": config_str, "filename": "custom_name.json"})
    assert r_exp1.status_code == 200
    assert r_exp1.headers["content-disposition"] == 'attachment; filename="custom_name.json"'
    assert r_exp1.text == config_str

    # Test export with default auto-derived filename from config name
    r_exp2 = test_client.post("/api/config/export", json={"config_json": config_str})
    assert r_exp2.status_code == 200
    assert r_exp2.headers["content-disposition"] == 'attachment; filename="export_save_test.json"'

    # Test export with invalid config
    r_exp_err = test_client.post("/api/config/export", json={"config_json": "{"})
    assert r_exp_err.status_code == 400

    # Test save endpoint
    save_file = tmp_path / "saved_via_api.json"
    r_save = test_client.post("/api/config/save", json={"config_json": config_str, "filepath": str(save_file)})
    assert r_save.status_code == 200
    assert r_save.json()["success"] is True
    assert save_file.exists()
    assert save_file.read_text(encoding="utf-8") == config_str

    # Test save with invalid json
    r_save_err = test_client.post("/api/config/save", json={"config_json": "{", "filepath": str(save_file)})
    assert r_save_err.status_code == 400
