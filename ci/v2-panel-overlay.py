#!/usr/bin/env python3
"""Stage the unchanged PU2PNY-V2 web panel for a fresh Buildroot rootfs.

This stages static assets only. It does NOT claim the backend/API/RF is present.
Do not publish the resulting filesystem as a full hotspot.
"""
import argparse
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PANEL = REPO / "panel"
PAGES = {
    "index.html": "dashboard.html", "hotspot.html": "hotspot.html",
    "internet.html": "internet.html", "direct.html": "direct.html",
    "aprs.html": "aprs.html", "history.html": "history.html",
    "display.html": "display.html", "system.html": "system.html",
    "expert.html": "expert.html",
}
ROUTES = {name: ("/dashboard" if name == "index.html" else "/" + name[:-5])
          for name in PAGES}


def safe_write(dest, payload):
    if dest.is_symlink() or (dest.exists() and not dest.is_file()):
        raise ValueError("Unsafe destination: " + str(dest))
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.parent.is_symlink():
        raise ValueError("Symlink parent: " + str(dest.parent))
    dest.write_bytes(payload)


def rewrite_page(text):
    for old, new in (
        ('src="ui-common.js"', 'src="/ui-common-0.3.0.js"'),
        ('href="ui.css"', 'href="/ui-0.3.0.css"'),
        ('<link rel="stylesheet" href="pny-v2.css">', ''),
        ('href="favicon.png"', 'href="/favicon.png"'),
        ('src="favicon.png"', 'src="/favicon.png"'),
        ('href="apple-touch-icon.png"', 'href="/apple-touch-icon.png"'),
        ('href="favicon-192.png"', 'href="/favicon-192.png"'),
    ):
        text = text.replace(old, new)
    for name, route in ROUTES.items():
        text = text.replace('href="' + name + '"', 'href="' + route + '"')
    return text


def rewrite_common(text):
    old = ("  var ROUTE={live:'index.html',internet:'internet.html',hotspot:'hotspot.html',direct:'direct.html',\n"
           "    aprs:'aprs.html',history:'history.html',display:'display.html',system:'system.html',expert:'expert.html'};")
    new = ("  var ROUTE={live:'/dashboard',internet:'/internet',hotspot:'/hotspot',direct:'/direct',\n"
           "    aprs:'/aprs',history:'/history',display:'/display',system:'/system',expert:'/expert'};")
    if text.count(old) != 1 or text.count("sc.src='ui-language.js'") != 1:
        raise ValueError("V2 panel routing contract changed; review manually")
    return text.replace(old, new, 1).replace("sc.src='ui-language.js'", "sc.src='/ui-language.js'", 1)


def stage(target):
    target = Path(target).resolve()
    if not target.is_dir() or target == Path("/"):
        raise ValueError("Target must be an existing staging rootfs, not /")
    root = target / "usr/share/2pny"
    records = {}
    def put(name, payload):
        dest = root / name
        safe_write(dest, payload)
        records["usr/share/2pny/" + name] = hashlib.sha256(payload).hexdigest()
    for source, dest in PAGES.items():
        put(dest, rewrite_page((PANEL / source).read_text()).encode())
    put("ui-common-0.3.0.js", rewrite_common((PANEL / "ui-common.js").read_text()).encode())
    put("ui-0.3.0.css", ((PANEL / "ui.css").read_text() + "\n" +
                             (PANEL / "pny-v2.css").read_text()).encode())
    put("ui-language.js", (PANEL / "ui-language.js").read_bytes())
    for asset in ("favicon.png", "apple-touch-icon.png", "favicon-192.png"):
        put(asset, (PANEL / asset).read_bytes())
    return records


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("staging_rootfs")
    args = parser.parse_args()
    records = stage(args.staging_rootfs)
    print(json.dumps({"status": "STATIC_PANEL_STAGED_NOT_BOOTABLE",
                      "files": records}, sort_keys=True, indent=2))
