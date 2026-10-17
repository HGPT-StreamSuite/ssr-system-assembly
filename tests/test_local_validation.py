from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from validate_local import load_json, validate_document, validate_repository  # noqa: E402


class LocalAssemblyValidationTests(unittest.TestCase):
    def test_all_local_contract_examples_and_docs_validate(self) -> None:
        self.assertEqual(validate_repository(ROOT), [])

    def test_snapshot_requires_the_message_fields_needed_by_context(self) -> None:
        schema = load_json(ROOT / "contracts" / "schemas" / "context-snapshot.schema.json")
        invalid = {
            "snapshot_id": "snapshot-001",
            "conversation_id": "room-001",
            "messages": [{"message_id": "message-000", "text": "prior"}],
        }
        errors = validate_document(invalid, schema)
        self.assertTrue(any("author_id: required" in error for error in errors))
        self.assertTrue(any("created_at: required" in error for error in errors))

    def test_query_contract_has_only_materials_sources_and_status(self) -> None:
        schema = load_json(ROOT / "contracts" / "schemas" / "query-result.schema.json")
        example = load_json(ROOT / "contracts" / "examples" / "query-result.json")
        self.assertEqual(validate_document(example, schema), [])
        example["diagnostic"] = "internal detail"
        errors = validate_document(example, schema)
        self.assertTrue(any("additional property is not allowed" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
