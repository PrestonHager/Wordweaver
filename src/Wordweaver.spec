# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None

# Platform-specific settings
if sys.platform == 'darwin':
    icon_file = 'icons/wordweaver.icns'
elif sys.platform == 'win32':
    icon_file = 'icons/wordweaver.ico'
else:
    icon_file = 'icons/wordweaver.ico'

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('VERSION', '.'),
        ('icons', 'icons'),
    ],
    hiddenimports=[
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'platformdirs',
        'pyperclip',
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
    name='Wordweaver',
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
    icon=icon_file,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Wordweaver',
)

# macOS app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='Wordweaver.app',
        icon='icons/wordweaver.icns',
        bundle_identifier='com.prestonhager.wordweaver',
        info_plist={
            'CFBundleShortVersionString': Path('VERSION').read_text().strip(),
            'CFBundleVersion': Path('VERSION').read_text().strip(),
            'NSHighResolutionCapable': True,
            'LSMinimumSystemVersion': '10.13',
        },
    )
