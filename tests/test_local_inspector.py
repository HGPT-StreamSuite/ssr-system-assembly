from __future__ import annotations

import http.client
import io
import json
import os
import sys
import threading
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from local_inspector import (MAX_BODY_BYTES, InspectorHandler, RequestError, ThreadingHTTPServer,
                             catalog, evidence_matches, source_snapshot, validate_input)
from validate_local import validate_document


class InspectorValidationTests(unittest.TestCase):
    def test_all_eight_examples_use_the_existing_validator(self):
        entries = catalog()
        self.assertEqual(len(entries), 8)
        for entry in entries:
            with self.subTest(schema=entry["id"]):
                result = validate_input({"schema_id": entry["id"], "document": entry["example"]})
                self.assertEqual(result["errors"], validate_document(entry["example"], entry["schema"]))
                self.assertEqual(result["status"], "pass")

    def test_missing_message_id_reports_the_actual_field(self):
        result = validate_input({"schema_id": "chat-event", "document": {}})
        self.assertEqual(result["status"], "fail")
        self.assertIn("$.message_id: required", result["errors"])

    def test_query_extra_field_is_rejected(self):
        result = validate_input({"schema_id": "query-result", "document": {
            "status": "ok", "materials": [], "sources": [], "diagnostic": "synthetic"}})
        self.assertEqual(result["errors"], ["$.diagnostic: additional property is not allowed"])

    def test_empty_id_is_a_documented_schema_limit(self):
        entry = next(item for item in catalog() if item["id"] == "chat-event")
        entry["example"]["message_id"] = ""
        self.assertEqual(validate_input({"schema_id": "chat-event", "document": entry["example"]})["status"], "pass")

    def test_repeat_input_is_deterministic_and_not_stored(self):
        before = source_snapshot()["source_fingerprint"]
        payload = {"schema_id": "query-result", "document": {
            "status": "ok", "materials": [{"text": "SYNTHETIC-DO-NOT-STORE-901"}], "sources": []}}
        first, second = validate_input(payload), validate_input(payload)
        for key in ("status", "errors", "input_sha256"):
            self.assertEqual(first[key], second[key])
        self.assertNotEqual(first["request_id"], second["request_id"])
        self.assertNotIn("SYNTHETIC-DO-NOT-STORE-901", json.dumps(first))
        self.assertEqual(before, source_snapshot()["source_fingerprint"])

    def test_unknown_schema_and_path_are_rejected(self):
        for schema in ("../README", "unknown", [], None):
            with self.subTest(schema=schema), self.assertRaises(RequestError) as caught:
                validate_input({"schema_id": schema, "document": {}})
            self.assertEqual(caught.exception.status, 404)

    def test_request_shape_depth_and_nonfinite_are_rejected(self):
        nested = []
        for _ in range(33):
            nested = [nested]
        for payload in ({}, [], {"schema_id": "chat-event", "document": {}, "path": "x"},
                        {"schema_id": "chat-event", "document": nested},
                        {"schema_id": "chat-event", "document": float("inf")}):
            with self.subTest(payload_type=type(payload).__name__), self.assertRaises(RequestError):
                validate_input(payload)

    def test_evidence_requires_matching_head_branch_and_source(self):
        current = {"head": "synthetic-head", "branch": "synthetic-branch", "source_fingerprint": "synthetic-digest"}
        self.assertTrue(evidence_matches(dict(current), current))
        for key in current:
            changed = dict(current, **{key: "different"})
            self.assertFalse(evidence_matches(changed, current))
        self.assertFalse(evidence_matches(None, current))
        self.assertFalse(evidence_matches({}, current))


class InspectorHandlerTests(unittest.TestCase):
    """Exercise real request parsing/routing with memory streams, not network sockets."""
    port = 8872

    def request(self, method, path, body=None, headers=None):
        body = body or b""
        headers = {"Host": f"127.0.0.1:{self.port}", "Content-Length": str(len(body)), **(headers or {})}
        raw = (f"{method} {path} HTTP/1.0\r\n" + "".join(f"{k}: {v}\r\n" for k, v in headers.items()) + "\r\n").encode("ascii") + body

        class MemoryConnection:
            def __init__(self):
                self.input = io.BytesIO(raw)
                self.output = io.BytesIO()

            def makefile(self, *_args, **_kwargs):
                return self.input

            def settimeout(self, _value):
                pass

            def sendall(self, data):
                self.output.write(data)

        connection = MemoryConnection()
        InspectorHandler(connection, ("127.0.0.1", 0), SimpleNamespace(server_port=self.port))
        head, data = connection.output.getvalue().split(b"\r\n\r\n", 1)
        lines = head.decode("ascii").split("\r\n")
        return int(lines[0].split()[1]), dict(line.split(": ", 1) for line in lines[1:]), data

    def post(self, path, payload, headers=None):
        return self.request("POST", path, json.dumps(payload).encode("utf-8"),
                            {"Content-Type": "application/json", **(headers or {})})

    def test_page_assets_and_acceptance_document_are_real(self):
        for path, fragment in (("/", b"json-input"), ("/app.js", b"createRequestSession"),
                               ("/styles.css", b"@media"), ("/acceptance.md", b"CASE-10")):
            with self.subTest(path=path):
                status, headers, body = self.request("GET", path)
                self.assertEqual(status, 200)
                self.assertIn(fragment, body)
                self.assertEqual(headers["Cache-Control"], "no-store")
                self.assertIn("frame-ancestors 'none'", headers["Content-Security-Policy"])
                self.assertNotIn("Access-Control-Allow-Origin", headers)

    def test_catalog_and_safe_snapshot(self):
        status, _, body = self.request("GET", "/api/catalog")
        value = json.loads(body)
        self.assertEqual(status, 200)
        self.assertEqual(len(value["contracts"]), 8)
        self.assertEqual(value["common_standard"]["assessment"], "blocked")
        self.assertTrue(value["common_standard"]["specification_received"])
        self.assertFalse(value["common_standard"]["default_browser_verified"])
        self.assertEqual(len(value["snapshot"]["source_fingerprint"]), 64)
        self.assertNotIn(str(ROOT), body.decode())

    def test_actual_validation_and_repo_check(self):
        status, _, body = self.post("/api/validate", {"schema_id": "query-result", "document": {
            "status": "no_data", "materials": [], "sources": []}})
        self.assertEqual(status, 200)
        value = json.loads(body)
        self.assertEqual(value["status"], "pass")
        self.assertEqual(value["assessment_scope"], "repo_function_case_only")
        self.assertEqual(value["common_standard"]["assessment"], "blocked")
        status, _, body = self.post("/api/check", {})
        value = json.loads(body)
        self.assertEqual((status, value["status"], value["schemas"], value["examples"]), (200, "pass", 8, 8))
        self.assertEqual(value["common_standard"]["assessment"], "blocked")

    def test_malformed_empty_and_nonfinite_json(self):
        for body in (b"", b"{broken", b'{"schema_id":"chat-event","document":NaN}', b"\xff"):
            with self.subTest(body=body):
                status, _, data = self.request("POST", "/api/validate", body, {"Content-Type": "application/json"})
                self.assertEqual(status, 400)
                self.assertEqual(json.loads(data)["status"], "error")
                self.assertNotIn(b"Traceback", data)

    def test_media_length_and_payload_limits(self):
        status, _, _ = self.request("POST", "/api/validate", b"{}", {"Content-Type": "text/plain"})
        self.assertEqual(status, 415)
        for header, expected in (({"Content-Length": "invalid"}, 400), ({"Transfer-Encoding": "chunked"}, 400)):
            status, _, _ = self.request("POST", "/api/validate", b"{}", {"Content-Type": "application/json", **header})
            self.assertEqual(status, expected)
        status, _, _ = self.request("POST", "/api/validate", b"x" * (MAX_BODY_BYTES + 1), {"Content-Type": "application/json"})
        self.assertEqual(status, 413)

    def test_host_and_origin_are_restricted(self):
        for headers in ({"Host": "elsewhere.invalid"}, {"Origin": "https://elsewhere.invalid"}, {"Origin": "null"}):
            with self.subTest(headers=headers):
                self.assertEqual(self.post("/api/check", {}, headers)[0], 403)
        local = {"Origin": f"http://127.0.0.1:{self.port}"}
        self.assertEqual(self.post("/api/check", {}, local)[0], 200)

    def test_arbitrary_files_queries_and_operations_are_not_exposed(self):
        for path in ("/.git/config", "/../README.md", "/secrets", "/%2e%2e/README.md", "/api/catalog?file=README"):
            with self.subTest(path=path):
                self.assertEqual(self.request("GET", path)[0], 404)
        self.assertEqual(self.post("/api/run-shell", {})[0], 404)
        self.assertEqual(self.post("/api/check", {"path": "../other-repo"})[0], 400)

    def test_evidence_is_readable_and_head_has_no_body(self):
        status, _, body = self.request("GET", "/api/evidence")
        self.assertEqual(status, 200)
        self.assertIn(json.loads(body)["status"], ("collected", "not_collected"))
        self.assertEqual(json.loads(body)["common_standard"]["status"], "defined")
        status, headers, body = self.request("HEAD", "/")
        self.assertEqual(status, 200)
        self.assertGreater(int(headers["Content-Length"]), 0)
        self.assertEqual(body, b"")

class InspectorProtocolBoundaryTests(unittest.TestCase):
    """Malformed framing uses memory streams; never send these via a real socket."""
    def setUp(self):
        self.probe = InspectorHandlerTests("test_actual_validation_and_repo_check")
        self.port = self.probe.port

    def request(self, *args, **kwargs):
        return self.probe.request(*args, **kwargs)

    def post(self, *args, **kwargs):
        return self.probe.post(*args, **kwargs)

    def test_incomplete_body_and_duplicate_headers_are_rejected_then_recover(self):
        for headers, expected in (({"Content-Length": "10"}, 400),
                                  ({"Content-Length": "2\r\nContent-Length: 2"}, 400),
                                  ({"Host": f"127.0.0.1:{self.port}\r\nHost: synthetic.invalid"}, 403),
                                  ({"Origin": f"http://127.0.0.1:{self.port}\r\nOrigin: https://synthetic.invalid"}, 403)):
            with self.subTest(headers=headers):
                status, _, _ = self.request("POST", "/api/check", b"{}", {"Content-Type": "application/json", **headers})
                self.assertEqual(status, expected)
        status, _, body = self.post("/api/check", {})
        self.assertEqual((status, json.loads(body)["status"]), (200, "pass"))

    def test_arbitrary_command_path_endpoint_or_acl_fields_are_not_accepted(self):
        for key in ("command", "python_path", "database", "file", "endpoint", "acl", "purpose"):
            with self.subTest(key=key):
                status, _, _ = self.post("/api/validate", {"schema_id": "query-result", "document": {}, key: "synthetic-denied-value"})
                self.assertEqual(status, 400)

    def test_invalid_local_spec_is_safe_error_then_builtin_validation_recovers(self):
        sandbox = ROOT / ".test-temp"
        sandbox.mkdir(exist_ok=True)
        isolated = Path(tempfile.mkdtemp(prefix="native-handler-", dir=sandbox))
        (isolated / "contracts" / "schemas").mkdir(parents=True)
        (isolated / "contracts" / "examples").mkdir()
        (isolated / "contracts" / "schemas" / "synthetic.schema.json").write_text('{"required":true}', encoding="utf-8")
        (isolated / "contracts" / "examples" / "synthetic.json").write_text('{}', encoding="utf-8")
        with patch("local_inspector.ROOT", isolated):
            status, _, body = self.request("GET", "/api/catalog")
            self.assertEqual(status, 500)
            self.assertNotIn(b"Traceback", body)
            self.assertNotIn(str(isolated).encode(), body)
        status, _, body = self.post("/api/validate", {"schema_id": "query-result", "document": {"status": "ok", "materials": [], "sources": []}})
        self.assertEqual((status, json.loads(body)["status"]), (200, "pass"))


@unittest.skipUnless(os.environ.get("ASSEMBLY_RUN_SOCKET_TESTS") == "1",
                     "Real loopback HTTP is opt-in; current environment denied socket connect (WinError 10013).")
class InspectorLoopbackTests(InspectorHandlerTests):
    """Only enable after socket policy is resolved; do not use this to retry a denial."""
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), InspectorHandler)
        cls.port = cls.server.server_port
        cls.blocked = None
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def request(self, method, path, body=None, headers=None):
        if self.__class__.blocked:
            raise unittest.SkipTest(self.__class__.blocked)
        client = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            client.request(method, path, body=body, headers=headers or {})
            response = client.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        except PermissionError as exc:
            self.__class__.blocked = f"Socket denied; no more connection attempts: {exc}"
            raise unittest.SkipTest(self.__class__.blocked) from None
        finally:
            client.close()


if __name__ == "__main__":
    unittest.main()
