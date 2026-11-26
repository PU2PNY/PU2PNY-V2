#!/usr/bin/env python3
"""Software-only regression for staging the V2 panel on a fresh rootfs."""
import hashlib
import importlib.util
import tempfile
from pathlib import Path

here = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("v2_panel_overlay", here / "v2-panel-overlay.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
repo = here.parent
with tempfile.TemporaryDirectory(prefix="pny-v2-panel-") as temp:
    target = Path(temp)
    files = module.stage(target)
    assert len(files) == 15, ("missing panel assets", len(files))
    web = target / "usr/share/2pny"
    assert (web / "dashboard.html").is_file()
    assert (web / "ui-language.js").read_bytes() == (repo / "panel/ui-language.js").read_bytes()
    assert (web / "favicon.png").read_bytes() == (repo / "panel/favicon.png").read_bytes()
    for source, dest in module.PAGES.items():
        page = (web / dest).read_text()
        assert 'src="/ui-common-0.3.0.js"' in page, dest
        assert 'href="/ui-0.3.0.css"' in page, dest
        assert 'href="pny-v2.css"' not in page, dest
        assert 'href="index.html"' not in page, dest
    js = (web / "ui-common-0.3.0.js").read_text()
    assert "live:'/dashboard'" in js
    assert "sc.src='/ui-language.js'" in js
    for name, expected_sha in files.items():
        assert hashlib.sha256((target / name).read_bytes()).hexdigest() == expected_sha, name
    assert not (target / "usr/local/bin/2pnyd").exists(), "This step must never fake backend"
print("V2_PANEL_STAGE_SW_PASS_STATIC_ONLY")
