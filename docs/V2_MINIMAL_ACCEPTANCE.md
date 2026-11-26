# PU2PNY-V2 Minimal — acceptance and restart point

Status: DOC only; build, SW, VPS and HW pending. No release delivered.
Baseline: build/v2-test-2, commit 34e6bab0e1b99e95c1a4b79c11198d8d89f9b90e; preserve TEST-1/2 and DISPLAY-041 (5.00.002 ON7LDS). See existing UI contract and TEST-1/2 changelogs. START_HERE, MASTER_SPEC, RELEASE_STATUS and TEST_MATRIX were not found under those names in baseline tree.

## Hard acceptance criteria
- Separate ARM32 (ARMv6 Pi Zero W where feasible, ARMv7 otherwise separately identified) and ARM64 bootable SD images, each complete `.img.xz` <= 80,000,000 bytes; no external package download required for promised features. Never truncate an image or remove features silently. If size fails, stop publication and report measured breakdown.
- Buildroot upstream pinned to verified maintained release; reproducible package sources/hashes, license inventory, kernel/firmware/board support; compare BusyBox init port vs retaining systemd, because existing code directly calls systemctl/journalctl and relies on unit/timer semantics. No assumption of compatibility.
- Retain panel routes, languages, identity, RF controls, DMR simplex/duplex, D-Star, YSF, P25, NXDN, POCSAG/DAPNET, APRS/DPRS, Direct/P2P, history, display, Helix, update and backup/recovery. FM/M17 and transcoding only where demonstrated. All implemented features available for testing; services activate only when configured and supported, no automatic RF transmission or invalid gateway credentials.
- Network: AP recovery, STA/Ethernet, two saved Wi-Fi profiles, association and IPv4 before AP shutdown, rollback, mDNS; preserve V2 identity and approved behavior. Display: preserve official ON7LDS path; no flash or competing writer.
- Correct TEST-2 known defects: wizard AP/STA and probe; DMR profile persistence; public/private action; YSF audio with actual logs; Direct groups and display options. Full report must not leak credentials, raw unreviewed config or logs. All pending until verified.
- Test every manager and API, persistence/reboot, no-secret report, build architecture, compressed size, xz integrity, SHA256, filesystem, boot in available environment, explicit HW checklist. Never infer hardware pass from CI.

## Next implementation milestone
Inventory actual runtime executable dependencies, systemd units/timers, kernel modules, firmware, libraries, Python/Bash features, gateway source and display artifacts in TEST-2. Map each to Buildroot packages or explicit compatibility port. Measure minimal boot image and additive size per component. Preserve existing branch and releases. Do not release a boot-only demo as a full-feature image.

Upstream: https://buildroot.org/downloads/manual/manual.html
