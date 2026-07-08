# -*- mode: python ; coding: utf-8 -*-

import os
import sys

from PyInstaller.utils.hooks import collect_submodules

block_cipher = None
spec_root = os.path.dirname(os.path.abspath(SPEC))

style_dir = os.path.join(spec_root, 'app', 'styles')
datas = [
    (os.path.join(style_dir, 'dark.qss'), os.path.join('app', 'styles')),
    (os.path.join(style_dir, 'light.qss'), os.path.join('app', 'styles')),
]

hiddenimports = [
    'pyte',
    'pyte.screens',
    'pyte.streams',
    'pyte.graphics',
    'app.chip_catalog',
    'bds.wave_graphics_patch',
    'serial',
    'serial.tools.list_ports',
]
hiddenimports += collect_submodules('pylink')

is_windows = sys.platform.startswith('win')

a = Analysis(
    ['main.py'],
    pathex=[spec_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['scipy'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

if is_windows:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='rtt_t2',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon='tool.ico',
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='rtt_t2',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='rtt_t2',
)
