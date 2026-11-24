#!/usr/bin/env python3
"""PU2PNY-V2 TEST backend: 5.15 backend + static routes the V2 panel needs.

The V2 panel (feat/panel-v2) ships favicon/apple-touch-icon images and is served
through the daemon's existing fixed asset routes. The stock daemon serves only
/ui-0.3.0.css, /ui-common-0.3.0.js and /ui-language.js plus the page routes;
it has no generic static server. This step adds three tiny ServeFile routes so
the panel's brand/icon images resolve instead of 404ing. No behaviour change to
RF, gateways, the hardware probe or any API handler.

This is a TEST build. It is not approved and nothing here is hardware-verified.
"""
from pathlib import Path
import subprocess
import sys

repo = Path(__file__).resolve().parents[1]
out = Path(sys.argv[1]).resolve()
arch = sys.argv[2]
subprocess.run([sys.executable, str(repo / 'ci/prepare-5.15-backend.py'), str(out), arch], check=True)
main = out / 'main.go'
source = main.read_text()


def replace(old, new):
    global source
    assert source.count(old) == 1, old
    source = source.replace(old, new, 1)


# V2-PANEL-ASSETS: serve the panel's icon images from /usr/share/2pny.
anchor = ('\thttp.HandleFunc("/ui-0.3.0.css", func(w http.ResponseWriter, r *http.Request) '
          '{ http.ServeFile(w, r, "/usr/share/2pny/ui-0.3.0.css") })\n')
routes = anchor + ''.join(
    '\thttp.HandleFunc("/%s", func(w http.ResponseWriter, r *http.Request) '
    '{ http.ServeFile(w, r, "/usr/share/2pny/%s") })\n' % (name, name)
    for name in ('favicon.png', 'apple-touch-icon.png', 'favicon-192.png')
)
replace(anchor, routes)

main.write_text(source)
print("PREPARE_V2_BACKEND_OK", arch)
