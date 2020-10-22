#!/bin/sh

BUILD_DIR="${HOME}/python-build"
PY_ENV="${HOME}/.venv/gflare"

if [ ! -d "$BUILD_DIR" ]; then

	mkdir ~/Universal
	cd ~/Universal
	curl -O https://www.python.org/ftp/python/3.8.6/Python-3.8.6.tgz
	tar -xvf Python-3.8.6.tgz
	cd Python-3.8.6/Mac/BuildScript

	echo "Set TCL version from 8.6.8 to 8.6.10"
	sed -i.bak 's,ftp://ftp.tcl.tk/pub/tcl//tcl8_6/tcl8.6.8-src.tar.gz,ftp://ftp.tcl.tk/pub/tcl//tcl8_6/tcl8.6.10-src.tar.gz,g' build-installer.py
	sed -i.bak 's,ftp://ftp.tcl.tk/pub/tcl//tcl8_6/tcl8.6.8-src.tar.gz,ftp://ftp.tcl.tk/pub/tcl//tcl8_6/tcl8.6.10-src.tar.gz,g' build-installer.py
	mv build-installer.py.bak build-installer.py
	sed -i.bak 's,81656d3367af032e0ae6157eff134f89,97c55573f8520bcab74e21bfd8d0aadc,g' build-installer.py
	sed -i.bak 's,81656d3367af032e0ae6157eff134f89,97c55573f8520bcab74e21bfd8d0aadc,g' build-installer.py
	mv build-installer.py.bak build-installer.py
	sed -i.bak 's,name="Tcl 8.6.8",name="Tcl 8.6.10",g' build-installer.py
	sed -i.bak 's,name="Tcl 8.6.8",name="Tcl 8.6.10",g' build-installer.py
	mv build-installer.py.bak build-installer.py

	echo "Set TK version from 8.6.8 to 8.6.10"
	sed -i.bak 's,ftp://ftp.tcl.tk/pub/tcl//tcl8_6/tk8.6.8-src.tar.gz,ftp://ftp.tcl.tk/pub/tcl//tcl8_6/tk8.6.10-src.tar.gz,g' build-installer.py
	sed -i.bak 's,ftp://ftp.tcl.tk/pub/tcl//tcl8_6/tk8.6.8-src.tar.gz,ftp://ftp.tcl.tk/pub/tcl//tcl8_6/tk8.6.10-src.tar.gz,g' build-installer.py
	mv build-installer.py.bak build-installer.py
	sed -i.bak 's,5e0faecba458ee1386078fb228d008ba,602a47ad9ecac7bf655ada729d140a94,g' build-installer.py
	sed -i.bak 's,5e0faecba458ee1386078fb228d008ba,602a47ad9ecac7bf655ada729d140a94,g' build-installer.py
	mv build-installer.py.bak build-installer.py
	sed -i.bak 's,name="Tk 8.6.8",name="Tk 8.6.10",g' build-installer.py
	sed -i.bak 's,name="Tk 8.6.8",name="Tk 8.6.10",g' build-installer.py
	mv build-installer.py.bak build-installer.py

	echo "Disable TCL/TK patch"
	sed -i.bak 's#"tk868_on_10_8_10_9.patch",##g' build-installer.py
	sed -i.bak 's#"tk868_on_10_8_10_9.patch",##g' build-installer.py
	mv build-installer.py.bak build-installer.py

	brew install sphinx-doc
	echo "Add sphinx to PATH"
	sed -i.bak "s,'/bin:/sbin:/usr/bin:/usr/sbin','/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/opt/sphinx-doc/bin',g" build-installer.py
	sed -i.bak "s,'/bin:/sbin:/usr/bin:/usr/sbin','/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/opt/sphinx-doc/bin',g" build-installer.py
	mv build-installer.py.bak build-installer.py

	echo "Starting build ..."
	mkdir -p $BUILD_DIR
	python2.7 build-installer.py --universal-archs=intel-64 --dep-target=10.9 --build-dir=$BUILD_DIR

fi

echo "Installing Python ..."

cd $BUILD_DIR
cd installer/Python.mpkg/Contents/Packages
sudo pax -z -p e -r -f PythonFramework-3.8.pkg/Contents/Archive.pax.gz
sudo mkdir -p /Library/Frameworks/Python.framework/
sudo cp -r Versions /Library/Frameworks/Python.framework/
sudo ./PythonInstallPip-3.8.pkg/Contents/Resources/postflight


if [ ! -d "$PY_ENV" ]; then

	echo "Creating virtual environment for Python ..."
	/Library/Frameworks/Python.framework/Versions/3.8/bin/python3 -m venv $PY_ENV

	echo "Activating virtual environment ..."
	source $PY_ENV/bin/activate
fi
