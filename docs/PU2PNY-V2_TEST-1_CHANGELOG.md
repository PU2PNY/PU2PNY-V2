# PU2PNY-V2 — TEST-1 changelog

**Classification: TEST / physical-test candidate. NOT approved. Nothing hardware-verified.**

Target: Raspberry Pi 32-bit (ARMv6, GOARM=6) — covers Pi Zero W and all Raspberry Pi.
First-access AP name: `PU2PNY-RPI-32`.

Built by reusing the proven PU2PNY-OS pipeline (NOT Buildroot — that is a later phase):
the published **5.12.002 board-32** image is the base; the proven **5.15** overlay and
backend are applied, then the V2 panel and the owner-reported fixes on top. The V2 image
is a safe superset of 5.15; internal `/etc/2pny/version` stays `5.15.000` (code lineage),
and `/etc/2pny/v2-build` = `PU2PNY-V2-TEST-1`.

## What went in

### Panel (replaces the old generated panel)
- New static panel from `feat/panel-v2` installed over the daemon's existing fixed routes:
  - `panel/index.html` → `/usr/share/2pny/dashboard.html` (served at `/dashboard`);
    `hotspot/internet/direct/aprs/history/display/system/expert.html` kept their names.
  - `panel/ui-common.js` → `/usr/share/2pny/ui-common-0.3.0.js`.
  - `panel/ui.css` + `panel/pny-v2.css` concatenated → `/usr/share/2pny/ui-0.3.0.css`.
  - `panel/ui-language.js` → `/usr/share/2pny/ui-language.js`.
  - `favicon.png`, `apple-touch-icon.png`, `favicon-192.png` → `/usr/share/2pny/`.
- Install-time rewrites so the panel works against the device daemon:
  nav `ROUTE` map → clean routes (`/dashboard`, `/internet`, …); `ui-common.js` → the
  served `/ui-common-0.3.0.js`; CSS → the single served `/ui-0.3.0.css`;
  `ui-language.js` loader → `/ui-language.js`; icon refs → absolute paths.
- Backend: three `ServeFile` routes added for the panel icons
  (`/favicon.png`, `/apple-touch-icon.png`, `/favicon-192.png`). No API/RF change.
  (`ci/prepare-v2-backend.py`)

### CPU (owner-reported)
- **Clock persistence — root cause fixed.** `tz-apply` replaces the `/etc/localtime`
  symlink (and `/etc/timezone`) via a temp dir *inside* `/etc`, but the unit allowed only
  `/etc/timezone` under `ProtectSystem=full`, so every apply failed and the clock stayed
  Europe/London. Drop-in `etc/systemd/system/2pny-timezone-apply.service.d/70-rw-etc.conf`
  adds `ReadWritePaths=/etc`. Build asserts `tzdata` has `America/Sao_Paulo`.
- **60s timezone POST storm — gone by design.** The old `ui-common` re-armed an auto-TZ
  `/api/clock/browser` POST on failure every ~60s. The V2 `ui-common.js` has no auto-TZ
  loop at all (it only reads `tz` from `/api/status`/`/api/system`), so the storm is
  removed by shipping the V2 panel. The wizard still sends the browser TZ once.
- **Retry churn slowed.** Drop-in `2pny-profile-autostart-retry.timer.d/70-slower.conf`
  changes `OnUnitInactiveSec` 90s → 300s (reset + set).

### YSF (owner-reported)
- Generated `YSFGateway.ini` had `Revert=0` (`Reconnect` was already `1` in the base), so
  YSF stayed unlinked after an inactivity drop. `2pny-protocol-network-apply` now emits
  `Revert=1` (one-key change to a file that was baseline-protected in the old repo).
- QSO-safe watchdog `2pny-ysf-linkguard` (+ `.service` + `.timer`, enabled via
  `timers.target.wants`): restarts `2pny-ysfgateway.service` **only** when it is active yet
  its local UDP bridge (`:4200`, the link to MMDVMHost) is confirmed down across two checks
  8s apart. A dead bridge means the gateway is already muted — no live QSO is cut. It is
  **never** a blind periodic restart. Reflector re-link is handled by `Revert=1`.

### Voice (owner-reported)
- DMRGateway logged `Unable to open the index file - .../Portugues.indx` because no
  Portuguese voice pack is shipped. `2pny-dmr-apply` now defaults `[Voice] Enabled=0`
  (`voice_cfg.get("enabled", False)`), so DMRGateway stops erroring. RF/gateway untouched;
  a user who installs a pack can re-enable via `voice-settings.json`.

### Display-boot (low risk)
- Drop-in `2pny-display-boot.service.d/70-timeout.conf` raises `TimeoutStartSec` 5s → 30s
  (no reordering of the boot).

## Validation (SW/CI only)
xz integrity, SHA-256, ext4 `fsck`, read-only remount manifest, backend byte-match,
ELF 32-bit ARM for all gateway binaries, protected RF/Nextion baseline unchanged (except
the one intentional YSF `Revert` key), bootloader first-MiB unchanged. Backend `go test`
and the 5.13/5.13.003/5.14/5.15/rf-access source gates pass.
**RF / MMDVM / Nextion / DMR duplex / real TX-RX: NOT verified** — requires a Raspberry Pi.

## Panel buttons still pending a backend (secondary — fail gracefully)
- **Direct groups** — panel POSTs `/api/direct/group` (create/delete); the daemon has no
  such route (a `2pny-direct-group` helper exists but is not proxied). → 404, fails cleanly.
- **Full report** (expert) — POST `/api/system {action:"full-report"}`; `systemControlHandler`
  handles only operational-on/off/reboot/poweroff. → error shown, no report.
- **Display rotation/brightness/mmdvm_info/nextion_face** — POST `/api/display/override`
  with new fields; the base handler does not persist brightness / mmdvm-on-all-screens /
  front-back face yet (OLED rotation path exists). → saved partially.
- **Public/private + identity edit** — POST `/api/station/settings`; the endpoint exists,
  but new visibility/identity fields may be ignored until the daemon honours them.
