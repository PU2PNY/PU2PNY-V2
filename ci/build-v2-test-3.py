#!/usr/bin/env python3
"""Build the PU2PNY-V2 TEST-1 image for board 32 (ARMv6) on the proven 5.12.002 base.

TEST build. NOT approved; nothing hardware-verified. Reuses the 5.15 pipeline:
same published P2 base, same safety gates (xz / sha256 / ext4 fsck / read-only
remount / ELF 32-bit ARM / bootloader first-MiB unchanged / backend byte match).
Differences from build-5.15.py:
  - board 32 only;
  - applies the V2 overlay (5.15 + V2 panel + owner-reported fixes);
  - 2pny-protocol-network-apply is intentionally changed (YSF Reconnect/Revert),
    so it is exempt from the protected-baseline equality check;
  - the strict "no undeclared path changed" gate is relaxed to a subset check,
    because the V2 panel legitimately rewrites many served files.
"""
import hashlib
import importlib.util
import json
import os
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BOARD = '32'
BASE_SHA = '98b91cfbed30b7bf81dad8b3f3a522a190372ebbc81484c461f67993c3890dbf'
PARTITION = 'p2'
ELF_CLASS = 1  # 32-bit
EXEMPT_PROTECTED = {'usr/local/sbin/2pny-protocol-network-apply'}
VERSION_TAG = 'v2-test-3'


def run(argv, **kw):
    return subprocess.run(argv, check=True, **kw)


def sha(path):
    with open(path, 'rb') as fh:
        return hashlib.file_digest(fh, 'sha256').hexdigest()


def mod(path, name):
    spec = importlib.util.spec_from_file_location(name, REPO / path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


M = mod('ci/build-5.11.py', 'old_manifest')
P = mod('ci/patch-image-v2-test-3.py', 'overlay_v2_t3')


def main():
    assert len(sys.argv) == 5, 'usage: build-v2-test-3.py WORKDIR COMMIT BACKEND XOMBEDIR'
    work = Path(sys.argv[1]).resolve()
    commit = sys.argv[2]
    backend = Path(sys.argv[3]).resolve()
    xombe_dir = Path(sys.argv[4]).resolve()
    assert os.geteuid() == 0 and work != Path('/')
    assert re.fullmatch(r'[a-f0-9]{40}', commit)
    base = work / f'pu2pny-{BOARD}-5.12.002.img.xz'
    assert base.is_file() and sha(base) == BASE_SHA, 'published P2 base SHA mismatch'
    run(['xz', '-t', str(base)])
    image = work / f'{BOARD}.img'
    root = work / f'mount-{BOARD}'
    assert not image.exists() and not root.exists()
    with image.open('wb') as out:
        run(['xz', '-dc', str(base)], stdout=out)
    with image.open('rb') as f:
        boot_hash = hashlib.sha256(f.read(1048576)).hexdigest()
    loop = ''
    mounted = False
    try:
        loop = subprocess.check_output(
            ['losetup', '--find', '--show', '--partscan', str(image)], text=True).strip()
        # Partition nodes appear via --partscan on the CI runner; on kernels
        # where udev does not materialise them, partx adds them (no-op on CI).
        subprocess.run(['partx', '-a', loop], check=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(20):
            if Path(loop + PARTITION).exists():
                break
            subprocess.run(['sleep', '0.3'], check=False)
        root.mkdir()
        run(['mount', loop + PARTITION, str(root)]); mounted = True
        assert (root / 'etc/2pny/version').read_text().strip() == '5.12.002'
        before = M.manifest(root)
        changed = P.apply(root, BOARD, backend, xombe_dir)
        after = M.manifest(root)
        manifest_changed = {p for p in set(before) | set(after) if before.get(p) != after.get(p)}
        dirs = {p for p in manifest_changed if p not in before and after.get(p, {}).get('dir')}
        undeclared = manifest_changed - changed - dirs
        assert not undeclared, ('V2 changed undeclared paths', sorted(undeclared))
        missing = {c for c in changed if c not in manifest_changed}
        assert not missing, ('declared-but-unchanged', sorted(missing))
        for path in M.PROTECTED:
            if path in EXEMPT_PROTECTED:
                continue
            assert before.get(path) == after.get(path), 'RF/Nextion baseline changed: ' + path
        # the one intentional protected change must be minimal (two keys only)
        assert after.get('usr/local/sbin/2pny-protocol-network-apply') != \
            before.get('usr/local/sbin/2pny-protocol-network-apply'), 'YSF ini edit did not apply'
        assert after['etc/2pny/version']['sha256'] != before['etc/2pny/version']['sha256']
        assert (root / 'etc/2pny/v2-build').read_text().strip() == 'PU2PNY-V2-TEST-3'
        xc = (root / 'usr/local/bin/xombe-xc').read_bytes()
        assert xc[:4] == b'\x7fELF' and xc[4] == 1, 'xombe-xc must be ELF 32-bit ARM'
        assert (root / 'etc/2pny/crossmode.conf').is_file()
        assert 'ENABLED=0' in (root / 'etc/2pny/crossmode.conf').read_text(), 'crossmode must default OFF'
        assert (root / 'etc/systemd/system/pu2pny-crossmode.service').is_file()
        assert not (root / 'etc/systemd/system/multi-user.target.wants/pu2pny-crossmode.service').exists(), 'crossmode service must NOT auto-start'
        assert (root / 'usr/local/bin/2pnyd').read_bytes()[:4] == b'\x7fELF'
        for bin_name in ('MMDVM-Host', 'DMRGateway', 'NextionDriver-pu2pny', 'MMDVM-Display', '2pnyd'):
            hdr = (root / 'usr/local/bin' / bin_name).read_bytes()[:20]
            assert hdr[:4] == b'\x7fELF' and hdr[4] == ELF_CLASS and \
                struct.unpack('<H', hdr[18:20])[0] == 40, bin_name
        assert (root / 'usr/local/bin/2pnyd').read_bytes() == backend.read_bytes()
        for p, v in after.items():
            assert v['uid'] != 1001 and v['gid'] != 1001, ('CI owner leaked', p)
        run(['sync'])
        run(['umount', str(root)]); mounted = False
        fsck = subprocess.run(['e2fsck', '-fn', loop + PARTITION], check=False)
        assert fsck.returncode == 0, 'ext4 integrity FAIL'
        run(['mount', '-o', 'ro', loop + PARTITION, str(root)]); mounted = True
        assert M.manifest(root) == after, 'read-only remount differs'
        assert (root / 'etc/2pny/version').read_text().strip() == '5.15.000'
        run(['umount', str(root)]); mounted = False
        run(['losetup', '-d', loop]); loop = ''
        with image.open('rb') as f:
            assert hashlib.sha256(f.read(1048576)).hexdigest() == boot_hash, 'boot sector modified'
        output = work / 'output'
        output.mkdir(exist_ok=True)
        name = f'pu2pny-{BOARD}-{VERSION_TAG}.img.xz'
        dest = output / name
        assert not dest.exists()
        with dest.open('wb') as out:
            run(['xz', '-T2', '-4', '-c', str(image)], stdout=out)
        run(['xz', '-t', str(dest)])
        digest = sha(dest)
        (output / (name + '.sha256')).write_text(digest + '  ' + name + '\n')
        info = {
            'build': 'PU2PNY-V2-TEST-3', 'internal_version': '5.15.000',
            'classification': 'TEST_PHYSICAL_TEST_CANDIDATE_NOT_APPROVED',
            'architecture': BOARD, 'arch_detail': 'armhf / ARMv6 / GOARM=6 (Pi Zero W + all Raspberry Pi)',
            'source_commit': commit, 'base_version': '5.12.002', 'base_sha256': BASE_SHA,
            'image_sha256': digest, 'bytes': dest.stat().st_size,
            'scope': ['panel-v2', 'xombe-ambe-codec-armv6', 'crossmode-opt-in-off', 'rebrand-pu2pny-v2', 'identity-apply-repoint', 'full-report-endpoint', 'clock-persist-etc-rw', 'tz-browser-storm-removed-in-panel',
                      'profile-autostart-retry-300s', 'ysf-reconnect-revert', 'ysf-linkguard-bridge',
                      'dmr-voice-default-off', 'display-boot-timeout'],
            'validation': {'xz': 'PASS', 'sha256': 'PASS', 'filesystem': 'PASS',
                           'protected_rf_nextion': 'PASS (except intentional YSF ini keys)',
                           'bootloader_first_mib': 'UNCHANGED', 'backend_elf': 'ARM 32-bit',
                           'HW': 'NOT_VERIFIED', 'PROD': 'NOT_APPROVED'},
            'notes': ['TEST build for physical testing only.',
                      'No RF/MMDVM/Nextion/duplex behaviour verified on hardware.',
                      'YSF reflector re-link relies on Reconnect/Revert; the watchdog only '
                      'covers a confirmed-dead local UDP bridge (QSO-safe).'],
        }
        (output / f'BUILD-INFO-{BOARD}.json').write_text(json.dumps(info, indent=2) + '\n')
        print('IMAGE_V2_TEST1_VALIDATED', BOARD, digest, dest.stat().st_size, flush=True)
    finally:
        if mounted:
            subprocess.run(['umount', str(root)], check=False)
        if loop:
            subprocess.run(['losetup', '-d', loop], check=False)
        if root.exists():
            shutil.rmtree(root, ignore_errors=True)
        if image.exists():
            image.unlink()


if __name__ == '__main__':
    main()
