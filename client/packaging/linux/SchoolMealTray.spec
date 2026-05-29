# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules


block_cipher = None
repo_root = Path(SPECPATH).resolve().parents[2]
tray_root = repo_root / "school-meal-tray"
gi_hiddenimports = collect_submodules("gi")

a = Analysis(
    [str(tray_root / "meal_tray.py")],
    pathex=[str(tray_root)],
    binaries=[],
    datas=[],
    hiddenimports=gi_hiddenimports + [
        "dotenv",
        "gi.repository.AyatanaAppIndicator3",
        "gi.repository.AppIndicator3",
        "gi.repository.Gdk",
        "gi.repository.GLib",
        "gi.repository.Gtk",
        "requests",
    ],
    hookspath=[],
    hooksconfig={
        "gi": {
            "module-versions": {
                "AyatanaAppIndicator3": "0.1",
                "AppIndicator3": "0.1",
                "Gtk": "3.0",
                "Gdk": "3.0",
            },
        },
    },
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="SchoolMealTray",
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
