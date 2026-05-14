# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


block_cipher = None
project_root = Path(SPECPATH).resolve().parents[1]

a = Analysis(
    [str(project_root / "app" / "main.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=[],
    hiddenimports=[
        "app.api",
        "app.config",
        "app.diagnostics",
        "app.tray",
        "app.web_popup",
        "httpx",
        "dotenv",
        "PIL",
        "pyperclip",
        "pystray",
        "pystray._darwin",
        "webview",
        "webview.platforms.cocoa",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="WhatsMeal",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
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
    upx=False,
    upx_exclude=[],
    name="WhatsMeal",
)
app = BUNDLE(
    coll,
    name="WhatsMeal.app",
    icon=None,
    bundle_identifier="kr.hs.gbsm.whatsmeal",
    info_plist={
        "CFBundleName": "WhatsMeal",
        "CFBundleDisplayName": "WhatsMeal",
        "CFBundleShortVersionString": "0.1.0",
        "CFBundleVersion": "0.1.0",
        "LSUIElement": True,
        "NSHighResolutionCapable": True,
    },
)
