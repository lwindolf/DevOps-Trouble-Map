DevOps Trouble Map
==================

Why is so much knowledge about your IT architecture implicit? Why do we need to check what is running during an incident to know about the state of the system? Which components are affected by this Nagios alert? Why does no one ever update the system documentation?

When you care about above questions try "DevOps Trouble Map" (short DOTM) which

- doesn't reinvent monitoring, but integrates with Nagios, Icinga & Co.
- provides automatic *layer 4 system archictecture charts*.
- maps alerts live into system architecture charts.

Note that the project is pre-alpha right now.

Installation
------------

On Debian/Ubuntu:

     apt-get install netcat redis-server python-redis python-bottle python-requests python-configparser

Alternatively install the Python dependencies with PIP:

     pip3 install bottle
     pip3 install -r dotm-monitor/requirements.txt
   
FIXME: How and where to install all the stuff

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
