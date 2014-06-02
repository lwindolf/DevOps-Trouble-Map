DevOps Trouble Map
==================

Why is so much knowledge about your IT architecture implicit? Why do we need to check what is running during an incident to know about the state of the system? Which components are affected by this Nagios alert? Why does no one ever update the system documentation?

When you care about above questions try "DevOps Trouble Map" (short DOTM) which

- doesn't reinvent monitoring, but integrates with Nagios, Icinga & Co.
- provides automatic *layer 4 system archictecture charts*.
- maps alerts live into system architecture charts.

Note that the project is pre-alpha right now.

Server Installation
--------------------

On Debian/Ubuntu:

     apt-get install netcat redis-server python-redis python-bottle python-requests python-configparser

Alternatively install the Python dependencies with PIP:

     pip3 install bottle
     pip3 install -r dotm-monitor/requirements.txt
   
FIXME: How and where to install all the stuff

To install the frontend code along with the provided example Apache 2.4 config on a Debian like setup:

    cp -r dotm-frontend/ /usr/local/share/dotm-frontend
    ln -s /usr/local/share/dotm-frontend/apache-2.4.conf /etc/apache2/conf-enabled/dotm.conf
    /etc/init.d/apache2 reload


Client Installation
-------------------

The dotm-node client is to be installed on all monitored servers. It can be build as following

    cd dotm-node/
    autoreconf -i
    ./configure
    make
    make install

The client is comprised of only a single binary "dotm-node" that should be shipped by any automation tool you run.

FIXME: Currently there is no init script provided.


Software Stack
--------------

DOTM will use the following technologies

- Simple remote agent "dotm-node" (in C using libevent and glib)
- Redis as backend store
- Python bottle with Jinja templating
- JSON backend data access
- any jQuery library for rendering



![architecture overview](doc/dotm-architecture.png?raw=true)

Redis Data Schema
-----------------

So far the following relations are probably needed:

![entity overview](doc/dotm-er.png?raw=true)

Right now the following relation namespaces are used in Redis

- dotm::nodes (list of node names, resovable via local resolver and to be identical with remote hostname)
- dotm::connections::&lt;node name>::&lt;port>::&lt;remote node/IP> (hash with the following key values):
  * 'process' => &lt;string>
  * 'connections' => &lt;int>
  * 'last_connection' =>  &lt;timestamp>
  * 'last_seen' => &lt;timestamp>
- dotm::services::&lt;node name>::&lt;port> (hash with the following key values):
  * 'process' => &lt;string>
  * 'last_seen' => &lt;timestamp>
