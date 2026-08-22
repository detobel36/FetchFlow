from typing import Any

from jexflow.errors import ExtractionError
from jexflow.parser import BaseDocument, get_selector_engine


class ElementExtractor:
    """Extracts text or attribute values from DOM nodes, JSON objects, or documents."""

    @staticmethod
    def extract_nodes(root: Any, selector: str, selector_type: str = "css") -> list[Any]:  # noqa: ANN401
        """Select matching nodes or objects."""
        engine = get_selector_engine(selector_type)
        return engine.select(root, selector)

    @classmethod
    def extract_field_values(  # noqa: C901, PLR0912
        cls,
        root: Any,  # noqa: ANN401
        selector: str,
        selector_type: str = "css",
        extraction_type: str = "text",
        attribute: str | None = None,
    ) -> list[Any]:
        """Extract raw values from element(s) matching selector."""
        nodes = cls.extract_nodes(root, selector, selector_type)
        results: list[Any] = []

        is_json_context = selector_type in ("jsonpath", "json")

        for node in nodes:
            if isinstance(node, BaseDocument):
                node = node.raw_content  # noqa: PLW2901

            if isinstance(node, (int, float, bool)):
                results.append(str(node) if not is_json_context else node)
                continue

            if isinstance(node, str):
                results.append(node)
                continue

            if node is None:
                continue

            if isinstance(node, (dict, list)):
                if is_json_context:
                    results.append(node)
                else:
                    results.append(str(node))
                continue

            if extraction_type == "text":
                if hasattr(node, "text_content"):
                    text_val = node.text_content()
                elif hasattr(node, "text") and node.text:
                    text_val = node.text
                else:
                    text_val = ""
                results.append(text_val)
            elif extraction_type == "attribute":
                if not attribute:
                    msg = "Extraction type 'attribute' requires 'attribute' name parameter."
                    raise ExtractionError(msg)
                attr_val = node.get(attribute, "") if hasattr(node, "get") or isinstance(node, dict) else ""
                if attr_val is not None:
                    results.append(str(attr_val))
            else:
                msg = f"Unsupported extraction type: '{extraction_type}'"
                raise ExtractionError(msg)

        return results
