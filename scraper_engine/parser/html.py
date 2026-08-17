from abc import ABC, abstractmethod
from typing import List, Any
import lxml.html

from scraper_engine.errors import ParsingError


class HTMLDocument:
    """Encapsulates an lxml HTML tree for unified DOM querying."""

    def __init__(self, content: str):
        try:
            self.tree = lxml.html.fromstring(content)
        except Exception as e:
            raise ParsingError(f"Failed to parse HTML document: {e}") from e


class SelectorEngine(ABC):
    """Abstract interface for selector engines (CSS, XPath, JSONPath, etc.)."""

    @abstractmethod
    def select(self, root: Any, selector: str) -> List[Any]:
        """Returns matching DOM nodes or elements from root."""
        pass


class CSSSelectorEngine(SelectorEngine):
    """CSS Selector Engine using lxml."""

    def select(self, root: Any, selector: str) -> List[Any]:
        if hasattr(root, "cssselect"):
            return root.cssselect(selector)
        elif isinstance(root, HTMLDocument):
            return root.tree.cssselect(selector)
        return []


class XPathSelectorEngine(SelectorEngine):
    """XPath Selector Engine using lxml."""

    def select(self, root: Any, selector: str) -> List[Any]:
        tree = root.tree if isinstance(root, HTMLDocument) else root
        if hasattr(tree, "xpath"):
            res = tree.xpath(selector)
            if isinstance(res, list):
                return res
            return [res]
        return []


SELECTOR_ENGINES = {
    "css": CSSSelectorEngine(),
    "xpath": XPathSelectorEngine(),
}


def get_selector_engine(selector_type: str = "css") -> SelectorEngine:
    if selector_type not in SELECTOR_ENGINES:
        raise ParsingError(f"Unsupported selector_type: '{selector_type}'. Supported: {list(SELECTOR_ENGINES.keys())}")
    return SELECTOR_ENGINES[selector_type]
