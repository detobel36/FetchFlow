import json
from typing import Any

import jsonschema

from jexflow.config.validator import SCRAPER_CONFIG_SCHEMA


def find_key_line_number(json_str: str, key_path: list[str | int]) -> int:
    """Attempt to locate the line number in json_str corresponding to a key path."""
    if not key_path:
        return 1

    lines = json_str.splitlines()
    string_keys = [str(k) for k in key_path if isinstance(k, str)]
    if not string_keys:
        return 1

    target_key = string_keys[-1]
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

    validator = jsonschema.Draft7Validator(SCRAPER_CONFIG_SCHEMA)
    errors = list(validator.iter_errors(data))
    if errors:
        schema_errors = []
        for err in errors:
            path_list = list(err.path)
            path_str = ".".join(str(p) for p in path_list) if path_list else "root"
            line = find_key_line_number(json_str, path_list)
            schema_errors.append({
                "path": path_str,
                "message": f"{path_str}: {err.message}",
                "line": line,
            })

        return {
            "valid": False,
            "syntax_error": None,
            "schema_errors": schema_errors,
            "config": data,
        }

    return {
        "valid": True,
        "syntax_error": None,
        "schema_errors": [],
        "config": data,
    }
