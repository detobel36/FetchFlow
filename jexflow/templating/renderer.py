import re
from typing import Any

from jexflow.errors import TemplateError


class TemplateRenderer:
    """Renders strings by replacing {{variable_name}} placeholders with values from context."""

    VAR_PATTERN = re.compile(r"\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}")

    @classmethod
    def render_string(cls, template: str, context: dict[str, Any]) -> str:
        """Interpolate variables into a template string."""
        if not isinstance(template, str):
            return template

        def replace_match(match: re.Match[str]) -> str:
            """Replace a variable placeholder with its value from context."""
            var_name = match.group(1).strip()
            # Support nested context access (e.g., step.field)
            parts = var_name.split(".")
            curr = context
            for p in parts:
                if isinstance(curr, dict) and p in curr:
                    curr = curr[p]
                else:
                    msg = f"Variable '{var_name}' (missing key '{p}') not found in template context."
                    raise TemplateError(
                        msg,
                    )
            return str(curr)

        return cls.VAR_PATTERN.sub(replace_match, template)

    @classmethod
    def render_data(cls, data: Any, context: dict[str, Any]) -> Any: # noqa: ANN401
        """Recursively render template strings in dicts, lists, or primitive types."""
        if isinstance(data, str):
            return cls.render_string(data, context)
        if isinstance(data, dict):
            return {k: cls.render_data(v, context) for k, v in data.items()}
        if isinstance(data, list):
            return [cls.render_data(item, context) for item in data]
        return data
