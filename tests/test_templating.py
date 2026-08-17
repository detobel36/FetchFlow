import pytest

from scraper_engine.errors import TemplateError
from scraper_engine.templating import TemplateRenderer


def test_template_render_simple():
    ctx = {"base_url": "https://example.com", "id": "123", "value": "test"}
    result = TemplateRenderer.render_string("{{base_url}}/item/{{id}}?q={{value}}", ctx)
    assert result == "https://example.com/item/123?q=test"


def test_template_render_nested():
    ctx = {"products": {"id": "456", "name": "Widget"}}
    result = TemplateRenderer.render_string("Item {{products.id}}: {{products.name}}", ctx)
    assert result == "Item 456: Widget"


def test_template_render_missing_variable():
    ctx = {"a": "1"}
    with pytest.raises(TemplateError) as exc_info:
        TemplateRenderer.render_string("{{missing_var}}", ctx)
    assert "missing_var" in str(exc_info.value)


def test_template_render_data_structures():
    ctx = {"domain": "example.com", "path": "api"}
    data = {
        "url": "https://{{domain}}/{{path}}",
        "params": ["{{domain}}", 42, True],
    }
    rendered = TemplateRenderer.render_data(data, ctx)
    assert rendered == {
        "url": "https://example.com/api",
        "params": ["example.com", 42, True],
    }
