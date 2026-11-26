#!/usr/bin/env bash
# Buildroot infrastructure milestone only; not a functional hotspot release.
set -euo pipefail
repo="$(cd "$(dirname "$0")/.." && pwd)"
br="$(realpath "$1")"
out="$(realpath -m "$2")"
mkdir -p "$out"
make -C "$br" O="$out" raspberrypi0w_defconfig
# Keep native systemd semantics for the existing managers; avoid fake shims.
python3 - "$out/.config" "$repo/ci/minimal-arm32.fragment" <<'PY'
import pathlib,re,sys
p,fragment=map(pathlib.Path,sys.argv[1:])
lines=p.read_text().splitlines()
for line in fragment.read_text().splitlines():
    if not line or line.startswith('#'): continue
    key=line.split('=',1)[0]
    assert re.fullmatch(r'BR2_[A-Z0-9_]+',key),key
    lines=[s for s in lines if not (s.startswith(key+'=') or s=='# '+key+' is not set')]
    lines.append(line)
p.write_text('\n'.join(lines)+'\n')
PY
make -C "$br" O="$out" olddefconfig
while IFS= read -r line; do
    [[ -z "$line" || "$line" == \#* ]] && continue
    grep -Fxq "$line" "$out/.config" || { echo "Unresolved Buildroot option: $line" >&2; exit 1; }
done < "$repo/ci/minimal-arm32.fragment"
make -C "$br" O="$out" -j "$(nproc)"
test -s "$out/images/sdcard.img"
mkdir -p "$out/measurement"
xz -T2 -9 -c "$out/images/sdcard.img" > "$out/measurement/base-arm32.img.xz"
xz -t "$out/measurement/base-arm32.img.xz"
bytes="$(stat -c %s "$out/measurement/base-arm32.img.xz")"
printf 'BASE_ONLY_NOT_HOTSPOT\ncompressed_bytes=%s\n' "$bytes" | tee "$out/measurement/status.txt"
du -ah "$out/target" | sort -hr | head -100 > "$out/measurement/size-breakdown.txt" || true
if (( bytes > 80000000 )); then echo "Base exceeds 80 MB" >&2; exit 1; fi
