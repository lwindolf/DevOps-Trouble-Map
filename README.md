[![Build Status](https://travis-ci.org/lwindolf/DevOps-Trouble-Map.svg?branch=master)](https://travis-ci.org/lwindolf/DevOps-Trouble-Map)


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

The DOTM server has the following dependencies

- netcat
- redis-server
- Python modules
  - redis
  - bottle
  - requests
  - configparser

To automatically install the server including its dependencies on Debian/Ubuntu 
simply run

    scripts/install-server.sh

   
Agent Installation
------------------

The DOTM agent has the following dependencies

- glib 2.0
- libevent2

To automatically install the dotm_node agent simply run

    scripts/install-agent.sh

Of course as the agent is to be run on all monitored systems its single binary
should be distributed to all nodes using your favourite automation tool.


Software Stack
--------------

DOTM will use the following technologies

- Simple remote agent "dotm_node" (in C using libevent and glib)
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
  * 'last_connection' => &lt;timestamp>
  * 'last_seen' => &lt;timestamp>
  * 'direction' => &lt;in/out>
- dotm::services::&lt;node name>::&lt;port> (hash with the following key values):
  * 'process' => &lt;string>
  * 'last_seen' => &lt;timestamp>
- dotm::checks::nodes (hash with the following key values):
  * &lt;node name> => &lt;string> (JSON containing basic status information:
      {
          "status": "UP",
          "last_check": &lt;timestamp>,
          "last_status_change": &lt;timestamp>,
          "status_information": "hostname01 status information"
      })
  * ...
- dotm::checks::services (hash with the following key values):
  * &lt;node name> => &lt;string> (JSON containing all associated checks:
      {
          "Service01 name": {
              "status": "OK",
              "last_check": &lt;timestamp>,
              "last_status_change": &lt;timestamp>,
              "status_information": "Service01 status information"
          },
          "Service02 name": {
              "status": "CRITICAL",
              "last_check": &lt;timestamp>,
              "last_status_change": &lt;timestamp>,
              "status_information": "Service02 status information"
          },
      })
  * ...
- dotm::checks::config (hash with the following key values):
  * 'last_updated' => &lt;timestamp>
- dotm::checks::config::update_running (key with set expire flag used as a lock during monitoring data reload)

