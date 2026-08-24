import json
from os import PathLike
from pathlib import Path
from typing import Any

import jsonschema

from jexflow.errors import ConfigValidationError

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
                "parser": {"type": "string"},
                "for_each": {"$ref": "#/definitions/for_each"},
                "request": {"$ref": "#/definitions/request"},
                "extract": {"$ref": "#/definitions/extract"},
                "fields": {
                    "type": "object",
                    "additionalProperties": {"$ref": "#/definitions/field"},
                },
                "conditions": {
                    "type": "array",
                    "items": {"$ref": "#/definitions/condition"},
                },
            },
            "additionalProperties": False,
        },
        "condition": {
            "type": "object",
            "required": ["operator", "value"],
            "properties": {
                "field": {"type": "string"},
                "operator": {
                    "type": "string",
                    "enum": [
                        "contains",
                        "not_contains",
                        "equals",
                        "not_equals",
                        "bigger_than",
                        "smaller_than",
                    ],
                },
                "value": {},
            },
            "additionalProperties": False,
        },
        "for_each": {
            "type": "object",
            "required": ["from"],
            "properties": {
                "from": {"type": "string"},
                "field": {"type": "string"},
                "sub_field": {"type": "string"},
            },
            "additionalProperties": False,
        },
        "request": {
            "type": "object",
            "required": ["url"],
            "properties": {
                "method": {"type": "string", "default": "GET"},
                "url": {"type": "string"},
                "response_type": {"type": "string"},
                "headers": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                },
                "params": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                },
                "csrf_token": {"$ref": "#/definitions/csrf_token"},
            },
            "additionalProperties": False,
        },
        "csrf_token": {
            "type": "object",
            "required": ["url", "extract"],
            "properties": {
                "url": {"type": "string"},
                "method": {"type": "string", "default": "GET"},
                "extract": {"$ref": "#/definitions/extract"},
                "type": {"type": "string", "enum": ["text", "attribute"], "default": "text"},
                "attribute": {"type": "string"},
                "param_name": {"type": "string"},
                "header_name": {"type": "string"},
            },
            "additionalProperties": False,
        },
        "extract": {
            "type": "object",
            "required": ["selector"],
            "properties": {
                "selector": {"type": "string"},
                "selector_type": {
                    "type": "string",
                    "enum": ["css", "xpath", "jsonpath", "json"],
                    "default": "css",
                },
            },
            "additionalProperties": False,
        },
        "field": {
            "type": "object",
            "oneOf": [
                {
                    "type": "object",
                    "required": ["extract"],
                    "properties": {
                        "extract": {"$ref": "#/definitions/extract"},
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
                {
                    "type": "object",
                    "required": ["fields"],
                    "properties": {
                        "extract": {"$ref": "#/definitions/extract"},
                        "fields": {
                            "type": "object",
                            "additionalProperties": {"$ref": "#/definitions/field"},
                        },
                    },
                    "additionalProperties": False,
                },
            ],
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
    def load_from_file(filepath: str | PathLike[str]) -> dict[str, Any]:
        """Load and validate a scraper configuration from a JSON file."""
        try:
            with Path(filepath).open(encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError as e:
            msg = f"Configuration file not found: {filepath}"
            raise ConfigValidationError(msg) from e
        except json.JSONDecodeError as e:
            msg = f"Invalid JSON in configuration file '{filepath}': {e}"
            raise ConfigValidationError(msg) from e
        return ConfigLoader.load_from_dict(data)
