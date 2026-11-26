#!/usr/bin/env python3
"""Copy approved TEST-2 runtime from its read-only root filesystem."""
import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess

RUNTIME = (
    "usr/local/sbin/2pny-*", "usr/local/sbin/pu2pny-capability-scan",
    "usr/local/libexec/2pny-*", "usr/local/libexec/pu2pny/**/*",
    "usr/local/share/dstargateway.d/*",
    "usr/share/2pny/*", "usr/share/2pny/**/*",
    "var/lib/2pny/hosts/*",
    "etc/2pny/board-id", "etc/2pny/version",
    "etc/NetworkManager/conf.d/*2pny*.conf",
    "etc/NetworkManager/dispatcher.d/*2pny*",
    "etc/NetworkManager/dnsmasq-shared.d/2pny-captive.conf",
    "usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    "etc/avahi/avahi-daemon.conf", "etc/avahi/services/2pny-http.service",
    "etc/mosquitto/conf.d/pu2pny-local.conf",
    "etc/udev/rules.d/*pu2pny*",
    "etc/modules-load.d/2pny-i2c.conf",
    "etc/systemd/system/2pny*", "etc/systemd/system/2pny*.service.d/*.conf",
    "etc/systemd/system/pu2pny-*", "etc/systemd/system/helix-voice*.service",
    "etc/systemd/journald.conf.d/*2pny.conf",
)
GATEWAYS = (
    "2pny-direct-core", "DMRGateway", "dstargateway", "YSFGateway",
    "DAPNETGateway", "P25Gateway", "NXDNGateway", "dgwvoicetransmit",
    "DMR2NXDN", "DMR2YSF", "YSF2DMR", "YSF2NXDN", "YSF2P25",
)
BOOT_UNITS = (
    "2pny-eventd.service", "2pny-network-manager.service",
    "2pny-network-core.service", "2pny-network-online.service",
    "2pny-mdns-alias.service", "2pny-mdns-guard.service",
    "2pny-wifi-retry-reconcile.service", "2pnyd.service",
    "2pny-hardware-manager.service", "2pny-hardware-detect.service",
    "2pny-mmdvmhost.service", "2pny-profile-autostart.service",
    "2pny-operational-restore.service", "2pny-operational-apply.path",
    "2pny-display-detect.path", "2pny-display-core.service",
    "2pny-display-reconcile.service", "2pny-display-apply-request.path",
)
# TEST-2 delegates AP/DHCP to its network core, not the default daemons.
MASKED_UNITS = (
    "hostapd.service", "dnsmasq.service", "NetworkManager-wait-online.service",
    "2pny-firstboot.service", "2pny-setup-watch.service",
)
REQUIRED = (
    "usr/share/2pny/wizard.html", "usr/share/2pny/protocols.html",
    "usr/share/2pny/radioid.html", "usr/share/2pny/rf-access.html",
    "usr/share/2pny/network/hostapd.template",
    "usr/share/2pny/network/dnsmasq-ap.template",
    "usr/local/sbin/2pny-network-core", "usr/local/sbin/2pny-wifi-profiles",
    "usr/local/libexec/pu2pny/2pny-network-manager",
    "etc/systemd/system/2pny-network-core.service",
    "etc/systemd/system/2pny-mmdvmhost.service",
)


def copy_runtime(baseline, target):
    baseline, target = baseline.resolve(), target.resolve()
    if baseline == Path("/") or target == Path("/") or baseline == target or baseline in target.parents:
        raise ValueError("Expected distinct TEST-2 and staging roots")
    if (baseline / "etc/2pny/v2-build").read_text().strip() != "PU2PNY-V2-TEST-2":
        raise ValueError("Expected an approved TEST-2 filesystem")
    for name in REQUIRED:
        if not (baseline / name).is_file():
            raise ValueError(f"TEST-2 is missing {name}")
    for pattern in RUNTIME:
        for source in sorted(baseline.glob(pattern)):
            name = source.relative_to(baseline)
            # Previous build snapshots and bytecode are not runtime inputs.
            if not source.is_file() or source.is_symlink() or any(
                ".pre-" in part or part.endswith((".bak", ".pyc")) or part == "__pycache__"
                for part in name.parts
            ):
                continue
            if not source.resolve().is_relative_to(baseline):
                raise ValueError(f"Source escapes TEST-2: {name}")
            dest = target / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
    for name in GATEWAYS:
        source = baseline / "usr/local/bin" / name
        if source.is_symlink() or not source.is_file():
            raise ValueError(f"Missing expected TEST-2 executable: {name}")
        header = subprocess.check_output(["readelf", "-hA", source], text=True)
        if not re.search(r"Machine:\s+ARM\s*$", header, re.MULTILINE):
            raise ValueError(f"Unexpected architecture: {name}")
        if name == "2pny-direct-core":
            build_info = subprocess.check_output(["go", "version", "-m", source], text=True)
            if not re.search(r"\bGOARM=6\b", build_info):
                raise ValueError(f"Unexpected Go ARM target: {name}")
        elif not re.search(r"Tag_CPU_arch:\s+v6(?:KZ?|T2)?\s*$", header, re.MULTILINE):
            raise ValueError(f"Executable does not target ARMv6: {name}")
        dest = target / "usr/local/bin" / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)


    # The original OLED/LCD code uses the SMBus class. Buildroot packages the
    # compatible Python implementation as smbus2; keep the I2C calls unchanged.
    for name in ("usr/local/sbin/2pny-display-core", "usr/local/libexec/pu2pny/i2c-505.py"):
        script = target / name
        code = script.read_text()
        if code.count("import smbus\n") != 1:
            raise ValueError(f"Expected one SMBus import in {name}")
        script.write_text(code.replace("import smbus\n", "import smbus2 as smbus\n"))

    unit_root = target / "etc/systemd/system"
    # Keep the MQTT listener on localhost, using the baseline config.
    mqtt = unit_root / "mosquitto.service.d/20-pu2pny.conf"
    mqtt.parent.mkdir(exist_ok=True)
    mqtt.write_text("[Service]\nExecStart=\n"
                    "ExecStart=/usr/sbin/mosquitto -c /etc/mosquitto/conf.d/pu2pny-local.conf\n")
    wants = unit_root / "multi-user.target.wants"
    wants.mkdir(exist_ok=True)
    for name in BOOT_UNITS:
        if not (unit_root / name).is_file():
            raise ValueError(f"Missing boot unit: {name}")
        (wants / name).symlink_to(Path("..") / name)
    for name in MASKED_UNITS:
        if not (baseline / "etc/systemd/system" / name).is_symlink():
            raise ValueError(f"Expected a masked TEST-2 unit: {name}")
        (unit_root / name).symlink_to("/dev/null")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("baseline", type=Path)
    parser.add_argument("overlay", type=Path)
    args = parser.parse_args()
    copy_runtime(args.baseline, args.overlay)
    print("TEST2_RUNTIME_STAGED")
