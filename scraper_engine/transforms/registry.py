from typing import Dict, Type, Union, Any, List

from scraper_engine.errors import TransformationError
from scraper_engine.transforms.base import BaseTransformer
from scraper_engine.transforms.builtin import (
    TrimTransformer,
    LowerTransformer,
    UpperTransformer,
    ReplaceTransformer,
    SplitTransformer,
    RegexTransformer,
)


class TransformerRegistry:
    """Registry for registering and creating transformers from JSON config."""

    _transformers: Dict[str, Type[BaseTransformer]] = {}

    @classmethod
    def register(cls, name: str, transformer_cls: Type[BaseTransformer]) -> None:
        cls._transformers[name] = transformer_cls

    @classmethod
    def create(cls, spec: Union[str, Dict[str, Any]]) -> BaseTransformer:
        """
        Creates a transformer instance from a string name (e.g. "trim")
        or a dict spec (e.g. {"replace": {"from": ",", "to": "."}} or {"regex": "([0-9]+)"}).
        """
        if isinstance(spec, str):
            name = spec
            kwargs = {}
        elif isinstance(spec, dict):
            if len(spec) != 1:
                raise TransformationError(f"Transformer spec dict must contain exactly 1 key, got: {list(spec.keys())}")
            name = list(spec.keys())[0]
            val = spec[name]
            if isinstance(val, dict):
                # E.g. {"replace": {"from": ",", "to": "."}} -> mapped to replace constructor kwargs
                kwargs = {}
                for k, v in val.items():
                    key = "from_str" if k == "from" else "to_str" if k == "to" else k
                    kwargs[key] = v
            elif isinstance(val, (str, int, float)):
                # E.g. {"split": ","} or {"regex": "pattern"}
                if name == "split":
                    kwargs = {"delimiter": str(val)}
                elif name == "regex":
                    kwargs = {"pattern": str(val)}
                else:
                    kwargs = {"pattern" if name in ("regex",) else "value": str(val)}
            else:
                kwargs = {}
        else:
            raise TransformationError(f"Invalid transformer specification: {spec}")

        if name not in cls._transformers:
            raise TransformationError(f"Unknown transformer '{name}'. Registered: {list(cls._transformers.keys())}")

        try:
            return cls._transformers[name](**kwargs)
        except TypeError as e:
            raise TransformationError(f"Failed to instantiate transformer '{name}': {e}") from e

    @classmethod
    def apply_pipeline(cls, values: List[str], pipeline_specs: List[Union[str, Dict[str, Any]]]) -> List[str]:
        """Runs a list of values through a sequence of transformation steps."""
        current = values
        for spec in pipeline_specs:
            transformer = cls.create(spec)
            current = transformer.apply(current)
        return current


# Register built-in transformers
TransformerRegistry.register("trim", TrimTransformer)
TransformerRegistry.register("lower", LowerTransformer)
TransformerRegistry.register("upper", UpperTransformer)
TransformerRegistry.register("replace", ReplaceTransformer)
TransformerRegistry.register("split", SplitTransformer)
TransformerRegistry.register("regex", RegexTransformer)
