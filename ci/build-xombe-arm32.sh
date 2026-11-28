#!/bin/bash
# PU2PNY-V2 TEST-3: build + self-test the vendored xombe AMBE codec, cross-compile
# it for ARMv6 hard-float (runs on Pi Zero W AND Pi 4), and smoke-test under qemu.
# Usage: build-xombe-arm32.sh OUTDIR
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SRC="$(cd "$HERE/../third_party/xombe" && pwd)"
OUT="${1:?usage: build-xombe-arm32.sh OUTDIR}"
TOOLCHAIN="$HERE/arm-linux-gnueabihf-armv6.cmake"
mkdir -p "$OUT"

echo "== 1) native build + conformance self-test (ctest, vendored vectors) =="
cmake -S "$SRC" -B "$SRC/build-native" -DCMAKE_BUILD_TYPE=Release >/dev/null
cmake --build "$SRC/build-native" -j"$(nproc)" >/dev/null
( cd "$SRC/build-native" && ctest --output-on-failure -j"$(nproc)" )

echo "== 2) cross-compile ARMv6 hard-float (xombe-xc/dec/enc) =="
cmake -S "$SRC" -B "$SRC/build-arm" -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_TOOLCHAIN_FILE="$TOOLCHAIN" -DXOMBE_BUILD_TESTS=OFF >/dev/null
cmake --build "$SRC/build-arm" -j"$(nproc)" >/dev/null
for b in xombe-xc xombe-dec xombe-enc; do
  f="$SRC/build-arm/$b"
  test -x "$f"
  file "$f" | grep -Eq 'ELF 32-bit.*ARM'
  ! file "$f" | grep -Eqi 'aarch64|ARM64'
  arm-linux-gnueabihf-strip "$f" 2>/dev/null || true
  install -m0755 "$f" "$OUT/$b"
done

echo "== 3) qemu smoke: ARM transcoder must byte-match native (both directions) =="
V="$SRC/vectors/e3/es1.ref.d0.amb"
"$SRC/build-native/xombe-xc" --amb "$V" "$OUT/.n.dstar"
qemu-arm-static -L /usr/arm-linux-gnueabihf "$OUT/xombe-xc" --amb "$V" "$OUT/.a.dstar"
cmp "$OUT/.n.dstar" "$OUT/.a.dstar"
qemu-arm-static -L /usr/arm-linux-gnueabihf "$OUT/xombe-xc" --reverse "$OUT/.a.dstar" "$OUT/.a.r33"
test -s "$OUT/.a.r33"
rm -f "$OUT/.n.dstar" "$OUT/.a.dstar" "$OUT/.a.r33"

echo "XOMBE_ARM32_OK"
ls -la "$OUT"
