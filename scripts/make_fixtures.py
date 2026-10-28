#!/usr/bin/env python3
"""Generate deterministic, entirely synthetic fixtures. Stdlib only.

No production logs, secrets, usernames, private code or provider credentials.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "fixtures"
OUT.mkdir(parents=True, exist_ok=True)

fixtures = {
    "http-events.json": {
        "case": "fictional-api",
        "events": [
            {"seq": 1, "request_id": "SYN-REQ-001", "status": 200, "note": "success"},
            {"seq": 2, "request_id": "SYN-REQ-002", "status": 429, "note": "retry-after=7"},
            {"seq": 3, "request_id": "SYN-REQ-003", "status": 500, "note": "do not retry without idempotency key"},
            {"seq": 4, "request_id": "SYN-REQ-004", "status": 200, "note": "not the same response as seq=1"},
        ],
        "synthetic_token": "CANARY_NOT_A_REAL_SECRET_90210",
    },
    "oracle-style.log": (
        "2026-01-01T00:00:01Z SYN-REQ-001 HTTP=200 rows=17\n"
        "2026-01-01T00:00:02Z SYN-REQ-002 ORA-01722 invalid number (fictional)\n"
        "2026-01-01T00:00:03Z SYN-REQ-003 HTTP=500 rollback required\n"
        "2026-01-01T00:00:04Z SYN-REQ-004 HTTP=200 no duplicate commit\n"
    ),
    "flutter-style.log": (
        "00:00 +001: synthetic widget test PASS\n"
        "00:01 +002: synthetic voice cancellation test PASS\n"
        "00:02 +003: synthetic accessibility test FAIL: expected focus 2 got 3\n"
        "00:03 +004: synthetic regression test SKIPPED\n"
    ),
}
manifest = {"synthetic": True, "files": {}}
for name, value in fixtures.items():
    body = (json.dumps(value, sort_keys=True, ensure_ascii=True, indent=2) + "\n") if isinstance(value, dict) else value
    data = body.encode("utf-8")
    (OUT / name).write_bytes(data)
    manifest["files"][name] = {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
(OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("Generated 3 synthetic fixtures with SHA-256 manifest.")
