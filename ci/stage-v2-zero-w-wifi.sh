#!/usr/bin/env bash
# The Raspberry Pi Zero W brcmfmac SDIO driver needs firmware and board NVRAM.
set -euo pipefail
baseline="$(realpath "${1:?TEST-2 root required}")"
target="$(realpath "${2:?staging root required}")"
[[ "$baseline" != / && "$target" != / && "$baseline" != "$target" ]]
test "$(cat "$baseline/etc/2pny/v2-build")" = PU2PNY-V2-TEST-2

firmware="$baseline/usr/lib/firmware/brcm"
dest="$target/usr/lib/firmware/brcm"
for name in brcmfmac43430-sdio.bin brcmfmac43430-sdio.clm_blob \
    brcmfmac43430-sdio.raspberrypi,model-zero-w.txt; do
    source="$(realpath "$firmware/$name")"
    [[ "$source" == "$baseline/usr/lib/firmware/"* ]]
    test -s "$source"
    install -D -m 0644 "$source" "$dest/$name"
done
install -D -m 0644 "$baseline/usr/share/doc/firmware-brcm80211/copyright" \
    "$target/usr/share/licenses/pu2pny-zero-w-wifi/copyright"
