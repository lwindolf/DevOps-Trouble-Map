[![Build Status](https://travis-ci.org/lwindolf/DevOps-Trouble-Map.svg?branch=master)](https://travis-ci.org/lwindolf/DevOps-Trouble-Map)


DevOps Trouble Map
==================

Why is so much knowledge about your IT architecture implicit? Why do we need to check what is running during an incident to know about the state of the system? Which components are affected by this Nagios alert? Why does no one ever update the system documentation?

When you care about above questions try "DevOps Trouble Map" (short DOTM) which

- doesn't reinvent monitoring, but integrates with Nagios, Icinga & Co.
- provides automatic *layer 4 system archictecture charts*.
- maps alerts live into system architecture charts.

Note that the project is pre-alpha right now. Here are some impressions what the code does so far:

Mapping of Nagios alerts to detected services (note the 2nd column in the alert table):

![Alert Mapping](doc/dotm-screenshot-alerts.png?raw=true)

Those Nagios "service check" to "service" mappings are fuzzy logic regular expressions. DOTM brings presets and allows the user to refine them as needed. The fact that those mappings are actually necessary indicates the intrinsic problem of the missing service relation in Nagios, which mixes the concepts of "services" and "service checks". Only with "services" (which we detect based on open TCP ports) we can auto-detect impact.

![Service Mapping](doc/dotm-screenshot-service-mapping.png?raw=true)

Additionally to the Nagios node and service states DOTM aggregates the current connection details from the nodes. It remembers old connections to be able to see service usage transitions and create alarms for long unused or suddenly disconnected services. This helps with typical questions like "do we actually still need this X" or uncover a wrong firewall configuration.

![Connection and Service Tracking](doc/dotm-screenshot-connections.png?raw=true)

Finally those two sources of information are combined into a very simple "graphical" representation:

![Node Graph](doc/dotm-screenshot-nodegraph.png?raw=true)

In this "node graph" color coding indicates Nagios alerts as well as service states only discovered by DOTM.


Server Installation
--------------------

The DOTM server has the following dependencies

- netcat
- redis-server
- MaxMind GeoIP Lite (optional)
- Python2 modules
  - redis
  - bottle
  - requests
  - GeoIP

To automatically install the server including its dependencies on Debian/Ubuntu 
simply run

    scripts/install-server.sh

   
Agent Installation
------------------

The DOTM agent has the following dependencies

- glib-2.0
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
- Python2 bottle with Jinja templating
- JSON backend data access
- any jQuery library for rendering



![architecture overview](doc/dotm-architecture.png?raw=true)

Redis Data Schema
-----------------

So far the following relations are probably needed:

![entity overview](doc/dotm-er.png?raw=true)

Right now the following relation namespaces are used in Redis

- dotm::nodes (list of node names, resovable via local resolver and to be identical with remote hostname)
- dotm::nodes::&lt;node name>
  * 'last_fetch' => &lt;timestamp>
  * 'fetch_status' => &lt;'OK' or error message>
  * 'ips' => &lt;comma separated list of IPs>
  * 'service_alerts' => &lt;hash of service name - status tuples>
- dotm::connections::&lt;node name>::&lt;port>::&lt;remote node/IP> (hash):
  * 'process' => &lt;string>
  * 'connections' => &lt;int>
  * 'last_connection' => &lt;timestamp>
  * 'last_seen' => &lt;timestamp>
  * 'direction' => &lt;in/out>
  * 'remote_host' => &lt;IP or node name>
  * 'remote_port' => &lt;port number or 'high'>
  * 'local_port' => &lt;port number>
- dotm::services::&lt;node name>::&lt;port> (hash with the following key values):
  * 'process' => &lt;string>
  * 'last_seen' => &lt;timestamp>
- dotm::resolver::ip_to_node::&lt;IP> (string, &lt;node name>)
- dotm::checks::nodes::&lt;node name> (key with set expire):
  * JSON containing basic status information:
    {
        "node": "hostname01"
        "status": "UP",
        "last_check": &lt;timestamp>,
        "last_status_change": &lt;timestamp>,
        "status_information": "hostname01 status information"
    }
- dotm::checks::services::&lt;node name> (list of service JSONs with set expire):
  * List containing all associated node checks:
    [
        {
            "node": "hostname01",
            "service": "Service01 name"
            "status": "OK",
            "last_check": &lt;timestamp>,
            "last_status_change": &lt;timestamp>,
            "status_information": "Service01 status information"
        },
        {
            "node": "hostname01",
            "service": "Service02 name"
            "status": "CRITICAL",
            "last_check": &lt;timestamp>,
            "last_status_change": &lt;timestamp>,
            "status_information": "Service02 status information"
        }
    ]
- dotm::checks::config (hash with the following key values):
  * 'last_updated' => &lt;timestamp>
- dotm::config::\* (all preferences, for descriptions check the 'Settings' page)
- dotm::queue (list of queued backend tasks in JSON)
  * {"id": &lt;task key>, "fn": &lt;function name/action>, "args": &lt;function arguments>, "kwargs": &lt;function keywords>}
- dotm::queue::result::&lt;uuid4 name> (status and result of the queued task in JSON)
  * {"status": &lt;pending/processing/ready>, "result": &lt;result in JSON>}
