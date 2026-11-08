from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "contracts" / "schemas"
EXAMPLE_DIR = ROOT / "contracts" / "examples"
ALLOWED_TYPES = {"object", "array", "string", "integer", "number", "boolean", "null"}
ALLOWED_KEYWORDS = {"type", "required", "properties", "items", "enum", "additionalProperties",
                    "$schema", "$id", "$comment", "title", "description", "default", "examples"}
MAX_SCHEMA_DEPTH = 64
ACTIVE_REPOS = {"ssr-chat", "ssr-knowledge", "ssr-system-assembly"}
EXAMPLE_TO_SCHEMA = {"transcript-segment-reserved": "transcript-segment"}


def load_json(path: Path) -> Any:
    def invalid_constant(value: str):
        raise ValueError(f"non-finite JSON number: {value}")

    def finite_float(value: str):
        result = float(value)
        if not math.isfinite(result):
            raise ValueError("JSON number exceeds finite float range")
        return result

    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle, parse_constant=invalid_constant, parse_float=finite_float)


def _matches_type(value: Any, expected: str) -> bool:
    checks = {
        "object": lambda item: isinstance(item, dict),
        "array": lambda item: isinstance(item, list),
        "string": lambda item: isinstance(item, str),
        "integer": lambda item: (isinstance(item, int) and not isinstance(item, bool)) or (isinstance(item, float) and math.isfinite(item) and item.is_integer()),
        "number": lambda item: (isinstance(item, int) and not isinstance(item, bool)) or (isinstance(item, float) and math.isfinite(item)),
        "boolean": lambda item: isinstance(item, bool),
        "null": lambda item: item is None,
    }
    return checks[expected](value)


def _json_equal(left: Any, right: Any) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return isinstance(left, bool) and isinstance(right, bool) and left == right
    if left is None or right is None:
        return left is right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left == right
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(_json_equal(value, right[key]) for key, value in left.items())
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(_json_equal(a, b) for a, b in zip(left, right))
    return type(left) is type(right) and left == right


def validate_document(value: Any, schema: dict[str, Any], location: str = "$") -> list[str]:
    shape_errors = validate_schema_shape(schema, "schema")
    if shape_errors:
        return [f"{location}: invalid schema: {error}" for error in shape_errors]
    return _validate_document(value, schema, location)


def _validate_document(value: Any, schema: dict[str, Any], location: str) -> list[str]:
    errors: list[str] = []
    expected = schema.get("type")
    if expected:
        options = expected if isinstance(expected, list) else [expected]
        if not any(_matches_type(value, option) for option in options):
            return [f"{location}: expected one of {options}"]
    if "enum" in schema and not any(_json_equal(value, candidate) for candidate in schema["enum"]):
        errors.append(f"{location}: value is outside enum")
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{location}.{key}: required")
        properties = schema.get("properties", {})
        for key, child in value.items():
            if key in properties:
                errors.extend(_validate_document(child, properties[key], f"{location}.{key}"))
            elif schema.get("additionalProperties") is False:
                errors.append(f"{location}.{key}: additional property is not allowed")
    if isinstance(value, list) and "items" in schema:
        for index, child in enumerate(value):
            errors.extend(_validate_document(child, schema["items"], f"{location}[{index}]"))
    return errors


def validate_schema_shape(schema: Any, location: str, _depth: int = 0) -> list[str]:
    if _depth > MAX_SCHEMA_DEPTH:
        return [f"{location}: schema nesting exceeds {MAX_SCHEMA_DEPTH} levels"]
    if not isinstance(schema, dict):
        return [f"{location}: schema must be an object"]
    errors: list[str] = []
    for key in schema:
        if key not in ALLOWED_KEYWORDS:
            errors.append(f"{location}: unsupported schema keyword {key}")
    if "type" in schema:
        expected = schema["type"]
        options = expected if isinstance(expected, list) else [expected]
        if not options or any(not isinstance(option, str) or option not in ALLOWED_TYPES for option in options):
            errors.append(f"{location}: unsupported type declaration {expected}")
        elif len(set(options)) != len(options):
            errors.append(f"{location}.type: declarations must be unique")
    properties = schema.get("properties", {})
    if not isinstance(properties, dict):
        errors.append(f"{location}.properties: must be an object")
        properties = {}
    required = schema.get("required", [])
    if not isinstance(required, list) or any(not isinstance(key, str) for key in required):
        errors.append(f"{location}.required: must be an array of property names")
        required = []
    if len(set(required)) != len(required):
        errors.append(f"{location}.required: property names must be unique")
    for key in required:
        if key not in properties:
            errors.append(f"{location}.required: {key} has no property declaration")
    for key, child in properties.items():
        if not isinstance(key, str):
            errors.append(f"{location}.properties: names must be strings")
        errors.extend(validate_schema_shape(child, f"{location}.properties.{key}", _depth + 1))
    if "items" in schema:
        errors.extend(validate_schema_shape(schema["items"], f"{location}.items", _depth + 1))
    if "enum" in schema and (not isinstance(schema["enum"], list) or not schema["enum"]):
        errors.append(f"{location}.enum: must be a non-empty array")
    elif "enum" in schema:
        values = schema["enum"]
        if any(_json_equal(value, earlier) for index, value in enumerate(values) for earlier in values[:index]):
            errors.append(f"{location}.enum: values must be unique")
    if "additionalProperties" in schema and not isinstance(schema["additionalProperties"], bool):
        errors.append(f"{location}.additionalProperties: only boolean values are supported")
    return errors


def validate_repository(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    schema_dir = root / "contracts" / "schemas"
    example_dir = root / "contracts" / "examples"
    schemas: dict[str, dict[str, Any]] = {}
    invalid_schemas: set[str] = set()
    schema_paths = sorted(schema_dir.glob("*.schema.json"))
    example_paths = sorted(example_dir.glob("*.json"))
    if not schema_paths:
        errors.append("contracts/schemas: no schema files found")
    if not example_paths:
        errors.append("contracts/examples: no example files found")
    for path in schema_paths:
        schema_name = path.name.removesuffix(".schema.json")
        try:
            schema = load_json(path)
        except (OSError, ValueError, RecursionError) as exc:
            errors.append(f"{path.relative_to(root)}: cannot read JSON: {exc}")
            invalid_schemas.add(schema_name)
            continue
        shape_errors = validate_schema_shape(schema, str(path.relative_to(root)))
        errors.extend(shape_errors)
        if shape_errors:
            invalid_schemas.add(schema_name)
        else:
            schemas[schema_name] = schema

    examples_seen: set[str] = set()
    for path in example_paths:
        try:
            value = load_json(path)
        except (OSError, ValueError, RecursionError) as exc:
            errors.append(f"{path.relative_to(root)}: cannot read JSON: {exc}")
            continue
        stem = path.stem
        schema_name = EXAMPLE_TO_SCHEMA.get(stem, stem)
        if schema_name in invalid_schemas:
            examples_seen.add(schema_name)
            errors.append(f"{path.relative_to(root)}: matching schema is invalid; document was not validated")
            continue
        schema = schemas.get(schema_name)
        if schema is None:
            errors.append(f"{path.relative_to(root)}: no matching schema {schema_name}")
            continue
        examples_seen.add(schema_name)
        errors.extend(validate_document(value, schema, f"{path.relative_to(root)}"))

    missing_examples = (set(schemas) | invalid_schemas) - examples_seen
    if missing_examples:
        errors.append(f"schemas without examples: {', '.join(sorted(missing_examples))}")

    catalog_path = root / "docs" / "repo-catalog.md"
    try:
        catalog = catalog_path.read_text(encoding="utf-8")
        listed = set(re.findall(r"^\| `([^`]+)` \|", catalog, flags=re.MULTILINE))
        if listed != ACTIVE_REPOS:
            errors.append(f"active repo catalog mismatch: expected {sorted(ACTIVE_REPOS)}, got {sorted(listed)}")
    except (OSError, UnicodeError) as exc:
        errors.append(f"docs/repo-catalog.md: cannot read: {exc}")

    architecture_path = root / "docs" / "architecture.md"
    try:
        architecture = architecture_path.read_text(encoding="utf-8")
        for required in ("flowchart", "conversation-context", "conversation-store", "answer-context", "純 repo 依賴圖"):
            if required not in architecture:
                errors.append(f"docs/architecture.md: missing {required}")
    except (OSError, UnicodeError) as exc:
        errors.append(f"docs/architecture.md: cannot read: {exc}")

    return errors


def main() -> int:
    errors = validate_repository(ROOT)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"Validated {len(list(SCHEMA_DIR.glob('*.schema.json')))} schemas and {len(list(EXAMPLE_DIR.glob('*.json')))} local examples.")
    print("Repo catalog and architecture markers are consistent. No other repository was read or executed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
