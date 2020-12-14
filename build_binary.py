import sys
from cx_Freeze import setup, Executable
from os import environ, getcwd, path
from greenflare.core.defaults import Defaults

sys.path.append(getcwd() + path.sep + 'greenflare')
print(sys.path)
print(getcwd())

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {"include_files": ["greenflare/resources/"]}


# GUI applications require a different base on Windows (the default is for a
# console application).
base = None

targetName = "greenflare"
if sys.platform == "win32":
    base = "Win32GUI"
    targetName = "greenflare.exe"

target = Executable(
    script='greenflare/app.py',
    base=base,
    icon='greenflare/resources/greenflare-icon-32x32.ico',
    targetName=targetName
)

setup(name='Greenflare SEO Crawler',
      version=Defaults.version,
      author='Benjamin Görler',
      description='Greenflare SEO Crawler',
      options={'build_exe': build_exe_options},
      executables=[target])
