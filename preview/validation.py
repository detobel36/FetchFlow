import json
import re
from typing import Any

from scraper_engine.config.validator import ConfigValidator
from scraper_engine.errors import ConfigValidationError


def find_key_line_number(json_str: str, key_path: list[str | int]) -> int:
    """Attempt to locate the line number in json_str corresponding to a key path."""
    if not key_path:
        return 1

    lines = json_str.splitlines()
    target_key = str(key_path[-1])

    for idx, line in enumerate(lines, start=1):
        if f'"{target_key}"' in line:
            return idx

    return 1


def validate_scraper_json(json_str: str) -> dict[str, Any]:
    """Validate JSON syntax and scraper config schema.

    Returns:
        Dict with keys:
        - valid: bool
        - syntax_error: dict or None (keys: line, column, message)
        - schema_errors: list of dicts (keys: path, message, line)
        - config: parsed dict or None
    """
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as err:
        return {
            "valid": False,
            "syntax_error": {
                "line": err.lineno,
                "column": err.colno,
                "message": f"Invalid JSON at line {err.lineno}: {err.msg}",
            },
            "schema_errors": [],
            "config": None,
        }

    if not isinstance(data, dict):
        return {
            "valid": False,
            "syntax_error": None,
            "schema_errors": [
                {
                    "path": "$",
                    "message": "Scraper configuration root must be a JSON object.",
                    "line": 1,
                },
            ],
            "config": None,
        }

    try:
        ConfigValidator.validate(data)
    except ConfigValidationError as err:
        schema_errors = []
        msg = str(err)

        match = re.search(r"Failed validating '([^']+)' in schema\['([^']+)'\]", msg)
        path_str = match.group(2) if match else "config"

        schema_errors.append({
            "path": path_str,
            "message": msg,
            "line": 1,
        })

        return {
            "valid": False,
            "syntax_error": None,
            "schema_errors": schema_errors,
            "config": data,
        }
    except Exception as err:  # noqa: BLE001
        return {
            "valid": False,
            "syntax_error": None,
            "schema_errors": [
                {
                    "path": "config",
                    "message": f"Configuration error: {err}",
                    "line": 1,
                },
            ],
            "config": data,
        }

    return {
        "valid": True,
        "syntax_error": None,
        "schema_errors": [],
        "config": data,
    }
