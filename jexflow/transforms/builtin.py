import base64
import html
import re
from urllib.parse import parse_qs, quote, unquote, urljoin, urlparse

from jexflow.errors import TransformationError
from jexflow.transforms.base import BaseTransformer


class TrimTransformer(BaseTransformer):
    """Trims leading and trailing whitespace."""

    def transform_single(self, value: str) -> str:
        """Trims leading and trailing whitespace."""
        return value.strip()


class LowerTransformer(BaseTransformer):
    """Converts string to lowercase."""

    def transform_single(self, value: str) -> str:
        """Convert string to lowercase."""
        return value.lower()


class UpperTransformer(BaseTransformer):
    """Converts string to uppercase."""

    def transform_single(self, value: str) -> str:
        """Convert string to uppercase."""
        return value.upper()


class URLEncodeTransformer(BaseTransformer):
    """Encodes string for inclusion in URLs."""

    def transform_single(self, value: str) -> str:
        """URL encode string."""
        return quote(value, safe="")


class SpaceToDashTransformer(BaseTransformer):
    """Replaces spaces with dashes."""

    def transform_single(self, value: str) -> str:
        """Replace spaces with dashes."""
        return value.replace(" ", "-")


class ReplaceTransformer(BaseTransformer):
    """Replaces occurrences of a substring or pattern."""

    def __init__(self, from_str: str = "", to_str: str = "") -> None:
        """Init.

        Args:
        from_str: The substring or pattern to replace.
        to_str: The replacement string.
        """
        self.from_str = from_str
        self.to_str = to_str

    def transform_single(self, value: str) -> str:
        """Replace occurrences of a substring or pattern."""
        return value.replace(self.from_str, self.to_str)


class SplitTransformer(BaseTransformer):
    """Splits string by delimiter, expanding 1 item into multiple items."""

    def __init__(self, delimiter: str = ",") -> None:
        """Init.

        Args:
        delimiter: The delimiter to split the string by.
        """
        self.delimiter = delimiter

    def transform_single(self, value: str) -> list[str]:
        """Split string by delimiter, expanding 1 item into multiple items."""
        return value.split(self.delimiter)


class RegexTransformer(BaseTransformer):
    """Applies regex pattern matching/extraction to string.

    - If capture groups are present, returns captured group(s) or list of captures.
    - If no capture groups, returns matching substring(s).
    - If no match found, returns empty string or original value depending on configuration.
    """

    def __init__(self, pattern: str, group: int | None = None) -> None:
        """Init.

        Args:
        pattern: A regex pattern.
        group: An optional capture group to return.
        """
        try:
            self.regex = re.compile(pattern)
        except re.error as e:
            msg = f"Invalid regex pattern '{pattern}': {e}"
            raise TransformationError(msg) from e
        self.group = group

    def transform_single(self, value: str) -> str | list[str]:
        """Apply regex pattern matching/extraction to string."""
        matches = self.regex.findall(value)
        if not matches:
            return ""

        # If group is explicitly requested
        if self.group is not None:
            search_match = self.regex.search(value)
            if search_match and self.group <= len(search_match.groups()):
                return search_match.group(self.group)
            return ""

        # If findall returned tuples (multiple capture groups)
        if isinstance(matches[0], tuple):
            # Flatten or return first group/joined
            return ["".join(m) for m in matches]

        return matches


class URLJoinTransformer(BaseTransformer):
    """Joins a base URL with a relative URL string."""

    def __init__(self, base: str = "") -> None:
        """Init.

        Args:
            base: The base URL to join with.
        """
        self.base = base

    def transform_single(self, value: str) -> str:
        """Join base URL and relative URL value."""
        return urljoin(self.base, value)


class URLDecodeTransformer(BaseTransformer):
    """Decodes a URL-encoded string."""

    def transform_single(self, value: str) -> str:
        """URL decode string."""
        return unquote(value)


class ParseURLTransformer(BaseTransformer):
    """Parses a URL string and returns a specific URL component or string representation.

    Component options: 'scheme', 'netloc', 'path', 'params', 'query', 'fragment'.
    If component is None or empty, returns str(urlparse(value)).
    """

    def __init__(self, component: str | None = None) -> None:
        """Init.

        Args:
            component: Specific component to extract (e.g., 'scheme', 'netloc', 'path', 'query').
        """
        self.component = component

    def transform_single(self, value: str) -> str:
        """Parse URL string."""
        parsed = urlparse(value)
        if self.component:
            return getattr(parsed, self.component, "")
        return str(parsed)


class QueryParamTransformer(BaseTransformer):
    """Extracts the value of a specific query parameter from a URL or query string."""

    def __init__(self, param: str = "") -> None:
        """Init.

        Args:
            param: Name of the query parameter to extract.
        """
        self.param = param

    def transform_single(self, value: str) -> str | list[str]:
        """Extract query parameter value."""
        if not self.param:
            return ""

        # If full URL, parse query part, else parse value directly
        query_str = urlparse(value).query if "://" in value or "?" in value else value
        parsed = parse_qs(query_str)
        vals = parsed.get(self.param)
        if not vals:
            return ""
        if len(vals) == 1:
            return vals[0]
        return vals


class Base64EncodeTransformer(BaseTransformer):
    """Encodes a string to Base64."""

    def transform_single(self, value: str) -> str:
        """Base64 encode string."""
        return base64.b64encode(value.encode("utf-8")).decode("utf-8")


class Base64DecodeTransformer(BaseTransformer):
    """Decodes a Base64-encoded string."""

    def transform_single(self, value: str) -> str:
        """Base64 decode string."""
        try:
            return base64.b64decode(value.encode("utf-8")).decode("utf-8")
        except Exception as e:
            msg = f"Failed to base64 decode '{value}': {e}"
            raise TransformationError(msg) from e


class HTMLDecodeTransformer(BaseTransformer):
    """Decodes HTML entities (e.g. &amp;, &lt;) in a string."""

    def transform_single(self, value: str) -> str:
        """HTML decode string."""
        return html.unescape(value)


class HTMLEncodeTransformer(BaseTransformer):
    """Encodes special characters in a string to HTML entities."""

    def __init__(self, quote_char: bool = True) -> None:  # noqa: FBT001, FBT002
        """Init.

        Args:
            quote_char: Whether to encode quote characters.
        """
        self.quote = quote_char

    def transform_single(self, value: str) -> str:
        """HTML encode string."""
        return html.escape(value, quote=self.quote)
