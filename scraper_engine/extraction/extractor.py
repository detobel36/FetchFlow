from typing import Any

from scraper_engine.errors import ExtractionError
from scraper_engine.parser.html import get_selector_engine


class ElementExtractor:
    """Extracts text or attribute values from DOM nodes or documents."""

    @staticmethod
    def extract_nodes(root: Any, selector: str, selector_type: str = "css") -> list[Any]: # noqa: ANN401
        """Select matching DOM nodes."""
        engine = get_selector_engine(selector_type)
        return engine.select(root, selector)

    @classmethod
    def extract_field_values(
        cls,
        root: Any, # noqa: ANN401
        selector: str,
        selector_type: str = "css",
        extraction_type: str = "text",
        attribute: str | None = None,
    ) -> list[str]:
        """Extract raw values from element(s) matching selector.

        Always returns a list of strings to preserve predictable output format.
        """
        nodes = cls.extract_nodes(root, selector, selector_type)
        results: list[str] = []

        for node in nodes:
            # If XPath selected a direct string/primitive value
            if isinstance(node, (str, int, float, bool)):
                results.append(str(node))
                continue

            # Otherwise, node is an lxml HtmlElement
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
                attr_val = node.get(attribute, "")
                if attr_val is not None:
                    results.append(str(attr_val))
            else:
                msg = f"Unsupported extraction type: '{extraction_type}'"
                raise ExtractionError(msg)

        return results
