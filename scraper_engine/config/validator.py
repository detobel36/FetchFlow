import json
from pathlib import Path
from typing import Any

import jsonschema

from scraper_engine.errors import ConfigValidationError

SCRAPER_CONFIG_SCHEMA: dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "ScraperConfig",
    "type": "object",
    "required": ["name", "steps"],
    "properties": {
        "name": {"type": "string"},
        "version": {"type": "string"},
        "variables": {
            "type": "object",
            "additionalProperties": {"type": "string"},
        },
        "steps": {
            "type": "array",
            "minItems": 1,
            "items": {"$ref": "#/definitions/step"},
        },
    },
    "additionalProperties": False,
    "definitions": {
        "step": {
            "type": "object",
            "required": ["id"],
            "properties": {
                "id": {"type": "string"},
                "for_each": {"$ref": "#/definitions/for_each"},
                "request": {"$ref": "#/definitions/request"},
                "extract": {"$ref": "#/definitions/extract"},
                "fields": {
                    "type": "object",
                    "additionalProperties": {"$ref": "#/definitions/field"},
                },
            },
            "additionalProperties": False,
        },
        "for_each": {
            "type": "object",
            "required": ["from"],
            "properties": {
                "from": {"type": "string"},
                "field": {"type": "string"},
            },
            "additionalProperties": False,
        },
        "request": {
            "type": "object",
            "required": ["url"],
            "properties": {
                "method": {"type": "string", "default": "GET"},
                "url": {"type": "string"},
                "headers": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                },
                "params": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                },
            },
            "additionalProperties": False,
        },
        "extract": {
            "type": "object",
            "required": ["selector"],
            "properties": {
                "selector": {"type": "string"},
                "selector_type": {"type": "string", "enum": ["css", "xpath"], "default": "css"},
            },
            "additionalProperties": False,
        },
        "field": {
            "type": "object",
            "required": ["selector"],
            "properties": {
                "selector": {"type": "string"},
                "selector_type": {"type": "string", "enum": ["css", "xpath"], "default": "css"},
                "type": {"type": "string", "enum": ["text", "attribute"], "default": "text"},
                "attribute": {"type": "string"},
                "transform": {
                    "type": "array",
                    "items": {
                        "oneOf": [
                            {"type": "string"},
                            {"type": "object"},
                        ],
                    },
                },
            },
            "additionalProperties": False,
        },
    },
}


class ConfigValidator:
    """Validates scraper configuration against JSON schema."""

    @staticmethod
    def validate(config: dict[str, Any]) -> None:
        """Validate the scraper configuration against the schema."""
        validator = jsonschema.Draft7Validator(SCRAPER_CONFIG_SCHEMA)
        errors = list(validator.iter_errors(config))
        if errors:
            error_messages = []
            for err in errors:
                path = ".".join(str(p) for p in err.path) if err.path else "root"
                error_messages.append(f"{path}: {err.message}")
            raise ConfigValidationError(
                f"Configuration validation failed with {len(errors)} error(s):\n" + "\n".join(error_messages),
                errors=error_messages,
            )


class ConfigLoader:
    """Loads and validates JSON scraper configurations."""

    @staticmethod
    def load_from_dict(config_dict: dict[str, Any]) -> dict[str, Any]:
        """Load and validate a scraper configuration from a dictionary."""
        ConfigValidator.validate(config_dict)
        return config_dict

    @staticmethod
    def load_from_json(json_str: str) -> dict[str, Any]:
        """Load and validate a scraper configuration from a JSON string."""
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            msg = f"Invalid JSON format: {e}"
            raise ConfigValidationError(msg) from e
        return ConfigLoader.load_from_dict(data)

    @staticmethod
    def load_from_file(filepath: str) -> dict[str, Any]:
        """Load and validate a scraper configuration from a JSON file."""
        try:
            with Path.open(filepath, encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError as e:
            msg = f"Configuration file not found: {filepath}"
            raise ConfigValidationError(msg) from e
        except json.JSONDecodeError as e:
            msg = f"Invalid JSON in configuration file '{filepath}': {e}"
            raise ConfigValidationError(msg) from e
        return ConfigLoader.load_from_dict(data)
