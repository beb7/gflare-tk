import sys
from cx_Freeze import setup, Executable
from os import environ

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
bdist_msi_options = {'data': msi_data, 'install_icon': "greenflare-icon-256x256.ico"}

# MacOS
# bdist_mac_options = {'iconfile': 'greenflare-icon-64x64.icns', 'bundle_name': 'greenflare', 'custom_info_plist': 'Info.plist', 'include_resources': [('/usr/local/Cellar/tcl-tk/8.6.10/lib/tcl8.6', 'tcl8.6'), ('/usr/local/Cellar/tcl-tk/8.6.10/lib/tk8.6', 'tk8.6')]}
bdist_mac_options = {'iconfile': 'greenflare-icon-64x64.icns', 'bundle_name': 'greenflare', 'custom_info_plist': 'Info.plist'}
bdist_dmg_options = {'applications_shortcut': True, "volume_label": "Greenflare SEO Crawler"}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None

targetName="greenflare"
if sys.platform == "win32":
	# base = "Win32GUI"
	targetName="greenflare.exe"
elif sys.platform == "darwin":
    print("Exclude tkinter on macos and rely on an external install ...")
    build_exe_options["exclude"] = ["tkinter"]
#     print("Applying tcl-tk hack ...")
#     environ['TK_LIBRARY'] = '/usr/local/Cellar/tcl-tk/8.6.10/lib/tk8.6/'
#     environ['TCL_LIBRARY'] = '/usr/local/Cellar/tcl-tk/8.6.10/lib/tcl8.6/' 

target = Executable(
    script="greenflare.py",
    base=base,
    icon="greenflare-icon-256x256.ico",
    targetName=targetName
    )

setup(  name = "Greenflare SEO Crawler",
        version = "0.64",
        author = "Geenflare",
        description = "Scalable, low memory SEO crawler",
        options = {"build_exe": build_exe_options, "bdist_msi": bdist_msi_options, "bdist_mac": bdist_mac_options, "bdist_dmg": bdist_dmg_options},
        executables = [target])
