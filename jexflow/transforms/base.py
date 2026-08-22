from abc import ABC, abstractmethod


class BaseTransformer(ABC):
    """Abstract base class for all transformations."""

    @abstractmethod
    def transform_single(self, value: str) -> str | list[str]:
        """Transform a single string value into a string or list of strings."""

    def apply(self, values: list[str]) -> list[str]:
        """Apply transformation to a list of values, handling list expansion."""
        result: list[str] = []
        for val in values:
            transformed = self.transform_single(val)
            if isinstance(transformed, list):
                result.extend(transformed)
            elif isinstance(transformed, str):
                result.append(transformed)
            elif transformed is not None:
                result.append(str(transformed))
        return result
