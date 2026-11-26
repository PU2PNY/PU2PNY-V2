#!/usr/bin/env bash
set -euo pipefail

repo="$(cd "$(dirname "$0")/.." && pwd)"
overlay="$(realpath "${1:?Provide a staging directory}")"
[[ -d "$overlay" && "$overlay" != / && -z "$(ls -A "$overlay")" ]] || {
    echo "Use an empty staging directory" >&2
    exit 1
}
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT

python3 "$repo/ci/prepare-v2-test-2-backend.py" "$work" arm32
cp "$repo/ci/test-v2-full-report.go" "$work/v2_full_report_test.go"
(
    cd "$work"
    env -u GOOS -u GOARCH -u GOARM GO111MODULE=off CGO_ENABLED=0 go test ./...
    GO111MODULE=off CGO_ENABLED=0 GOOS=linux GOARCH=arm GOARM=6 \
        go build -trimpath -ldflags='-s -w' -o 2pnyd .
)
file "$work/2pnyd" | grep -E 'ELF 32-bit.*ARM.*statically linked'
go version -m "$work/2pnyd" | grep -E 'build[[:space:]]+GOARM=6(,|$)'

python3 "$repo/ci/v2-panel-overlay.py" "$overlay"
install -D -m 0755 "$work/2pnyd" "$overlay/usr/local/bin/2pnyd"
# Install a unit without boot activation while its runtime dependencies are migrated.
install -D -m 0644 "$repo/runtime/v2/2pnyd.service" "$overlay/etc/systemd/system/2pnyd.service"
