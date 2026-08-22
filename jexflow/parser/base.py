from abc import ABC, abstractmethod
from typing import Any


class BaseDocument(ABC):
    """Abstract base class for parsed documents."""

    @property
    @abstractmethod
    def raw_content(self) -> Any:  # noqa: ANN401
        """Return the underlying raw or parsed content of the document."""


class SelectorEngine(ABC):
    """Abstract interface for selector engines (CSS, XPath, JSONPath, etc.)."""

    @abstractmethod
    def select(self, root: Any, selector: str) -> list[Any]:  # noqa: ANN401
        """Return matching nodes, elements, or objects from root.

        Args:
            root: The root document or container node to query.
            selector: The query string or expression.

        Returns:
            A list of matching elements or values.
        """
