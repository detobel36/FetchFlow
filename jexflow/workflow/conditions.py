from typing import Any, ClassVar

from jexflow.templating import TemplateRenderer


def resolve_field_value(item: Any, field_path: str) -> Any:  # noqa: ANN401
    """Resolve a dot-separated field path from an item structure."""
    parts = field_path.split(".")
    current = item
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list):
            res = []
            for elem in current:
                if isinstance(elem, dict) and part in elem:
                    val = elem[part]
                    if isinstance(val, list):
                        res.extend(val)
                    else:
                        res.append(val)
            current = res
        else:
            return None
    return current


def _to_float(val: Any) -> float | None:  # noqa: ANN401
    """Try to convert value to float, returns None if failed."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        cleaned = val.strip()
        try:
            return float(cleaned)
        except ValueError:
            pass
    return None


class ConditionEvaluator:
    """Evaluates filtering conditions against item dicts or context."""

    OPERATORS: ClassVar[set[str]] = {
        "contains",
        "not_contains",
        "equals",
        "not_equals",
        "bigger_than",
        "smaller_than",
    }

    @classmethod
    def evaluate_condition(
        cls,
        condition: dict[str, Any],
        item: dict[str, Any],
        context_data: dict[str, Any] | None = None,
    ) -> bool:
        """Evaluate a single condition object against an item."""
        field_path = condition.get("field")
        op = str(condition.get("operator", "")).strip()
        target_val = condition.get("value")

        full_ctx = dict(item)
        if context_data:
            full_ctx.update(context_data)

        if isinstance(target_val, str):
            target_val = TemplateRenderer.render_string(target_val, full_ctx)

        if field_path:
            actual_val = resolve_field_value(item, field_path)
            if actual_val is None and context_data:
                actual_val = resolve_field_value(context_data, field_path)
        else:
            actual_val = item

        return cls.compare(actual_val, op, target_val)

    @classmethod
    def compare(cls, actual: Any, operator: str, expected: Any) -> bool:  # noqa: C901, PLR0911, PLR0912, ANN401
        """Compare actual value with expected value based on operator."""
        if operator not in cls.OPERATORS:
            msg = f"Unsupported condition operator: '{operator}'"
            raise ValueError(msg)

        if operator == "contains":
            if actual is None:
                return False
            if isinstance(actual, (list, tuple)):
                return any(cls.compare(elem, "contains", expected) for elem in actual)
            actual_str = str(actual).lower()
            expected_str = str(expected).lower() if expected is not None else ""
            return expected_str in actual_str

        if operator == "not_contains":
            return not cls.compare(actual, "contains", expected)

        if operator == "equals":
            if actual is None or expected is None:
                return actual == expected
            num_a, num_b = _to_float(actual), _to_float(expected)
            if num_a is not None and num_b is not None:
                return num_a == num_b
            if isinstance(actual, str) and isinstance(expected, str):
                return actual.lower() == expected.lower()
            return actual == expected

        if operator == "not_equals":
            return not cls.compare(actual, "equals", expected)

        if operator == "bigger_than":
            num_a, num_b = _to_float(actual), _to_float(expected)
            if num_a is not None and num_b is not None:
                return num_a > num_b
            if actual is not None and expected is not None:
                return str(actual) > str(expected)
            return False

        if operator == "smaller_than":
            num_a, num_b = _to_float(actual), _to_float(expected)
            if num_a is not None and num_b is not None:
                return num_a < num_b
            if actual is not None and expected is not None:
                return str(actual) < str(expected)
            return False

        msg = f"Unsupported condition operator: '{operator}'"
        raise ValueError(msg)

    @classmethod
    def evaluate_conditions(
        cls,
        conditions: list[dict[str, Any]] | dict[str, Any],
        item: dict[str, Any],
        context_data: dict[str, Any] | None = None,
    ) -> bool:
        """Evaluate a list of conditions (AND logic) or single condition object."""
        if not conditions:
            return True
        if isinstance(conditions, dict):
            conditions = [conditions]

        return all(cls.evaluate_condition(cond, item, context_data) for cond in conditions)
