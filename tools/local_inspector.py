"""Loopback-only, read-only UI for this repository's existing validator."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from uuid import uuid4

from validate_local import MAX_SCHEMA_DEPTH, EXAMPLE_TO_SCHEMA, load_json, validate_document, validate_repository, validate_schema_shape

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
MAX_BODY_BYTES = 65_536
MAX_DEPTH = 32
MAX_RETURNED_ERRORS = 100
API_VERSION = "1"
COMMON_STANDARD = {
    "status": "defined",
    "specification_received": True,
    "definition": "網頁必須能在使用者的預設瀏覽器實際開啟並可操作、運作正常。",
    "assessment": "blocked",
    "default_browser_verified": False,
    "note": "所有 repo 採相同門檻；本輪必要 loopback 操作曾被拒，未取得預設瀏覽器實測證據。功能測例不替代此門檻。",
}
STATIC = {
    "/": (WEB / "index.html", "text/html; charset=utf-8"),
    "/app.js": (WEB / "app.js", "text/javascript; charset=utf-8"),
    "/styles.css": (WEB / "styles.css", "text/css; charset=utf-8"),
    "/acceptance.md": (ROOT / "docs" / "independent-acceptance.md", "text/plain; charset=utf-8"),
}


class RequestError(ValueError):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


def source_snapshot() -> dict:
    paths = {ROOT / "README.md", ROOT / ".gitignore"}
    for pattern in ("docs/*.md", "contracts/**/*.json", "contracts/*.md",
                    "tools/*.py", "tests/*.py", "tests/*.cjs", "web/*.html", "web/*.js", "web/*.css"):
        paths.update(ROOT.glob(pattern))
    manifest = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(paths, key=lambda item: item.relative_to(ROOT).as_posix()) if p.is_file()}
    canonical = "\n".join(f"{name}={digest}" for name, digest in manifest.items())
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")

    def git(*args: str):
        try:
            run = subprocess.run(["git", *args], cwd=ROOT, env=env, capture_output=True,
                                 text=True, encoding="utf-8", timeout=5, check=False)
            return run.stdout.rstrip("\r\n") if run.returncode == 0 else None
        except (OSError, subprocess.TimeoutExpired):
            return None

    dirty = git("status", "--porcelain=v1", "--untracked-files=all")
    return {"repo": "ssr-system-assembly", "head": git("rev-parse", "HEAD"),
            "branch": git("branch", "--show-current"),
            "dirty": dirty.splitlines() if dirty is not None else None,
            "source_fingerprint": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            "source_manifest": manifest,
            "fingerprint_scope": "repo source/docs/contracts/web; excludes web/evidence.json and test artifacts"}


def catalog() -> list[dict]:
    result = []
    for path in sorted((ROOT / "contracts" / "examples").glob("*.json")):
        schema_id = EXAMPLE_TO_SCHEMA.get(path.stem, path.stem)
        schema = load_json(ROOT / "contracts" / "schemas" / f"{schema_id}.schema.json")
        if validate_schema_shape(schema, schema_id):
            raise ValueError("Invalid local contract; no document validation was performed.")
        result.append({"id": schema_id, "title": schema.get("title", schema_id), "schema": schema,
                       "example": load_json(path),
                       "example_source": f"contracts/examples/{path.name}",
                       "reserved": schema_id == "transcript-segment"})
    return result


def evidence_matches(saved, current: dict) -> bool:
    return bool(isinstance(saved, dict) and current.get("head") and current.get("branch")
                and all(saved.get(key) == current.get(key)
                        for key in ("source_fingerprint", "head", "branch")))


def interface_manifest() -> dict:
    value = load_json(ROOT / "contracts" / "interfaces" / "local-inspector.v1.json")
    if not isinstance(value, dict) or value.get("interface_version") != API_VERSION or value.get("repo") != "ssr-system-assembly":
        raise ValueError("Invalid local interface manifest.")
    for name in ("validation_request_schema", "validation_response_schema", "error_response_schema"):
        if validate_schema_shape(value.get(name), name):
            raise ValueError("Invalid local interface schema.")
    expected_limits = {"request_bytes": MAX_BODY_BYTES, "request_depth": MAX_DEPTH,
                       "returned_errors": MAX_RETURNED_ERRORS, "schema_depth": MAX_SCHEMA_DEPTH}
    if value.get("limits") != expected_limits:
        raise ValueError("Interface limits do not match the native implementation.")
    routes = value.get("routes")
    if not isinstance(routes, list) or any(not isinstance(route, dict) or not isinstance(route.get("method"), str)
                                         or not isinstance(route.get("path"), str) for route in routes):
        raise ValueError("Invalid local interface route list.")
    return value


def check_depth(value) -> None:
    stack = [(value, 1)]
    while stack:
        item, depth = stack.pop()
        if depth > MAX_DEPTH:
            raise RequestError(f"JSON 深度超過 {MAX_DEPTH} 層。")
        if isinstance(item, dict):
            stack.extend((child, depth + 1) for child in item.values())
        elif isinstance(item, list):
            stack.extend((child, depth + 1) for child in item)


def validate_input(payload: dict) -> dict:
    if not isinstance(payload, dict) or set(payload) != {"schema_id", "document"}:
        raise RequestError("需要 schema_id 與 document，且不接受其他請求欄位。")
    schema_id = payload["schema_id"]
    schemas = {entry["id"]: entry for entry in catalog()}
    if not isinstance(schema_id, str) or schema_id not in schemas:
        raise RequestError("未知契約；只能選擇本 repo 的內建契約。", 404)
    check_depth(payload)
    document = payload["document"]
    try:
        serialized = json.dumps(document, ensure_ascii=True, sort_keys=True,
                                separators=(",", ":"), allow_nan=False)
    except (ValueError, TypeError):
        raise RequestError("輸入必須是有限數值的有效 JSON。") from None
    errors = validate_document(document, schemas[schema_id]["schema"])
    return {"api_version": API_VERSION, "status": "fail" if errors else "pass", "schema_id": schema_id,
            "errors": errors[:MAX_RETURNED_ERRORS], "error_count": len(errors), "errors_truncated": len(errors) > MAX_RETURNED_ERRORS,
            "input_sha256": hashlib.sha256(serialized.encode("utf-8")).hexdigest(),
            "mode": "local_python_schema_subset", "assessment_scope": "repo_function_case_only",
            "common_standard": dict(COMMON_STANDARD), "request_id": str(uuid4()),
            "observed_utc": datetime.now(timezone.utc).isoformat(), "snapshot": source_snapshot()}


class InspectorHandler(BaseHTTPRequestHandler):
    server_version = "AssemblyInspector"
    sys_version = ""

    def log_message(self, *_args):
        # Never log user input, request URLs or local environment details.
        pass

    def setup(self):
        super().setup()
        self.connection.settimeout(5)

    def _reply(self, status: int, value, content_type="application/json; charset=utf-8", *, head=False):
        if isinstance(value, dict):
            value = {**value, "api_version": API_VERSION}
        body = value if isinstance(value, bytes) else json.dumps(value, ensure_ascii=True, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'")
        self.end_headers()
        if not head:
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass  # A cancelled browser request has no data side effects.

    def _guard(self):
        port = self.server.server_port
        if len(self.headers.get_all("Host", [])) != 1 or len(self.headers.get_all("Origin", [])) > 1:
            raise RequestError("Host／Origin 標頭不得重複。", 403)
        host = self.headers.get("Host", "")
        allowed = {f"127.0.0.1:{port}", f"localhost:{port}"}
        if host not in allowed:
            raise RequestError("只接受本機 loopback Host。", 403)
        origin = self.headers.get("Origin")
        if origin is not None and origin != f"http://{host}":
            raise RequestError("不接受跨來源請求。", 403)

    def _body(self):
        if self.headers.get("Transfer-Encoding"):
            raise RequestError("不接受 Transfer-Encoding；請使用明確 Content-Length。")
        if len(self.headers.get_all("Content-Length", [])) > 1:
            raise RequestError("Content-Length 標頭不得重複。")
        if self.headers.get("Content-Type", "").split(";")[0].lower() != "application/json":
            raise RequestError("Content-Type 必須為 application/json。", 415)
        try:
            size = int(self.headers.get("Content-Length", "-1"))
        except ValueError:
            raise RequestError("Content-Length 不合法。") from None
        if size < 0:
            raise RequestError("需要明確的 Content-Length。", 411)
        if size > MAX_BODY_BYTES:
            raise RequestError("請求超過 64 KiB；只允許小型合成 JSON。", 413)

        def invalid_constant(_value):
            raise ValueError("non-finite number")

        try:
            raw = self.rfile.read(size)
            if len(raw) != size:
                raise RequestError("請求內容不完整，與 Content-Length 不符。")
            value = json.loads(raw.decode("utf-8"), parse_constant=invalid_constant)
            check_depth(value)
            return value
        except RequestError:
            raise
        except (ValueError, UnicodeError, RecursionError):
            raise RequestError("JSON 解析失敗；請檢查語法、深度與有限數值。") from None

    def do_GET(self, *, head=False):
        try:
            self._guard()
            if self.path in STATIC:
                path, content_type = STATIC[self.path]
                return self._reply(200, path.read_bytes(), content_type, head=head)
            if self.path == "/api/interface":
                value = {"interface": interface_manifest(), "snapshot": source_snapshot(),
                         "common_standard": dict(COMMON_STANDARD)}
            elif self.path == "/api/catalog":
                value = {"contracts": catalog(), "snapshot": source_snapshot(),
                         "common_standard": dict(COMMON_STANDARD),
                         "limits": {"body_bytes": MAX_BODY_BYTES, "depth": MAX_DEPTH}}
            elif self.path == "/api/evidence":
                path = WEB / "evidence.json"
                saved = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
                current = source_snapshot()
                value = {"status": "collected" if saved else "not_collected", "evidence": saved,
                         "common_standard": dict(COMMON_STANDARD),
                         "matches_current_source": evidence_matches(saved, current),
                         "snapshot": current}
            else:
                raise RequestError("找不到此路徑；不提供任意檔案讀取。", 404)
            self._reply(200, value, head=head)
        except RequestError as exc:
            self._reply(exc.status, {"status": "error", "error": str(exc)}, head=head)
        except (OSError, ValueError, RecursionError):
            self._reply(500, {"status": "error", "error": "本 repo 檔案無法讀取；請在終端檢查來源。"}, head=head)

    def do_HEAD(self):
        self.do_GET(head=True)

    def do_POST(self):
        try:
            self._guard()
            if self.path not in ("/api/validate", "/api/check"):
                raise RequestError("未知操作。", 404)
            payload = self._body()
            if self.path == "/api/validate":
                value = validate_input(payload)
            else:
                if payload != {}:
                    raise RequestError("本 repo 範例檢查不接受自訂路徑或參數。")
                errors = validate_repository(ROOT)
                value = {"status": "fail" if errors else "pass", "errors": errors,
                         "assessment_scope": "repo_function_case_only", "common_standard": dict(COMMON_STANDARD),
                         "schemas": len(list((ROOT / "contracts" / "schemas").glob("*.schema.json"))),
                         "examples": len(list((ROOT / "contracts" / "examples").glob("*.json"))),
                         "scope": "本 repo schema/examples、三 repo 清單及架構文字標記；不執行 unit tests。",
                         "request_id": str(uuid4()), "observed_utc": datetime.now(timezone.utc).isoformat(),
                         "snapshot": source_snapshot()}
            self._reply(200, value)
        except RequestError as exc:
            self._reply(exc.status, {"status": "error", "error": str(exc)})
        except (OSError, ValueError, RecursionError):
            self._reply(500, {"status": "error", "error": "本機驗證無法完成；沒有寫入或傳送資料。"})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8872)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    try:
        server = ThreadingHTTPServer(("127.0.0.1", args.port), InspectorHandler)
    except OSError as exc:
        print(f"Cannot start 127.0.0.1:{args.port}: {exc}. No alternate port was tried.", file=sys.stderr)
        return 1
    print(f"Assembly inspector: http://127.0.0.1:{server.server_port}/ (read-only, Ctrl+C to stop)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
