"""Contract receipts use the fixed native adapter with no network or external source."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import local_inspector as app
from validate_local import validate_document
import test_local_inspector as inspector_tests


class NativeInterfaceContractTests(unittest.TestCase):
    def setUp(self):
        self.probe = inspector_tests.InspectorHandlerTests("test_actual_validation_and_repo_check")
        self.manifest = app.interface_manifest()

    def test_machine_readable_request_and_response_match_real_native_operation(self):
        request = self.manifest["synthetic_request_example"]
        self.assertEqual(validate_document(request, self.manifest["validation_request_schema"]), [])
        response = app.validate_input(request)
        self.assertEqual(validate_document(response, self.manifest["validation_response_schema"]), [])
        self.assertEqual(response["status"], "pass")
        self.assertEqual(response["api_version"], self.manifest["interface_version"])
        self.assertEqual(response["common_standard"]["assessment"], "blocked")

    def test_every_declared_route_executes_and_keeps_current_source_binding(self):
        expected = {("GET", "/api/interface"), ("GET", "/api/catalog"), ("GET", "/api/evidence"),
                    ("POST", "/api/validate"), ("POST", "/api/check")}
        self.assertEqual({(item["method"], item["path"]) for item in self.manifest["routes"]}, expected)
        fingerprint = app.source_snapshot()["source_fingerprint"]
        for method, route in sorted(expected):
            with self.subTest(method=method, route=route):
                if method == "GET":
                    status, _, raw = self.probe.request(method, route)
                else:
                    payload = self.manifest["synthetic_request_example"] if route == "/api/validate" else {}
                    status, _, raw = self.probe.post(route, payload)
                response = json.loads(raw)
                self.assertEqual(status, 200)
                self.assertEqual(response["api_version"], "1")
                self.assertEqual(response["snapshot"]["source_fingerprint"], fingerprint)
                self.assertEqual(response["common_standard"]["assessment"], "blocked")

    def test_real_rejections_match_error_envelope_without_loosening_purpose_or_acl(self):
        for route, payload, headers, expected in (
                ("/api/validate", {}, {}, 400),
                ("/api/validate", {"schema_id": "unknown", "document": {}}, {}, 404),
                ("/api/check", {}, {"Origin": "https://synthetic.invalid"}, 403),
                ("/api/validate", dict(self.manifest["synthetic_request_example"], purpose="synthetic", acl="allow"), {}, 400)):
            with self.subTest(expected=expected, payload=payload):
                status, _, raw = self.probe.post(route, payload, headers)
                self.assertEqual(status, expected)
                self.assertEqual(validate_document(json.loads(raw), self.manifest["error_response_schema"]), [])

    def test_invalid_interface_version_is_safe_error_and_fixed_interface_recovers(self):
        sandbox = ROOT / ".test-temp"
        sandbox.mkdir(exist_ok=True)
        isolated = Path(tempfile.mkdtemp(prefix="native-interface-", dir=sandbox))
        (isolated / "contracts" / "interfaces").mkdir(parents=True)
        (isolated / "contracts" / "interfaces" / "local-inspector.v1.json").write_text(
            '{"repo":"ssr-system-assembly","interface_version":"incompatible"}', encoding="utf-8")
        with patch.object(app, "ROOT", isolated):
            status, _, raw = self.probe.request("GET", "/api/interface")
            self.assertEqual(status, 500)
            self.assertEqual(validate_document(json.loads(raw), self.manifest["error_response_schema"]), [])
            self.assertNotIn(str(isolated).encode(), raw)
        status, _, raw = self.probe.request("GET", "/api/interface")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(raw)["interface"]["interface_version"], "1")

    def test_head_returns_only_headers_for_the_fixed_interface(self):
        status, headers, body = self.probe.request("HEAD", "/api/interface")
        self.assertEqual(status, 200)
        self.assertEqual(body, b"")
        self.assertGreater(int(headers["Content-Length"]), 0)


if __name__ == "__main__":
    unittest.main()
