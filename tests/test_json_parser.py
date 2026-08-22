import pytest

from jexflow.errors import ParsingError
from jexflow.extraction import ElementExtractor
from jexflow.parser import (
    BaseDocument,
    JSONDocument,
    JSONPathSelectorEngine,
    get_document,
    get_selector_engine,
    register_document_parser,
    register_selector_engine,
)


def test_json_document_parse_valid():
    doc = JSONDocument('{"name": "test", "items": [1, 2, 3]}')
    assert doc.raw_content == {"name": "test", "items": [1, 2, 3]}

    doc_dict = JSONDocument({"a": 1})
    assert doc_dict.raw_content == {"a": 1}


def test_json_document_parse_invalid():
    with pytest.raises(ParsingError, match="Failed to parse JSON document"):
        JSONDocument("invalid json content")

    with pytest.raises(ParsingError, match="Unsupported content type"):
        JSONDocument(12345)


def test_jsonpath_selector_engine_basic():
    engine = JSONPathSelectorEngine()
    data = {
        "store": {
            "book": [
                {"title": "Book A", "price": 10},
                {"title": "Book B", "price": 20},
            ],
            "category": "fiction",
        },
    }

    doc = JSONDocument(data)

    # Root / key lookups
    assert engine.select(doc, "$.store.category") == ["fiction"]
    assert engine.select(data, "store.category") == ["fiction"]

    # Array index
    assert engine.select(doc, "$.store.book[0].title") == ["Book A"]
    assert engine.select(doc, "$.store.book[1].price") == [20]

    # Array wildcard
    assert engine.select(doc, "$.store.book[*].title") == ["Book A", "Book B"]

    # Recursive descent
    assert engine.select(doc, "..title") == ["Book A", "Book B"]


def test_element_extractor_json():
    data = {
        "users": [
            {"id": "1", "name": "Alice", "role": "admin"},
            {"id": "2", "name": "Bob", "role": "user"},
        ],
    }
    doc = JSONDocument(data)

    nodes = ElementExtractor.extract_nodes(doc, "$.users[*]", "jsonpath")
    assert len(nodes) == 2
    assert nodes[0] == {"id": "1", "name": "Alice", "role": "admin"}

    names = ElementExtractor.extract_field_values(doc, "$.users[*].name", "jsonpath")
    assert names == ["Alice", "Bob"]

    roles = ElementExtractor.extract_field_values(nodes[0], "role", "jsonpath")
    assert roles == ["admin"]


def test_custom_parser_and_selector_registration():
    class XMLDoc(BaseDocument):
        def __init__(self, content: str) -> None:
            self.content = f"XML<{content}>"

        @property
        def raw_content(self) -> str:
            return self.content

    class CustomEngine:
        def select(self, root: BaseDocument, selector: str) -> list[str]:
            return [f"custom:{selector}:{root.raw_content}"]

    register_document_parser("xml", XMLDoc)
    register_selector_engine("custom", CustomEngine())

    doc = get_document("hello", "xml")
    assert doc.raw_content == "XML<hello>"

    engine = get_selector_engine("custom")
    assert engine.select(doc, "query") == ["custom:query:XML<hello>"]
