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

- Simple remote agent (C or Perl...)
- Redis as backend store
- Python bobo with Jinja templating
- JSON backend data access
- any jQuery library for rendering
