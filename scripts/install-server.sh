#!/bin/bash

# This is a simple DOTM installer for Debian/Ubuntu

readonly PREFIX=${1-/usr/local}

if [ ! -f configure.ac ]; then
	echo "ERROR: Please run this script from source root!"
	exit 1
fi

if ! lsb_release -i | egrep 'Debian|Ubuntu|Mint' >/dev/null; then
	echo "ERROR: Currently only Debian/Ubuntu are supported by this script!"
	echo "Please contribute installation instructions for other distributions!"
	exit 1
fi
	
echo "### Installing dependencies..."
apt-get install netcat redis-server python-redis python-bottle python-requests python-geoip geoip-database-contrib python-daemon curl

echo "### Compiling and installing ($PREFIX)..."
autoreconf -i
./configure --prefix=$PREFIX
make clean && make && make install
if [ $? -ne 0 ]; then
	echo "ERROR: Compiling/installation failed!"
	exit 1
fi
 
echo "### Installing backend init script..."
cp backend/dotm_backend.rc /etc/init.d/dotm_backend
chmod a+x /etc/init.d/dotm_backend
update-rc.d dotm_backend defaults
/etc/init.d/dotm_backend restart

echo "### Installing api init script..."
cp backend/dotm_api.rc /etc/init.d/dotm_api
chmod a+x /etc/init.d/dotm_api
update-rc.d dotm_api defaults
/etc/init.d/dotm_api restart

echo "### Setting up Apache config..."
ln -s /usr/local/share/dotm_frontend/apache-2.4.conf /etc/apache2/conf-enabled/dotm.conf
/etc/init.d/apache2 reload

echo "### Installing state fetcher cron..."
cp aggregator/cron_dotm_aggregator /etc/cron.d/
