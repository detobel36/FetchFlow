from typing import Any, ClassVar

from scraper_engine.errors import TransformationError
from scraper_engine.transforms.base import BaseTransformer
from scraper_engine.transforms.builtin import (
    LowerTransformer,
    RegexTransformer,
    ReplaceTransformer,
    SplitTransformer,
    TrimTransformer,
    UpperTransformer,
)


class TransformerRegistry:
    """Registry for registering and creating transformers from JSON config."""

    _transformers: ClassVar[dict[str, type[BaseTransformer]]] = {}

    @classmethod
    def register(cls, name: str, transformer_cls: type[BaseTransformer]) -> None:
        """Register a transformer class by name."""
        cls._transformers[name] = transformer_cls

    @classmethod
    def _parse_spec(cls, spec: str | dict[str, Any]) -> tuple[str, dict[str, Any]]:
        """Parse a spec into (name, kwargs).

        Handles:
        - String: simple transformer name (e.g., "trim")
        - Dict with scalar value: e.g., {"split": ","} or {"regex": "pattern"}
        - Dict with nested dict: e.g., {"replace": {"from": ",", "to": "."}}
        """
        if isinstance(spec, str):
            return spec, {}

        if isinstance(spec, dict):
            if len(spec) != 1:
                msg = f"Transformer spec dict must contain exactly 1 key, got: {list(spec.keys())}"
                raise TransformationError(msg)
            name = next(iter(spec.keys()))
            value = spec[name]
            kwargs = cls._build_kwargs(name, value)
            return name, kwargs

        msg = f"Invalid transformer specification: {spec}"
        raise TransformationError(msg)

    @classmethod
    def _build_kwargs(cls, name: str, value: Any) -> dict[str, Any]:  # noqa: ANN401
        """Build constructor kwargs from a transformer name and value."""
        if isinstance(value, dict):
            # E.g. {"replace": {"from": ",", "to": "."}}
            kwargs = {}
            for k, v in value.items():
                key = "from_str" if k == "from" else "to_str" if k == "to" else k
                kwargs[key] = v
            return kwargs

        if isinstance(value, (str, int, float)):
            # E.g. {"split": ","} or {"regex": "pattern"}
            if name == "split":
                return {"delimiter": str(value)}
            if name == "regex":
                return {"pattern": str(value)}
            return {"value": str(value)}

        return {}

    @classmethod
    def create(cls, spec: str | dict[str, Any]) -> BaseTransformer:
        """Create a transformer instance from a string name (e.g. "trim") or a dict spec.

        Example: {"replace": {"from": ",", "to": "."}} or {"regex": "([0-9]+)"}.
        """
        name, kwargs = cls._parse_spec(spec)

        if name not in cls._transformers:
            msg = f"Unknown transformer '{name}'. Registered: {list(cls._transformers.keys())}"
            raise TransformationError(msg)

        try:
            return cls._transformers[name](**kwargs)
        except TypeError as e:
            msg = f"Failed to instantiate transformer '{name}': {e}"
            raise TransformationError(msg) from e

    @classmethod
    def apply_pipeline_with_trace(
        cls, values: list[str], pipeline_specs: list[str | dict[str, Any]],
    ) -> tuple[list[str], list[dict[str, Any]]]:
        """Run a list of values through transformations and return trace details.

        Returns:
            Tuple of (final_values, trace_steps)
            where trace_steps is a list of dicts:
            [{"spec": spec, "name": transformer_name, "input": [...], "output": [...]}]
        """
        current = values
        trace: list[dict[str, Any]] = []

        for spec in pipeline_specs:
            name, _ = cls._parse_spec(spec)
            transformer = cls.create(spec)
            input_vals = list(current)
            current = transformer.apply(current)
            trace.append({
                "spec": spec,
                "name": name,
                "input": input_vals,
                "output": list(current),
            })

        return current, trace

    @classmethod
    def apply_pipeline(cls, values: list[str], pipeline_specs: list[str | dict[str, Any]]) -> list[str]:
        """Run a list of values through a sequence of transformation steps."""
        final_vals, _ = cls.apply_pipeline_with_trace(values, pipeline_specs)
        return final_vals


# Register built-in transformers
TransformerRegistry.register("trim", TrimTransformer)
TransformerRegistry.register("lower", LowerTransformer)
TransformerRegistry.register("upper", UpperTransformer)
TransformerRegistry.register("replace", ReplaceTransformer)
TransformerRegistry.register("split", SplitTransformer)
TransformerRegistry.register("regex", RegexTransformer)
