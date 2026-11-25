#!/usr/bin/env python3
"""PU2PNY-V2 TEST-2 overlay: TEST-1 + rebrand to PU2PNY-V2 (fixes the name collision).

TEST build. NOT approved; nothing hardware-verified.

TEST-2 = every TEST-1 change, plus:
  1. Rebrand so the device stops colliding with the owner's other pu2pny32.local
     hotspot: AP SSID -> PU2PNY-V2; hostname + mDNS -> pu2pny-v2(.local); captive
     domain -> pu2pny-v2.local; panel + wizard branding -> PU2PNY-V2. The hostname
     is enforced at runtime by several scripts (mdns-guard, firstboot,
     network-switch, wifi-profiles), so every one is renamed, not just /etc.
     (Two PU2PNY-V2 units would still differ: avahi suffixes -2; the point here is
     to separate V2 from the old pu2pny32.local line.)

The identity-edit fix (panel now calls the existing /api/identity/apply instead of
the unimplemented /api/station/settings identity action) and the full-report
endpoint ride in the panel sources and the TEST-2 backend respectively.

It does not touch RF scripts, MMDVMHost, the hardware probe, the gateway binaries
or the Nextion baseline.
"""
import importlib.util
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BACKUP = '.pre-v2t2'


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, REPO / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


TEST1 = _load('ci/patch-image-v2-test-1.py', 'overlay_v2_t1')

# Files that still carry the old board-32 hostname/SSID after the TEST-1 overlay.
# internet/display/system/expert.html are replaced by the V2 panel (already
# rebranded at source), so they are not listed here.
HOSTNAME_FILES = [
    'etc/hostname',
    'etc/hosts',
    'etc/avahi/avahi-daemon.conf',
    'etc/NetworkManager/dnsmasq-shared.d/2pny-captive.conf',
    'etc/NetworkManager/dispatcher.d/90-pu2pny-mdns',
    'usr/share/2pny/network/dnsmasq-ap.template',
    'usr/local/sbin/2pny-network-core',
    'usr/local/sbin/2pny-network-switch',
    'usr/local/sbin/2pny-wifi-profiles',
    'usr/local/sbin/2pny-firstboot',
    'usr/local/sbin/2pny-mdns-guard',
]


def apply(root, board, backend):
    root = Path(root).resolve()
    assert root != Path('/') and board == '32', 'V2 TEST-2 builds only board 32 (ARMv6)'
    changed = set(TEST1.apply(root, board, backend))
    assert (root / 'etc/2pny/version').read_text().strip() == '5.15.000'

    def put(relative, data, mode=None):
        path = root / relative
        assert not path.is_symlink(), relative
        if path.is_file():
            bak = path.with_name(path.name + BACKUP)
            if not bak.exists() and not bak.is_symlink():
                shutil.copy2(path, bak)
                changed.add(relative + BACKUP)
        assert not path.exists() or path.is_file(), relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data.encode() if isinstance(data, str) else data)
        if mode is not None:
            path.chmod(mode)
        changed.add(relative)

    def rename(relative, pairs):
        src = (root / relative).read_text()
        for old, new in pairs:
            assert src.count(old) >= 1, ('rename target missing', relative, old)
            src = src.replace(old, new)
        put(relative, src)

    # ---- hostname / mDNS: pu2pny32 -> pu2pny-v2 everywhere it is set/enforced
    for rel in HOSTNAME_FILES:
        rename(rel, [('pu2pny32', 'pu2pny-v2')])
    # ---- AP SSID: pu2pny-32 -> PU2PNY-V2
    rename('usr/share/2pny/network/hostapd.template', [('ssid=pu2pny-32', 'ssid=PU2PNY-V2')])
    # ---- wizard page: hostname refs + visible branding
    rename('usr/share/2pny/wizard.html', [('pu2pny32', 'pu2pny-v2'), ('PU2PNY-OS', 'PU2PNY-V2')])

    # ---- build marker
    put('etc/2pny/v2-build', 'PU2PNY-V2-TEST-2\n', 0o644)
    return changed
