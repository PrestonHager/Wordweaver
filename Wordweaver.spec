# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

datas = [('src/icons/', 'icons/'), ('VERSION', '.')]
datas += collect_data_files('ipapy')


a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Wordweaver',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['src/icons/wordweaver.ico'],
)

# NOTE: The .app bundle is experimental code and may not work as expected
app = BUNDLE(
    exe,
    name='Wordweaver.app',
    icon='src/icons/wordweaver.icns',
    bundle_identifier='xyz.prestonhager.wordweaver',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSAppleScriptEnabled': False,
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeName': 'Wordweaver Project',
                'CFBundleTypeIconFile': 'src/icons/wordweaver.ico',
                'LSItemContentTypes': ['xyz.prestonhager.wordweaver.wordweaverproject'],
                'LSHandlerRank': 'Owner',
            }
        ]
    },
)
