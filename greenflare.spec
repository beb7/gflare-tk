# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(['greenflare.py'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='greenflare',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='greenflare.app')
app = BUNDLE(coll,
             name='greenflare.app',
             icon='greenflare-icon-64x64.icns',
             bundle_identifier='io.greenflare',
             info_plist={
                'NSPrincipalClass': 'NSApplication',
                'NSAppleScriptEnabled': False,
                'CFBundleDocumentTypes': [
                    {
                        'CFBundleTypeName': 'GreenflareDB',
                        'CFBundleTypeIconFile': 'greenflare-icon-64x64.icns',
                        'LSItemContentTypes': ['io.greenflare.gflaredb'],
                        'LSHandlerRank': 'Owner'
                    }
                ]
             }
            )

## Make app bundle double-clickable
import plistlib
from pathlib import Path
app_path = Path(app.name)

# read Info.plist
with open(app_path / 'Contents/Info.plist', 'rb') as f:
    pl = plistlib.load(f)

# write Info.plist
with open(app_path / 'Contents/Info.plist', 'wb') as f:
    pl['CFBundleExecutable'] = 'wrapper'
    plistlib.dump(pl, f)

# write new wrapper script
shell_script = """#!/bin/bash
DIR=$(cd "$(dirname '$0')"; pwd)
open $DIR/greenflare"""
with open(app_path / 'Contents/MacOS/wrapper', 'w') as f:
    f.write(shell_script)

# make it executable
(app_path  / 'Contents/MacOS/wrapper').chmod(0o755)