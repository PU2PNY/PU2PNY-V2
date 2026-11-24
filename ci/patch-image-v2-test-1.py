#!/usr/bin/env python3
"""PU2PNY-V2 TEST-1 overlay on the proven published 5.12.002 (board 32) rootfs.

This is a TEST build. It is NOT approved and nothing here is hardware-verified.

It is a safe superset of the proven 5.15 overlay:
  1. apply the full 5.15 overlay (all proven fixes + backend), version -> 5.15.000;
  2. swap in the new PU2PNY-V2 panel (feat/panel-v2), served through the
     daemon's existing fixed asset/page routes;
  3. apply the owner-reported fixes that 5.15 did NOT address:
       - CPU/clock persistence: timezone-apply can write /etc (root cause of the
         clock never latching and the browser retry storm). The V2 panel also
         drops the old 60s auto-timezone POST loop entirely.
       - profile-autostart retry churn slowed 90s -> 300s.
       - YSF re-link resilience: generated YSFGateway.ini gets Reconnect/Revert
         plus a QSO-safe local-bridge watchdog.
       - DMR voice: disabled by default so DMRGateway stops erroring on the
         missing Portuguese index (no voice pack shipped). RF/gateway untouched.
       - display-boot: oneshot start timeout raised off the 5s default.

It does not touch RF scripts, MMDVMHost, the hardware probe, the gateway
binaries or the Nextion baseline.
"""
import importlib.util
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PANEL = REPO / 'panel'
BACKUP = '.pre-v2'


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, REPO / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


FIVE15 = _load('ci/patch-image-5.15.py', 'overlay_515')

# --- clean-route and asset rewrites applied to every V2 panel page ----------
PAGE_ROUTE = {
    'index.html': '/dashboard', 'hotspot.html': '/hotspot', 'internet.html': '/internet',
    'direct.html': '/direct', 'aprs.html': '/aprs', 'history.html': '/history',
    'display.html': '/display', 'system.html': '/system', 'expert.html': '/expert',
}
# Which panel source file becomes which served file under /usr/share/2pny.
PAGE_DEST = {
    'index.html': 'dashboard.html', 'hotspot.html': 'hotspot.html',
    'internet.html': 'internet.html', 'direct.html': 'direct.html',
    'aprs.html': 'aprs.html', 'history.html': 'history.html',
    'display.html': 'display.html', 'system.html': 'system.html',
    'expert.html': 'expert.html',
}


def _rewrite_html(text):
    text = text.replace('src="ui-common.js"', 'src="/ui-common-0.3.0.js"')
    text = text.replace('href="ui.css"', 'href="/ui-0.3.0.css"')
    text = text.replace('<link rel="stylesheet" href="pny-v2.css">', '')
    text = text.replace('href="favicon.png"', 'href="/favicon.png"')
    text = text.replace('src="favicon.png"', 'src="/favicon.png"')
    text = text.replace('href="apple-touch-icon.png"', 'href="/apple-touch-icon.png"')
    text = text.replace('href="favicon-192.png"', 'href="/favicon-192.png"')
    for src, route in PAGE_ROUTE.items():
        text = text.replace('href="%s"' % src, 'href="%s"' % route)
    return text


def _rewrite_ui_common(text):
    old_route = (
        "  var ROUTE={live:'index.html',internet:'internet.html',hotspot:'hotspot.html',direct:'direct.html',\n"
        "    aprs:'aprs.html',history:'history.html',display:'display.html',system:'system.html',expert:'expert.html'};"
    )
    new_route = (
        "  var ROUTE={live:'/dashboard',internet:'/internet',hotspot:'/hotspot',direct:'/direct',\n"
        "    aprs:'/aprs',history:'/history',display:'/display',system:'/system',expert:'/expert'};"
    )
    assert text.count(old_route) == 1, 'V2 ui-common ROUTE map not found (panel changed?)'
    text = text.replace(old_route, new_route, 1)
    assert text.count("sc.src='ui-language.js'") == 1, 'V2 ui-common ui-language loader not found'
    text = text.replace("sc.src='ui-language.js'", "sc.src='/ui-language.js'", 1)
    return text


def apply(root, board, backend):
    root = Path(root).resolve()
    assert root != Path('/') and board == '32', 'V2 TEST-1 builds only board 32 (ARMv6)'
    changed = set(FIVE15.apply(root, board, backend))
    assert (root / 'etc/2pny/version').read_text().strip() == '5.15.000'

    def put(relative, data, mode=None):
        path = root / relative
        assert not path.is_symlink(), relative
        if path.is_file():
            bak = path.with_name(path.name + BACKUP)
            assert not bak.exists() and not bak.is_symlink(), bak
            shutil.copy2(path, bak)
            changed.add(relative + BACKUP)
        assert not path.exists() or path.is_file(), relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data.encode() if isinstance(data, str) else data)
        if mode is not None:
            path.chmod(mode)
        changed.add(relative)

    def edit(relative, old, new, count=1):
        src = (root / relative).read_text()
        assert src.count(old) == count, (relative, old, src.count(old))
        put(relative, src.replace(old, new, count))

    ui = 'usr/share/2pny/'

    # ---- 2. PU2PNY-V2 panel ------------------------------------------------
    for src_name, dest_name in PAGE_DEST.items():
        text = _rewrite_html((PANEL / src_name).read_text())
        put(ui + dest_name, text, 0o644)
    put(ui + 'ui-common-0.3.0.js', _rewrite_ui_common((PANEL / 'ui-common.js').read_text()), 0o644)
    css = (PANEL / 'ui.css').read_text() + '\n' + (PANEL / 'pny-v2.css').read_text()
    put(ui + 'ui-0.3.0.css', css, 0o644)
    put(ui + 'ui-language.js', (PANEL / 'ui-language.js').read_bytes(), 0o644)
    for asset in ('favicon.png', 'apple-touch-icon.png', 'favicon-192.png'):
        put(ui + asset, (PANEL / asset).read_bytes(), 0o644)

    # ---- 3a. clock persistence (CPU root cause) ----------------------------
    tz_unit = root / 'etc/systemd/system/2pny-timezone-apply.service'
    assert tz_unit.is_file(), 'missing 2pny-timezone-apply.service in base'
    assert (root / 'usr/share/zoneinfo/America/Sao_Paulo').is_file(), \
        'tzdata missing America/Sao_Paulo'
    put('etc/systemd/system/2pny-timezone-apply.service.d/70-rw-etc.conf',
        '# V2-TEST-1: tz-apply must write /etc/localtime (+/etc/timezone); the\n'
        '# stock unit only allowed /etc/timezone, so the clock never latched.\n'
        '[Service]\nReadWritePaths=/etc\n', 0o644)

    # ---- 3b. slow the profile-autostart retry churn (90s -> 300s) ----------
    retry_timer = root / 'etc/systemd/system/2pny-profile-autostart-retry.timer'
    assert retry_timer.is_file(), 'missing 2pny-profile-autostart-retry.timer in base'
    put('etc/systemd/system/2pny-profile-autostart-retry.timer.d/70-slower.conf',
        '[Timer]\nOnUnitInactiveSec=\nOnUnitInactiveSec=300s\n', 0o644)

    # ---- 3c. YSF re-link resilience ----------------------------------------
    # Generated YSFGateway.ini had Revert=0 (Reconnect was already 1 in the
    # 5.12.002 base), so YSF stayed unlinked after an inactivity drop instead of
    # reverting to the startup reflector. 2pny-protocol-network-apply is
    # baseline-protected in the old repo; in V2 we own it and flip only Revert.
    edit('usr/local/sbin/2pny-protocol-network-apply',
         'Reconnect=1\nRevert=0', 'Reconnect=1\nRevert=1')
    # QSO-safe watchdog: restart YSFGateway only when it is active but its local
    # UDP bridge (port 4200, the link to MMDVMHost) is confirmed down across two
    # checks. A dead bridge means the gateway is already muted, so no live QSO is
    # cut. Reflector re-link is handled by Reconnect/Revert above.
    put('usr/local/sbin/2pny-ysf-linkguard', (
        '#!/bin/bash\n'
        '# PU2PNY-V2 TEST-1 YSF local-bridge watchdog. Safe by construction:\n'
        '# only restarts a YSFGateway that is active yet has no bound bridge.\n'
        'set -euo pipefail\n'
        'svc=2pny-ysfgateway.service\n'
        'systemctl is-active --quiet "$svc" || exit 0\n'
        'bridge_down(){ ! ss -H -lun "sport = :4200" 2>/dev/null | grep -q .; }\n'
        'bridge_down || exit 0\n'
        'sleep 8\n'
        'systemctl is-active --quiet "$svc" || exit 0\n'
        'bridge_down || exit 0\n'
        'logger -t 2pny-ysf-linkguard "YSFGateway active but UDP bridge :4200 '
        'down; restarting (V2-TEST-1)"\n'
        'systemctl --no-block restart "$svc" || true\n'
    ), 0o755)
    put('etc/systemd/system/2pny-ysf-linkguard.service',
        '[Unit]\nDescription=PU2PNY-V2 YSF local-bridge watchdog (TEST-1)\n'
        'After=2pny-ysfgateway.service\n'
        '[Service]\nType=oneshot\nExecStart=/usr/local/sbin/2pny-ysf-linkguard\n'
        'Nice=10\n', 0o644)
    put('etc/systemd/system/2pny-ysf-linkguard.timer',
        '[Unit]\nDescription=PU2PNY-V2 YSF local-bridge watchdog schedule (TEST-1)\n'
        '[Timer]\nOnBootSec=180s\nOnUnitInactiveSec=120s\nAccuracySec=20s\n'
        '[Install]\nWantedBy=timers.target\n', 0o644)
    link = root / 'etc/systemd/system/timers.target.wants/2pny-ysf-linkguard.timer'
    link.parent.mkdir(parents=True, exist_ok=True)
    assert not link.exists(), link
    link.symlink_to('../2pny-ysf-linkguard.timer')
    changed.add('etc/systemd/system/timers.target.wants/2pny-ysf-linkguard.timer')

    # ---- 3d. DMR voice: default OFF so DMRGateway stops erroring ------------
    # The Portuguese voice pack is not shipped; DMRGateway logged
    # "Unable to open the index file - .../Portugues.indx" every start. Default
    # the generated [Voice] block to Enabled=0. RF/gateway itself untouched;
    # a user who installs a pack can re-enable via voice-settings.json.
    edit('usr/local/libexec/2pny-dmr-apply',
         'voice_cfg.get("enabled",True)', 'voice_cfg.get("enabled",False)')

    # ---- 3e. display-boot oneshot timeout ----------------------------------
    db_unit = root / 'etc/systemd/system/2pny-display-boot.service'
    if db_unit.is_file():
        put('etc/systemd/system/2pny-display-boot.service.d/70-timeout.conf',
            '# V2-TEST-1: the 5s oneshot timeout tripped before the modem/display\n'
            '# were ready. Give it room without reordering the boot.\n'
            '[Service]\nTimeoutStartSec=30s\n', 0o644)

    # ---- V2 build marker ---------------------------------------------------
    put('etc/2pny/v2-build', 'PU2PNY-V2-TEST-1\n', 0o644)
    return changed
