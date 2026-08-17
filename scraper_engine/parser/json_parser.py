import json
import re
from typing import Any

from scraper_engine.errors import ParsingError
from scraper_engine.parser.base import BaseDocument, SelectorEngine


class JSONDocument(BaseDocument):
    """Encapsulates parsed JSON data (dict or list)."""

    def __init__(self, content: str | dict[str, Any] | list[Any]) -> None:
        """Init.

        Args:
            content: The raw JSON string or pre-parsed dict/list.
        """
        if isinstance(content, (dict, list)):
            self.data = content
        elif isinstance(content, str):
            try:
                self.data = json.loads(content)
            except Exception as e:
                msg = f"Failed to parse JSON document: {e}"
                raise ParsingError(msg) from e
        else:
            msg = f"Unsupported content type for JSONDocument: {type(content)}"
            raise ParsingError(msg)

    @property
    def raw_content(self) -> Any:  # noqa: ANN401
        """Return the underlying JSON data structure."""
        return self.data


class JSONPathSelectorEngine(SelectorEngine):
    """Simple, zero-dependency JSONPath selector engine.

    Supports:
    - Root ($) and property access (`.key` or `key`)
    - List index access (`[0]`, `[1]`, `[*]`)
    - Wildcards (`*`)
    - Recursive descent (`..key`)
    """

    def select(self, root: Any, selector: str) -> list[Any]:  # noqa: ANN401
        """Select elements from root matching the JSON selector string.

        Args:
            root: JSONDocument instance, dict, list, or primitive.
            selector: Path expression (e.g. "$.items[*].name" or "items.0.name").

        Returns:
            List of matching values.
        """
        data = root.raw_content if isinstance(root, JSONDocument) else root

        if selector in ("", "$", "."):
            return list(data) if isinstance(data, list) else [data]

        expr = selector.removeprefix("$").removeprefix(".")

        if not expr:
            return list(data) if isinstance(data, list) else [data]

        # Handle recursive descent prefix '..'
        if expr.startswith("."):
            key = expr[1:]
            return self._recursive_find(data, key)

        current_nodes = [data]
        tokens = self._tokenize_expression(expr)

        for token in tokens:
            next_nodes = []
            for node in current_nodes:
                next_nodes.extend(self._evaluate_token(node, token))
            current_nodes = next_nodes

        return current_nodes

    def _tokenize_expression(self, expr: str) -> list[dict[str, Any]]:
        """Parse expression into path tokens."""
        tokens = []
        parts = expr.split(".")
        for part in parts:
            if not part:
                continue
            sub_parts = re.split(r"\[(.*?)\]", part)
            for idx, sub in enumerate(sub_parts):
                if sub == "":
                    continue
                if idx % 2 == 1:  # Inside brackets
                    if sub == "*":
                        tokens.append({"type": "wildcard_index"})
                    elif sub.isdigit() or (sub.startswith("-") and sub[1:].isdigit()):
                        tokens.append({"type": "index", "value": int(sub)})
                    else:
                        key_val = sub.strip("'\"")
                        tokens.append({"type": "key", "value": key_val})
                elif sub == "*":
                    tokens.append({"type": "wildcard_key"})
                else:
                    tokens.append({"type": "key", "value": sub})
        return tokens

    def _evaluate_key_token(self, node: Any, val: Any) -> list[Any]:  # noqa: ANN401
        if isinstance(node, dict) and val in node:
            return [node[val]]
        if isinstance(node, list) and isinstance(val, str) and val.isdigit():
            idx = int(val)
            if 0 <= idx < len(node):
                return [node[idx]]
        return []

    def _evaluate_index_token(self, node: Any, val: Any) -> list[Any]:  # noqa: ANN401
        if isinstance(node, list):
            idx = int(val)
            if -len(node) <= idx < len(node):
                return [node[idx]]
        return []

    def _evaluate_token(self, node: Any, token: dict[str, Any]) -> list[Any]:  # noqa: ANN401
        """Evaluate a single token against a node."""
        t_type = token["type"]
        val = token.get("value")

        if t_type == "key":
            return self._evaluate_key_token(node, val)
        if t_type == "index":
            return self._evaluate_index_token(node, val)
        if t_type in ("wildcard_key", "wildcard_index"):
            if isinstance(node, dict):
                return list(node.values())
            if isinstance(node, list):
                return node
        return []

    def _recursive_find(self, data: Any, key: str) -> list[Any]:  # noqa: ANN401
        """Recursively collect values for a key across nested dicts and lists."""
        results = []
        if isinstance(data, dict):
            for k, v in data.items():
                if k == key:
                    if isinstance(v, list):
                        results.extend(v)
                    else:
                        results.append(v)
                results.extend(self._recursive_find(v, key))
        elif isinstance(data, list):
            for item in data:
                results.extend(self._recursive_find(item, key))
        return results
