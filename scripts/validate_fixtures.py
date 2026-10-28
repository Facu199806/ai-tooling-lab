#!/usr/bin/env python3
"""Validate deterministic synthetic fixture integrity without external packages."""
import hashlib
import json
from pathlib import Path

directory = Path(__file__).resolve().parent.parent / "fixtures"
manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
assert manifest["synthetic"] is True
for name, expected in manifest["files"].items():
    data = (directory / name).read_bytes()
    assert hashlib.sha256(data).hexdigest() == expected["sha256"], name
    assert len(data) == expected["bytes"], name
assert len(manifest["files"]) == 3
print("PASS: 3 synthetic fixtures, hashes and byte lengths verified")
