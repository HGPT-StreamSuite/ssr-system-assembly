"""Fresh synthetic repository fixtures; no production files or sockets are used."""
from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import validate_local as validator


class InvalidSpecificationTests(unittest.TestCase):
    def fixture(self, schema=None, example=None):
        sandbox = ROOT / ".test-temp"
        sandbox.mkdir(exist_ok=True)
        root = Path(tempfile.mkdtemp(prefix="native-spec-", dir=sandbox))
        (root / "contracts" / "schemas").mkdir(parents=True)
        (root / "contracts" / "examples").mkdir()
        (root / "docs").mkdir()
        (root / "contracts" / "schemas" / "synthetic.schema.json").write_text(
            json.dumps(schema if schema is not None else {"type": "object"}), encoding="utf-8")
        (root / "contracts" / "examples" / "synthetic.json").write_text(
            json.dumps(example if example is not None else {}), encoding="utf-8")
        (root / "docs" / "repo-catalog.md").write_text(
            "\n".join(f"| `{name}` | synthetic |" for name in sorted(validator.ACTIVE_REPOS)), encoding="utf-8")
        (root / "docs" / "architecture.md").write_text(
            "flowchart conversation-context conversation-store answer-context 純 repo 依賴圖", encoding="utf-8")
        # Retain only our new synthetic fixtures as inspectable acceptance artifacts.
        return root

    def test_illegal_schema_shapes_return_errors_without_exceptions(self):
        invalid = [None, [], False, {"type": {}}, {"type": []}, {"type": ["string", {}]},
                   {"type": "unsupported"}, {"required": True}, {"required": "name"},
                   {"required": [{}]}, {"properties": []}, {"properties": {"name": []}},
                   {"items": False}, {"enum": "ok"}, {"enum": []},
                   {"additionalProperties": {}}, {"additionalProperties": 1}]
        for schema in invalid:
            with self.subTest(schema=schema):
                self.assertTrue(validator.validate_schema_shape(schema, "synthetic-schema"))
                self.assertTrue(any("invalid schema" in e for e in validator.validate_document({}, schema)))

    def test_unsupported_constraints_and_references_are_not_silently_ignored(self):
        for keyword, value in (("minLength", 5), ("$ref", "https://synthetic.invalid/schema"), ("anyOf", [])):
            with self.subTest(keyword=keyword):
                errors = validator.validate_document("", {"type": "string", keyword: value})
                self.assertTrue(any(f"unsupported schema keyword {keyword}" in e for e in errors))

    def test_required_property_declarations_and_duplicates_are_checked(self):
        self.assertTrue(validator.validate_schema_shape({"required": ["missing"]}, "synthetic"))
        errors = validator.validate_schema_shape({"properties": {"name": {}}, "required": ["name", "name"]}, "synthetic")
        self.assertTrue(any("unique" in e for e in errors))

    def test_valid_union_null_boolean_integer_and_metadata(self):
        schema = {"type": ["string", "null"], "title": "synthetic", "description": "annotation only"}
        self.assertEqual(validator.validate_document(None, schema), [])
        self.assertEqual(validator.validate_document("", schema), [])
        self.assertTrue(validator.validate_document(True, {"type": "integer"}))
        self.assertEqual(validator.validate_document(True, {"type": "boolean"}), [])
        self.assertEqual(validator.validate_document(0, {"type": "integer"}), [])
        self.assertTrue(validator.validate_document(None, {"type": "object"}))

    def test_json_enum_and_integer_semantics_do_not_confuse_booleans_and_numbers(self):
        self.assertTrue(validator.validate_document(True, {"enum": [1]}))
        self.assertTrue(validator.validate_document({"x": [True]}, {"enum": [{"x": [1]}]}))
        self.assertEqual(validator.validate_document(1.0, {"type": "integer", "enum": [1]}), [])
        self.assertTrue(validator.validate_document(1.5, {"type": "integer"}))
        self.assertTrue(validator.validate_document(float("inf"), {"type": "number"}))
        self.assertTrue(validator.validate_schema_shape({"enum": [1, 1.0]}, "synthetic"))
        self.assertEqual(validator.validate_schema_shape({"enum": [True, 1]}, "synthetic"), [])
        self.assertTrue(validator.validate_schema_shape({"type": ["string", "string"]}, "synthetic"))

    def test_excessive_schema_nesting_is_an_error(self):
        schema = {}
        for _ in range(70):
            schema = {"type": "array", "items": schema}
        self.assertTrue(any("exceeds 64" in e for e in validator.validate_document([], schema)))

    def test_invalid_schema_stops_example_validation_but_does_not_crash(self):
        root = self.fixture({"type": "object", "required": True})
        errors = validator.validate_repository(root)
        self.assertTrue(any("required: must be an array" in e for e in errors))
        self.assertTrue(any("document was not validated" in e for e in errors))

    def test_empty_schema_and_example_directories_cannot_pass(self):
        sandbox = ROOT / ".test-temp"
        sandbox.mkdir(exist_ok=True)
        root = Path(tempfile.mkdtemp(prefix="native-empty-", dir=sandbox))
        errors = validator.validate_repository(root)
        self.assertIn("contracts/schemas: no schema files found", errors)
        self.assertIn("contracts/examples: no example files found", errors)

    def test_bad_json_encoding_and_nonfinite_numbers_are_rejected(self):
        for raw in (b"{broken", b"\xff", b"NaN", b"Infinity", b"1e400"):
            with self.subTest(raw=raw):
                root = self.fixture()
                (root / "contracts" / "examples" / "synthetic.json").write_bytes(raw)
                errors = validator.validate_repository(root)
                self.assertTrue(any("cannot read JSON" in e for e in errors))

    def test_native_main_reports_failure_then_recovers_on_owned_fixture(self):
        root = self.fixture({"type": "object", "required": True})
        before_source = (ROOT / "contracts" / "examples" / "chat-event.json").read_bytes()
        output = io.StringIO()
        with patch.object(validator, "ROOT", root), patch.object(validator, "SCHEMA_DIR", root / "contracts" / "schemas"), patch.object(validator, "EXAMPLE_DIR", root / "contracts" / "examples"), contextlib.redirect_stdout(output):
            self.assertEqual(validator.main(), 1)
            (root / "contracts" / "schemas" / "synthetic.schema.json").write_text('{"type":"object"}', encoding="utf-8")
            self.assertEqual(validator.main(), 0)
        self.assertIn("ERROR:", output.getvalue())
        self.assertIn("Validated 1 schemas and 1 local examples.", output.getvalue())
        self.assertEqual(before_source, (ROOT / "contracts" / "examples" / "chat-event.json").read_bytes())

    def test_corrupt_documentation_is_a_diagnostic_not_a_traceback(self):
        root = self.fixture()
        (root / "docs" / "architecture.md").write_bytes(b"\xff")
        self.assertTrue(any("docs/architecture.md: cannot read" in e for e in validator.validate_repository(root)))

    def test_null_example_obeys_its_real_schema(self):
        root = self.fixture({"type": "null"})
        (root / "contracts" / "examples" / "synthetic.json").write_text("null", encoding="utf-8")
        self.assertEqual(validator.validate_repository(root), [])
        (root / "contracts" / "schemas" / "synthetic.schema.json").write_text('{"type":"object"}', encoding="utf-8")
        self.assertTrue(any("expected one of" in e for e in validator.validate_repository(root)))


if __name__ == "__main__":
    unittest.main()
