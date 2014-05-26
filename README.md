DevOps Trouble Map
==================

Why is so much knowledge about your IT architecture implicit? Why do we need to check what is running during an incident to know about the state of the system? Which components are affected by this Nagios alert? Why does no one ever update the system documentation?

When you care about above questions try "DevOps Trouble Map" (short DOTM) which

- doesn't reinvent monitoring, but integrates with Nagios, Icinga & Co.
- provides automatic *layer 4 system archictecture charts*.
- maps alerts live into system architecture charts.

Note that the project is pre-alpha right now.

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

- dotm::nodes (list of node names, resovable via local resolver and to be identical with remote hostname)
- dotm::services::&lt;node name>::&lt;port>::&lt;remote node/IP> (hash: 'process' => &lt;string>, 'connections' => &lt;int>, 'last_connection' =>  &lt;timestamp>, 'last_seen' => &lt;timestamp>)
