from typing import Any

from scraper_engine.parser.html import HTMLDocument, get_selector_engine

__all__ = ["ElementExtractor", "HTMLDocument", "get_selector_engine"]


def __getattr__(name: str) -> Any:  # noqa: ANN401
    if name == "ElementExtractor":
        from scraper_engine.extraction.extractor import ElementExtractor  # noqa: PLC0415

        return ElementExtractor
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
