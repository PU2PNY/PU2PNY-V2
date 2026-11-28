#!/usr/bin/env python3
"""PU2PNY-V2 TEST-3 overlay: TEST-2 + vendored xombe AMBE codec for crossmode.

TEST build. NOT approved; nothing hardware-verified.

TEST-3 = every TEST-2 change, plus the xombe (MIT, C99) AMBE 2400 / AMBE+2 codec
cross-compiled for ARMv6 hard-float, installed for opt-in D-Star<->DMR/YSF crossmode
transcoding. Crossmode is STRICTLY OPT-IN and OFF by default: with ENABLED=0 the
hotspot behaves exactly as TEST-2 (Normal mode, baseline RF path untouched).

Patent note (owner's decision, recorded in the changelog): xombe's README warns AMBE
patents may still be in force in some jurisdictions. It ships under its MIT license.

What this overlay installs (priorities (1)+(2) of the task; (3) panel toggle and (4)
live RF routing are NOT wired yet — see the changelog):
  - /usr/local/bin/xombe-xc,-dec,-enc  (ARMv6hf; self-tested + qemu-verified in CI)
  - /etc/2pny/crossmode.conf           (config-driven gain; proven XLX026 ambed values)
  - /usr/local/sbin/2pny-crossmode-xombe (dec->gain->enc transcoder + status/daemon)
  - /etc/systemd/system/pu2pny-crossmode.service (DISABLED: opt-in, never auto-starts)
It does not touch the Normal-mode RF path, MMDVMHost, gateways or the Nextion baseline.
"""
import importlib.util
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BACKUP = '.pre-v2t3'


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, REPO / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


TEST2 = _load('ci/patch-image-v2-test-2.py', 'overlay_v2_t2')

CROSSMODE_CONF = """# PU2PNY-V2 crossmode (xombe AMBE transcoder) configuration.
# OPT-IN and OFF by default. Tune by editing a number and restarting
# pu2pny-crossmode.service -- never by recompiling.
#
# ENABLED=0 -> Normal mode (baseline RF path, exactly like TEST-2).
ENABLED=0
# One cross-direction at a time: dstar2dmr | dmr2dstar
DIRECTION=dstar2dmr
# PCM gains in dB, applied in the decode->gain->encode path (the ambed model).
# Seeded with the owner's PROVEN XLX026 ambed values.
GAIN_DSTAR_TO_DMR=-20
GAIN_DMR_TO_DSTAR=19
# EQ and noise-gate off by default (match the ambed baseline).
EQ=off
NOISE_GATE=off
"""

WRAPPER = r'''#!/bin/sh
# PU2PNY-V2 crossmode transcoder (xombe). Config-driven gain; OPT-IN, OFF by default.
# Stage: ARMv6 codec + PCM-gain path installed and self-tested. Live RF streaming
# (routing MMDVMHost<->gateways through the transcoder) is NOT wired yet.
set -eu
CONF=/etc/2pny/crossmode.conf
ENABLED=0; DIRECTION=dstar2dmr; GAIN_DSTAR_TO_DMR=-20; GAIN_DMR_TO_DSTAR=19; EQ=off; NOISE_GATE=off
[ -r "$CONF" ] && . "$CONF"

pcm_gain() { # $1 = dB ; stdin raw S16LE -> stdout raw S16LE
	python3 -I -c '
import sys,struct
db=float(sys.argv[1]); f=10.0**(db/20.0)
r=sys.stdin.buffer.read()
o=bytearray()
for i in range(0,len(r)-1,2):
    v=int(round(struct.unpack_from("<h",r,i)[0]*f))
    v=32767 if v>32767 else -32768 if v<-32768 else v
    o+=struct.pack("<h",v)
sys.stdout.buffer.write(o)' "$1"
}

transcode() { # $1 in  $2 out  (uses DIRECTION + gains; dec->gain->enc)
	in="$1"; out="$2"; tmp="$(mktemp -d)"
	trap 'rm -rf "$tmp"' EXIT
	case "$DIRECTION" in
		dstar2dmr)
			xombe-dec --dstar "$in" "$tmp/a.raw"
			pcm_gain "$GAIN_DSTAR_TO_DMR" < "$tmp/a.raw" > "$tmp/g.raw"
			xombe-enc --air "$tmp/g.raw" "$out" ;;
		dmr2dstar)
			xombe-dec --air "$in" "$tmp/a.raw"
			pcm_gain "$GAIN_DMR_TO_DSTAR" < "$tmp/a.raw" > "$tmp/g.raw"
			xombe-enc --dstar "$tmp/g.raw" "$out" ;;
		*) echo "crossmode: bad DIRECTION=$DIRECTION" >&2; exit 2 ;;
	esac
}

case "${1:-status}" in
	status)
		echo "xombe: $(command -v xombe-xc || echo MISSING)"
		echo "ENABLED=$ENABLED DIRECTION=$DIRECTION GAIN_DSTAR_TO_DMR=$GAIN_DSTAR_TO_DMR GAIN_DMR_TO_DSTAR=$GAIN_DMR_TO_DSTAR EQ=$EQ NOISE_GATE=$NOISE_GATE" ;;
	transcode) shift; transcode "$@" ;;
	daemon)
		if [ "$ENABLED" != 1 ]; then echo "crossmode OFF (ENABLED=0); Normal mode"; exit 0; fi
		echo "crossmode: codec ready (DIRECTION=$DIRECTION, gains $GAIN_DSTAR_TO_DMR/$GAIN_DMR_TO_DSTAR dB); live RF routing not yet wired -- idling."
		exec sleep infinity ;;
	*) echo "usage: $0 {status|transcode IN OUT|daemon}" >&2; exit 1 ;;
esac
'''

SERVICE = """[Unit]
Description=PU2PNY-V2 crossmode AMBE transcoder (xombe) -- OPT-IN, OFF by default
ConditionPathExists=/etc/2pny/crossmode.conf
After=2pny-mmdvmhost.service
[Service]
Type=simple
ExecStart=/usr/local/sbin/2pny-crossmode-xombe daemon
Restart=no
Nice=5
[Install]
WantedBy=multi-user.target
"""


def apply(root, board, backend, xombe_dir):
    root = Path(root).resolve()
    xombe_dir = Path(xombe_dir).resolve()
    assert root != Path('/') and board == '32', 'V2 TEST-3 builds only board 32 (ARMv6)'
    changed = set(TEST2.apply(root, board, backend))
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

    # ARMv6 codec binaries (verified ELF 32-bit ARM by the build script).
    for b in ('xombe-xc', 'xombe-dec', 'xombe-enc'):
        data = (xombe_dir / b).read_bytes()
        assert data[:4] == b'\x7fELF' and data[4] == 1, b  # 32-bit
        put('usr/local/bin/' + b, data, 0o755)
    put('etc/2pny/crossmode.conf', CROSSMODE_CONF, 0o644)
    put('usr/local/sbin/2pny-crossmode-xombe', WRAPPER, 0o755)
    # Service is installed DISABLED: no symlink in multi-user.target.wants, so it
    # never auto-starts. Crossmode stays strictly opt-in.
    put('etc/systemd/system/pu2pny-crossmode.service', SERVICE, 0o644)
    put('etc/2pny/crossmode-codec', 'xombe 2f0a8e7 armv6hf (MIT); crossmode OPT-IN/OFF\n', 0o644)

    put('etc/2pny/v2-build', 'PU2PNY-V2-TEST-3\n', 0o644)
    return changed
