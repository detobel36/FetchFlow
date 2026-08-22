from typing import Any

import lxml.html

from jexflow.errors import ParsingError
from jexflow.parser.base import BaseDocument, SelectorEngine


class HTMLDocument(BaseDocument):
    """Encapsulates an lxml HTML tree for unified DOM querying."""

    def __init__(self, content: str) -> None:
        """Init.

        Args:
            content: The HTML content string.
        """
        try:
            self.tree = lxml.html.fromstring(content)
        except Exception as e:
            msg = f"Failed to parse HTML document: {e}"
            raise ParsingError(msg) from e

    @property
    def raw_content(self) -> Any:  # noqa: ANN401
        """Return underlying lxml HtmlElement tree."""
        return self.tree


class CSSSelectorEngine(SelectorEngine):
    """CSS Selector Engine using lxml."""

    def select(self, root: Any, selector: str) -> list[Any]:  # noqa: ANN401
        """Return matching DOM nodes or elements from root."""
        if hasattr(root, "cssselect"):
            return root.cssselect(selector)
        if isinstance(root, HTMLDocument):
            return root.tree.cssselect(selector)
        return []


class XPathSelectorEngine(SelectorEngine):
    """XPath Selector Engine using lxml."""

    def select(self, root: Any, selector: str) -> list[Any]:  # noqa: ANN401
        """Return matching DOM nodes or elements from root."""
        tree = root.tree if isinstance(root, HTMLDocument) else root
        if hasattr(tree, "xpath"):
            res = tree.xpath(selector)
            if isinstance(res, list):
                return res
            return [res]
        return []
