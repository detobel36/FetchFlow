from collections.abc import Callable
from typing import Any

from jexflow.errors import ParsingError
from jexflow.parser.base import BaseDocument, SelectorEngine
from jexflow.parser.html import CSSSelectorEngine, HTMLDocument, XPathSelectorEngine
from jexflow.parser.json_parser import JSONDocument, JSONPathSelectorEngine

# Document parsers registry
DOCUMENT_PARSERS: dict[str, Callable[[Any], BaseDocument]] = {
    "html": HTMLDocument,
    "json": JSONDocument,
}

# Selector engines registry
SELECTOR_ENGINES: dict[str, SelectorEngine] = {
    "css": CSSSelectorEngine(),
    "xpath": XPathSelectorEngine(),
    "jsonpath": JSONPathSelectorEngine(),
    "json": JSONPathSelectorEngine(),
}


def register_document_parser(parser_type: str, factory: Callable[[Any], BaseDocument]) -> None:
    """Register a new document parser type for extensible document handling."""
    DOCUMENT_PARSERS[parser_type.lower()] = factory


def register_selector_engine(selector_type: str, engine: SelectorEngine) -> None:
    """Register a new selector engine for extensible query evaluation."""
    SELECTOR_ENGINES[selector_type.lower()] = engine


def get_document(content: Any, parser_type: str = "html") -> BaseDocument:  # noqa: ANN401
    """Instantiate a BaseDocument using the registered parser for parser_type."""
    parser_key = parser_type.lower()
    if parser_key not in DOCUMENT_PARSERS:
        msg = f"Unsupported parser_type: '{parser_type}'. Supported: {list(DOCUMENT_PARSERS.keys())}"
        raise ParsingError(msg)

    parser_factory = DOCUMENT_PARSERS[parser_key]
    if isinstance(content, BaseDocument):
        return content
    return parser_factory(content)


def get_selector_engine(selector_type: str = "css") -> SelectorEngine:
    """Get selector engine by type."""
    engine_key = selector_type.lower()
    if engine_key not in SELECTOR_ENGINES:
        msg = f"Unsupported selector_type: '{selector_type}'. Supported: {list(SELECTOR_ENGINES.keys())}"
        raise ParsingError(msg)
    return SELECTOR_ENGINES[engine_key]


def __getattr__(name: str) -> Any:  # noqa: ANN401
    if name == "ElementExtractor":
        from jexflow.extraction.extractor import ElementExtractor  # noqa: PLC0415

        return ElementExtractor
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)


__all__ = [
    "BaseDocument",
    "CSSSelectorEngine",
    "ElementExtractor",
    "HTMLDocument",
    "JSONDocument",
    "JSONPathSelectorEngine",
    "SelectorEngine",
    "get_document",
    "get_selector_engine",
    "register_document_parser",
    "register_selector_engine",
]
