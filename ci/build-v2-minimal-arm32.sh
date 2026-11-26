#!/usr/bin/env bash
# Measure the base or the partial panel and backend integration.
set -euo pipefail
repo="$(cd "$(dirname "$0")/.." && pwd)"
br="$(realpath "$1")"
out="$(realpath -m "$2")"
status="BASE_ONLY_NOT_HOTSPOT"
overlay=""
if [[ ${3:-} == --panel-backend ]]; then
    overlay="$(mktemp -d)"
    trap 'rm -rf -- "$overlay"' EXIT
    bash "$repo/ci/stage-v2-arm32.sh" "$overlay"
    status="PANEL_BACKEND_ONLY_NOT_HOTSPOT"
elif (( $# != 2 )); then
    echo "Usage: $0 BUILDROOT OUT [--panel-backend]" >&2
    exit 2
fi
mkdir -p "$out"
make -C "$br" O="$out" raspberrypi0w_defconfig
# Keep native systemd semantics for the existing managers; avoid fake shims.
python3 - "$out/.config" "$repo/ci/minimal-arm32.fragment" "$overlay" <<'PY'
import pathlib,re,sys
p,fragment=map(pathlib.Path,sys.argv[1:3])
overlay = sys.argv[3]
lines=p.read_text().splitlines()
for line in fragment.read_text().splitlines():
    if not line or line.startswith('#'): continue
    key=line.split('=',1)[0]
    assert re.fullmatch(r'BR2_[A-Z0-9_]+',key),key
    lines=[s for s in lines if not (s.startswith(key+'=') or s=='# '+key+' is not set')]
    lines.append(line)
if overlay:
    key = 'BR2_ROOTFS_OVERLAY='
    existing = next((line[len(key):].strip('"') for line in lines if line.startswith(key)), '')
    overlays = ' '.join(filter(None, (existing, overlay)))
    lines = [line for line in lines if not line.startswith(key)]
    lines.append(f'{key}"{overlays}"')
p.write_text('\n'.join(lines)+'\n')
PY
make -C "$br" O="$out" olddefconfig
while IFS= read -r line; do
    [[ -z "$line" || "$line" == \#* ]] && continue
    grep -Fxq "$line" "$out/.config" || { echo "Unresolved Buildroot option: $line" >&2; exit 1; }
done < "$repo/ci/minimal-arm32.fragment"
make -C "$br" O="$out" -j "$(nproc)"
test -s "$out/images/sdcard.img"
if [[ -n "$overlay" ]]; then
    cmp "$overlay/usr/local/bin/2pnyd" "$out/target/usr/local/bin/2pnyd"
    cmp "$overlay/etc/systemd/system/2pnyd.service" "$out/target/etc/systemd/system/2pnyd.service"
    diff -r "$overlay/usr/share/2pny" "$out/target/usr/share/2pny"
fi
mkdir -p "$out/measurement"
xz -T2 -9 -c "$out/images/sdcard.img" > "$out/measurement/base-arm32.img.xz"
xz -t "$out/measurement/base-arm32.img.xz"
bytes="$(stat -c %s "$out/measurement/base-arm32.img.xz")"
printf '%s\ncompressed_bytes=%s\n' "$status" "$bytes" | tee "$out/measurement/status.txt"
du -ah "$out/target" | sort -hr | head -100 > "$out/measurement/size-breakdown.txt" || true
if (( bytes > 80000000 )); then echo "Measured image exceeds 80 MB" >&2; exit 1; fi
