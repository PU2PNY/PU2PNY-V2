#!/usr/bin/env python3
"""PU2PNY-V2 TEST-2 backend: TEST-1 backend + the /api/system full-report action.

TEST build. NOT approved; nothing hardware-verified.

Adds a read-only diagnostic report so the owner can send logs to root-cause the
YSF-no-audio issue: POST /api/system {action:"full-report"} returns a downloadable
text report with the selected protocol, service states, and local UDP sockets.
Raw configuration and journal output are excluded.
"""
from pathlib import Path
import subprocess
import sys

repo = Path(__file__).resolve().parents[1]
out = Path(sys.argv[1]).resolve()
arch = sys.argv[2]
subprocess.run([sys.executable, str(repo / 'ci/prepare-v2-backend.py'), str(out), arch], check=True)
main = out / 'main.go'
source = main.read_text()

anchor = '\tcase "reboot":'
assert source.count(anchor) == 1, 'reboot case anchor not unique'
case = (
    '\tcase "full-report":\n'
    '\t\tw.Header().Set("Cache-Control", "no-store")\n'
    '\t\twriteJSON(w, 200, map[string]any{"ok": true, "report": buildFullReport(r.Context()), '
    '"generated": time.Now().UTC().Format(time.RFC3339)})\n'
    '\t\treturn\n'
)
source = source.replace(anchor, case + anchor, 1)
if sys.argv[3:] == ["--buildroot"]:
    update_handler = "func updateStatusHandler("
    assert source.count(update_handler) == 1, 'review the inherited update handler'
    source = source.replace(update_handler, "func legacyUpdateStatusHandler(", 1)
    for name in ("update.go", "update_test.go"):
        (out / name).write_bytes((repo / "runtime/v2" / name).read_bytes())
elif sys.argv[3:]:
    raise SystemExit("Unknown V2 backend option")

main.write_text(source)

(out / 'web_v2report.go').write_bytes((repo / 'runtime/v2/full-report.go').read_bytes())
print("PREPARE_V2_TEST2_BACKEND_OK", arch)
