from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "contracts" / "schemas"
EXAMPLE_DIR = ROOT / "contracts" / "examples"
ALLOWED_TYPES = {"object", "array", "string", "integer", "number", "boolean", "null"}
ACTIVE_REPOS = {"ssr-chat", "ssr-knowledge", "ssr-system-assembly"}
EXAMPLE_TO_SCHEMA = {"transcript-segment-reserved": "transcript-segment"}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _matches_type(value: Any, expected: str) -> bool:
    checks = {
        "object": lambda item: isinstance(item, dict),
        "array": lambda item: isinstance(item, list),
        "string": lambda item: isinstance(item, str),
        "integer": lambda item: isinstance(item, int) and not isinstance(item, bool),
        "number": lambda item: isinstance(item, (int, float)) and not isinstance(item, bool),
        "boolean": lambda item: isinstance(item, bool),
        "null": lambda item: item is None,
    }
    return checks[expected](value)


def validate_document(value: Any, schema: dict[str, Any], location: str = "$") -> list[str]:
    errors: list[str] = []
    expected = schema.get("type")
    if expected:
        options = expected if isinstance(expected, list) else [expected]
        if not any(_matches_type(value, option) for option in options):
            return [f"{location}: expected one of {options}"]
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{location}: value is outside enum")
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{location}.{key}: required")
        properties = schema.get("properties", {})
        for key, child in value.items():
            if key in properties:
                errors.extend(validate_document(child, properties[key], f"{location}.{key}"))
            elif schema.get("additionalProperties") is False:
                errors.append(f"{location}.{key}: additional property is not allowed")
    if isinstance(value, list) and "items" in schema:
        for index, child in enumerate(value):
            errors.extend(validate_document(child, schema["items"], f"{location}[{index}]"))
    return errors


def validate_schema_shape(schema: Any, location: str) -> list[str]:
    if not isinstance(schema, dict):
        return [f"{location}: schema must be an object"]
    errors: list[str] = []
    expected = schema.get("type")
    options = expected if isinstance(expected, list) else [expected] if expected else []
    if any(option not in ALLOWED_TYPES for option in options):
        errors.append(f"{location}: unsupported type declaration {expected}")
    properties = schema.get("properties", {})
    if not isinstance(properties, dict):
        errors.append(f"{location}.properties: must be an object")
        properties = {}
    for key in schema.get("required", []):
        if key not in properties:
            errors.append(f"{location}.required: {key} has no property declaration")
    for key, child in properties.items():
        errors.extend(validate_schema_shape(child, f"{location}.properties.{key}"))
    if "items" in schema:
        errors.extend(validate_schema_shape(schema["items"], f"{location}.items"))
    return errors


def validate_repository(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    schema_dir = root / "contracts" / "schemas"
    example_dir = root / "contracts" / "examples"
    schemas: dict[str, dict[str, Any]] = {}
    for path in sorted(schema_dir.glob("*.schema.json")):
        try:
            schema = load_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path.relative_to(root)}: cannot read JSON: {exc}")
            continue
        errors.extend(validate_schema_shape(schema, str(path.relative_to(root))))
        schemas[path.name.removesuffix(".schema.json")] = schema

    examples_seen: set[str] = set()
    for path in sorted(example_dir.glob("*.json")):
        try:
            value = load_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path.relative_to(root)}: cannot read JSON: {exc}")
            continue
        stem = path.stem
        schema_name = EXAMPLE_TO_SCHEMA.get(stem, stem)
        schema = schemas.get(schema_name)
        if schema is None:
            errors.append(f"{path.relative_to(root)}: no matching schema {schema_name}")
            continue
        examples_seen.add(schema_name)
        errors.extend(validate_document(value, schema, f"{path.relative_to(root)}"))

    missing_examples = set(schemas) - examples_seen
    if missing_examples:
        errors.append(f"schemas without examples: {', '.join(sorted(missing_examples))}")

    catalog_path = root / "docs" / "repo-catalog.md"
    try:
        catalog = catalog_path.read_text(encoding="utf-8")
        listed = set(re.findall(r"^\| `([^`]+)` \|", catalog, flags=re.MULTILINE))
        if listed != ACTIVE_REPOS:
            errors.append(f"active repo catalog mismatch: expected {sorted(ACTIVE_REPOS)}, got {sorted(listed)}")
    except OSError as exc:
        errors.append(f"docs/repo-catalog.md: cannot read: {exc}")

    architecture_path = root / "docs" / "architecture.md"
    try:
        architecture = architecture_path.read_text(encoding="utf-8")
        for required in ("flowchart", "conversation-context", "conversation-store", "answer-context", "純 repo 依賴圖"):
            if required not in architecture:
                errors.append(f"docs/architecture.md: missing {required}")
    except OSError as exc:
        errors.append(f"docs/architecture.md: cannot read: {exc}")

    return errors


def main() -> int:
    errors = validate_repository()
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"Validated {len(list(SCHEMA_DIR.glob('*.schema.json')))} schemas and {len(list(EXAMPLE_DIR.glob('*.json')))} local examples.")
    print("Repo catalog and architecture markers are consistent. No other repository was read or executed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
