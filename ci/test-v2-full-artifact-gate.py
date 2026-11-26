#!/usr/bin/env python3
"""Gate must reject an incomplete 'under 80 MB' image."""
import importlib.util
import json
import lzma
import tempfile
from pathlib import Path

src = Path(__file__).with_name("v2-full-artifact-gate.py")
spec = importlib.util.spec_from_file_location("v2_gate", src)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

with tempfile.TemporaryDirectory() as tmp:
    p = Path(tmp)
    image = p / "fake.img.xz"
    image.write_bytes(lzma.compress(b"not a bootable image"))
    root = p / "root"
    root.mkdir()
    evidence = p / "evidence.json"
    evidence.write_text(json.dumps({"checks": {}, "inventory_complete": False}))
    report, ok = m.verify(image, root, evidence)
    assert not ok
    assert report["under_80mb"] and report["xz"] == "PASS"
    assert report["classification"] == "NOT_DELIVERED"
    assert report["missing_files"] and report["failed_checks"]
print("V2_FULL_GATE_FAIL_CLOSED_PASS")
