#!/bin/bash

# This is a simple DOTM agent installer for Debian/Ubuntu

readonly PREFIX=${1-/usr/local}

if [ ! -f configure.ac ]; then
	echo "ERROR: Please run this script from source root!"
	exit 1
fi

if ! lsb_release -i | egrep 'Debian|Ubuntu' >/dev/null; then
	echo "ERROR: Currently only Debian/Ubuntu are supported by this script!"
	echo "Please contribute installation instructions for other distributions!"
	exit 1
fi

cd agent || exit 1
	
echo "### Compiling and installing ($PREFIX)..."
autoreconf -i
./configure --prefix=$PREFIX
make clean && make && make install
if [ $? -ne 0 ]; then
	echo "ERROR: Compiling/installation failed!"
	exit 1
fi
 
echo "### Activating agent ..."
update-rc.d dotm_node defaults
/etc/init.d/dotm_node restart
