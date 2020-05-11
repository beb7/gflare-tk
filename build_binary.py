import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {"include_files": ["greenflare-icon-64x64.png", "greenflare-icon-256x256.ico"]}



shortcut_table = [
    ("DesktopShortcut",        # Shortcut
     "DesktopFolder",          # Directory_
     "Greenflare SEO Crawler",  # Name
     "TARGETDIR",              # Component_
     "[TARGETDIR]greenflare.exe",# Target
     None,                     # Arguments
     None,                     # Description
     None,                     # Hotkey
     "",                     # Icon
     0,                     # IconIndex
     None,                     # ShowCmd
     'TARGETDIR'               # WkDir
     )
    ]

# Now create the table dictionary
msi_data = {"Shortcut": shortcut_table}

# Change some default MSI options and specify the use of the above defined tables
bdist_msi_options = {'data': msi_data, 'install_icon': "icons/greenflare-icon-256x256.ico"}

# MacOS
bdist_mac_options = {'iconfile': 'icons/greenflare-icon-64x64.icns', 'bundle_name': 'greenflare'}
bdist_dmg_options = {'applications_shortcut': True, "volume_label": "Greenflare SEO Crawler"}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
	base = "Win32GUI"
	targetName="greenflare.exe"
else:
	targetName="greenflare"


target = Executable(
    script="greenflare.py",
    base=base,
    icon="icons/greenflare-icon-256x256.ico",
    targetName=targetName
    )

setup(  name = "Greenflare SEO Crawler",
        version = "0.64",
        author = "Geenflare",
        description = "Scalable, low memory SEO crawler",
        options = {"build_exe": build_exe_options, "bdist_msi": bdist_msi_options, "bdist_mac": bdist_mac_options, "bdist_dmg": bdist_dmg_options},
        executables = [target])
