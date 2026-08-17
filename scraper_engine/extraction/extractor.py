from typing import List, Any, Dict, Optional
import lxml.html

from scraper_engine.errors import ExtractionError
from scraper_engine.parser.html import HTMLDocument, get_selector_engine


class ElementExtractor:
    """Extracts text or attribute values from DOM nodes or documents."""

    @staticmethod
    def extract_nodes(root: Any, selector: str, selector_type: str = "css") -> List[Any]:
        """Selects matching DOM nodes."""
        engine = get_selector_engine(selector_type)
        return engine.select(root, selector)

    @classmethod
    def extract_field_values(
        cls,
        root: Any,
        selector: str,
        selector_type: str = "css",
        extraction_type: str = "text",
        attribute: Optional[str] = None
    ) -> List[str]:
        """
        Extracts raw values from element(s) matching selector.
        Always returns a list of strings to preserve predictable output format.
        """
        nodes = cls.extract_nodes(root, selector, selector_type)
        results: List[str] = []

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
                    raise ExtractionError("Extraction type 'attribute' requires 'attribute' name parameter.")
                attr_val = node.get(attribute, "")
                if attr_val is not None:
                    results.append(str(attr_val))
            else:
                raise ExtractionError(f"Unsupported extraction type: '{extraction_type}'")

        return results
