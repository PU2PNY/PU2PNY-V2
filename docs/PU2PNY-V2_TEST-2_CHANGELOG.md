# PU2PNY-V2 — TEST-2 changelog

**TEST / physical-test candidate. NOT approved. Nothing hardware-verified.**
Target: Raspberry Pi 32-bit (ARMv6). Built on the proven 5.12.002 base; all TEST-1
fixes retained. Internal `/etc/2pny/version` stays `5.15.000`; `/etc/2pny/v2-build` = `PU2PNY-V2-TEST-2`.

## Done in TEST-2 (priority order)

### 1. Rebrand to PU2PNY-V2 (fixes the pu2pny32.local collision) — DONE
Renamed everywhere the old board-32 identity was set or enforced at runtime:
- AP Wi-Fi SSID `pu2pny-32` → **PU2PNY-V2** (`usr/share/2pny/network/hostapd.template`).
- hostname + mDNS `pu2pny32` → **pu2pny-v2** / **pu2pny-v2.local**, in `/etc/hostname`,
  `/etc/hosts`, `/etc/avahi/avahi-daemon.conf`, and in the scripts that re-assert the
  hostname at runtime (`2pny-mdns-guard`, `2pny-firstboot`, `2pny-network-switch`,
  `2pny-wifi-profiles`) — so the rename is not reverted on boot.
- Captive domain `pu2pny32.local` → **pu2pny-v2.local** (`2pny-network-core`,
  `dnsmasq-ap.template`, `2pny-captive.conf`, `90-pu2pny-mdns`). Captive IP 10.43.0.1 kept.
- Panel + wizard branding "PU2PNY-OS" → **PU2PNY-V2** (all panel pages, ui-common.js, wizard.html).

Note: two PU2PNY-V2 units would not hard-collide (avahi suffixes `-2`); the goal here is to
separate V2 from the owner's existing pu2pny32.local hotspot.

### 3. Full-report endpoint (to diagnose YSF-no-audio next round) — DONE
`POST /api/system {action:"full-report"}` now returns a downloadable read-only report:
config, diagnostics (protocol, mmdvmhost/gateway active, UDP bridges, mqtt/protocol health,
rollback, dmr-duplex), hardware.json, display detection/runtime/settings/override,
network-radio.json, service states, and the **MMDVMHost / YSFGateway / DMRGateway / 2pnyd
journals** (last 200–400 lines). No RF/gateway change. (`ci/prepare-v2-test-2-backend.py`,
`web_v2report.go`; Expert → "Relatório completo").

### 4a. Identity edit (HTTP 400) — DONE
Panel now POSTs to the existing proper endpoint **`/api/identity/apply`** `{callsign, dmr_id}`
instead of the unimplemented `/api/station/settings {action:"identity"}`. That endpoint runs
`2pny-identity-apply` (callsign + DMR ID only, not a full RF reapply). Panel-side fix only.

### 4b. "Aplicar display" (opção de display inválida / HTTP 400) — DONE (the 400)
Root cause: the panel sent `layout` as a **string** into the daemon's `int` field, so the JSON
decode failed → 400. Panel now sends `layout:Number(...)` (+ `model_profile:"auto"`). With the
Nextion now physically confirmed, enabling it with a valid renderer/layout drives live MMDVM
data through the existing NextionDriver-pu2pny + MMDVMHost display path.

## Investigated / pending (honest status)

### 2. Wizard network handoff + re-entry — NOT FIXED (needs hardware-iterative work)
WIZ-514 (the "never freeze → Ir para configuração básica" fallback) IS present in this build
(injected by the 5.15 overlay into wizard.html). The owner's TEST-1 still froze at 12% on
"continuar sem internet": that 12% is the wizard progress bar; the underlying `2pny-hardware-probe`
is baseline-PROTECTED and blocks while the AP/hostapd is active (the device completed detection
100% when reached over its LAN IP). The AP→client Wi-Fi handoff hang ("conectando"), Wi-Fi scan
on re-entry, and Ethernet recognition live in `2pny-network-core` / wizard and are tangled with
the protected probe. These need careful, hardware-in-the-loop iteration and were NOT blind-edited
to avoid regressing the proven network/boot baseline. The rebrand should at least remove the
name-collision confusion. **Recommend reaching the device by its LAN IP for TEST-2**, and that
the next round focus solely on the wizard handoff with the owner on the hardware.

### 4c. Per-protocol DMR profile save/switch (HTTP 400 / "não configurado") — NOT FIXED
The panel "Ativar" only activates a profile that already has `rx_hz`; only YSF was configured via
the wizard, so DMR has no stored profile and activation is refused. Making "Configurar" for
DMR/D-Star/P25/NXDN work routes through `/api/protocol/apply` → the **PROTECTED**
`2pny-protocol-network-apply` (RF path). Not changed in TEST-2 to avoid RF regressions without
hardware. Pending a focused round.

### Public/private visibility — NOT FIXED
Panel POSTs `/api/config {action:"visibility"}`, but `publicConfigHandler` is read-only (ignores
the POST), so it silently no-ops. Needs a backend visibility action + gateway re-registration. Pending.

### 5. YSF audio (linked, no audio) — INVESTIGATE ONLY (not faked)
YSFGateway links (BR-XLX026) but passes no audio. Not root-caused without logs; hypotheses to
check from the new full-report: MMDVMHost `[System Fusion]` enable/DG-ID, the 4200 UDP bridge
actually carrying frames, and FICH/WiresX. **The real fix waits for the owner's full-report from
TEST-2.** No audio-path code was changed.

## Validation (SW/CI only)
Overlay applied against the real 5.12.002 base with zero undeclared/missing paths and zero
protected-baseline violations (except the intentional TEST-1 YSF Revert key); backend `go test`
+ ARMv6 ELF build pass; xz / SHA-256 / ext4 fsck / read-only remount / bootloader first-MiB all
enforced by `ci/build-v2-test-2.py`. RF / MMDVM / Nextion / YSF-audio: NOT verified.
