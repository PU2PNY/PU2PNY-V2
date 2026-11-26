#!/usr/bin/env bash
set -euo pipefail

linker="$(realpath -s "${1:?ARMv6 GCC required}")"
dest="$(realpath -m "${2:?target binary path required}")"
[[ -x "$linker" ]]
export RUSTUP_TOOLCHAIN=1.90.0
rustc --version | grep -E '^rustc 1\.90\.0 '
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
git clone -q https://github.com/PU2PNY/Helix-Voice.git "$work"
commit=b71a5fccd6371a88284866510000302f0126d565
git -C "$work" checkout -q --detach "$commit"
test "$(git -C "$work" rev-parse HEAD)" = "$commit"
(
    cd "$work"
    cargo test --workspace --offline
    CARGO_TARGET_ARM_UNKNOWN_LINUX_GNUEABIHF_LINKER="$linker" \
        cargo build --offline --release --target arm-unknown-linux-gnueabihf -p helix-daemon
)
binary="$work/target/arm-unknown-linux-gnueabihf/release/helix-daemon"
readelf -A "$binary" | grep -F 'Tag_CPU_arch: v6KZ'
qemu-arm -cpu arm1176 -L "$("$linker" --print-sysroot)" "$binary" --self-test
install -D -m 0755 "$binary" "$dest"
