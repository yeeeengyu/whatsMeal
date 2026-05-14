# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

import PySide6

block_cipher = None
pyside6_dir = Path(PySide6.__file__).resolve().parent
pyside6_plugins_dir = pyside6_dir / "plugins"
qt_plugin_binaries = [
    (
        str(plugin_path),
        str(Path("PySide6") / "plugins" / plugin_path.parent.relative_to(pyside6_plugins_dir)),
    )
    for plugin_path in pyside6_plugins_dir.rglob("*.dll")
]

a = Analysis(
    ["app/main.py"],
    pathex=["."],
    binaries=qt_plugin_binaries,
    datas=[],
    hiddenimports=[
        "app.api",
        "app.config",
        "app.diagnostics",
        "app.popup",
        "app.tray",
        "app.workers",
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
        "httpx",
        "dotenv",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=["app/pyinstaller_qt_plugins.py"],
    excludes=[
        "PyQt5",
        "PyQt6",
        "PySide2",
        "PySide6.Qt3DAnimation",
        "PySide6.Qt3DCore",
        "PySide6.Qt3DExtras",
        "PySide6.Qt3DInput",
        "PySide6.Qt3DLogic",
        "PySide6.Qt3DRender",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="WhatsMeal",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
