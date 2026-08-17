from abc import ABC, abstractmethod
from typing import List, Union, Any

from scraper_engine.errors import TransformationError


class BaseTransformer(ABC):
    """Abstract base class for all transformations."""

    @abstractmethod
    def transform_single(self, value: str) -> Union[str, List[str]]:
        """Transforms a single string value into a string or list of strings."""
        pass

    def apply(self, values: List[str]) -> List[str]:
        """Applies transformation to a list of values, handling list expansion."""
        result: List[str] = []
        for val in values:
            transformed = self.transform_single(val)
            if isinstance(transformed, list):
                result.extend(transformed)
            elif isinstance(transformed, str):
                result.append(transformed)
            elif transformed is not None:
                result.append(str(transformed))
        return result
