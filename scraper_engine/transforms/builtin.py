import re
from urllib.parse import quote

from scraper_engine.errors import TransformationError
from scraper_engine.transforms.base import BaseTransformer


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
