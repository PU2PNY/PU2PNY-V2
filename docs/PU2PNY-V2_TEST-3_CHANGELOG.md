# PU2PNY-V2 — TEST-3 changelog

**TEST / physical-test candidate. NOT approved. Nothing hardware-verified.**
Built on the proven TEST-2 Raspbian base (board 32 / ARMv6). The Normal-mode RF path is
untouched. Crossmode is strictly **opt-in and OFF by default** (`ENABLED=0`): without
enabling it, the hotspot behaves exactly like TEST-2.

## What went in — xombe AMBE codec for D-Star<->DMR/YSF crossmode

Vendored **xombe** (https://github.com/x0rro/xombe, MIT, C99) at commit `2f0a8e7` under
`third_party/xombe` — AMBE 2400 (D-Star) + AMBE+2 (DMR/YSF) decode/encode and parameter-space
transcoding.

### (1) DONE — codec cross-compiled ARMv6hf + self-test passing
- `ci/build-xombe-arm32.sh` + `ci/arm-linux-gnueabihf-armv6.cmake`: native build runs the full
  self-test suite (**88/88 ctest pass**, incl. the DMR↔D-STAR transcoders), then cross-compiles
  `xombe-xc/dec/enc` for **ARMv6 hard-float** (`-march=armv6 -mfpu=vfp -mfloat-abi=hard`), so one
  binary runs on **Pi Zero W and Pi 4**. A qemu smoke test transcodes a real vector both
  directions and confirms the ARM output is **byte-identical to native**. CI gates on all of this.
- Binaries installed at `/usr/local/bin/xombe-xc`, `xombe-dec`, `xombe-enc`.

### (2) DONE (codec + config path) — transcoder + config-driven gain
- `/etc/2pny/crossmode.conf`: config-driven, **edit a number and restart — never recompile**.
  Seeded with the owner's PROVEN XLX026 ambed values: `GAIN_DSTAR_TO_DMR=-20`,
  `GAIN_DMR_TO_DSTAR=19`; `EQ=off`, `NOISE_GATE=off`; `ENABLED=0` (OFF); `DIRECTION=dstar2dmr`.
- `/usr/local/sbin/2pny-crossmode-xombe`: `status` / `transcode IN OUT` / `daemon`. The gain is
  applied in the **decode→gain→encode** PCM path (the ambed model), because xombe-xc's fast
  parameter-space transcode has no PCM gain point. `transcode` is a working, verifiable file
  transcoder using the configured direction + gain.
- `/etc/systemd/system/pu2pny-crossmode.service`: installed **DISABLED** (no
  `multi-user.target.wants` symlink) — never auto-starts; crossmode is opt-in.

### (3) PENDING — panel Crossmode toggle
The V2 panel has no Operation Normal/Crossmode control yet (that existed in the old 2pny-os,
not in feat/panel-v2). The enable mechanism exists (config `ENABLED` + the opt-in service); the
panel button + backend endpoint to flip it are not wired this round.

### (4) PENDING — live RF routing
Routing the MMDVMHost<->gateway audio through the transcoder in real time (streaming ambed-style)
is not implemented. The `daemon` mode is an honest placeholder that logs "codec ready; live RF
routing not wired" and idles if enabled. The codec + gain are proven and ready for it.

## CPU / honesty
- Transcoding is heavy. On a **Pi 4** it is comfortable. On a **Pi Zero W** (single ARMv6) real-time
  one-cross-direction may be marginal — allowed but to be measured on hardware; it is a per-use
  toggle, one direction at a time. (xombe's own benchmark: on an RP2350 @150MHz the q15 encoder
  uses ~41% of a core, decoder ~6%; the Pi Zero W is faster but runs the float build.) No on-device
  CPU figure is fabricated; measure with the full-report once RF routing exists.
- **Patent (owner's decision):** xombe's README warns AMBE patents may still be in force in some
  jurisdictions. Shipped under its MIT license; recorded here as the owner's decision.

## Validation (SW/CI only)
xombe native 88/88 self-tests + ARMv6 cross-build + qemu byte-identical transcode; overlay applied
against the real 5.12.002 base with zero undeclared/missing paths and zero protected-baseline
violations; crossmode verified OFF by default and the service verified non-autostart;
xz/SHA-256/ext4 fsck/read-only remount/bootloader gates enforced by `ci/build-v2-test-3.py`.
RF / live crossmode / audio: NOT verified on hardware.
