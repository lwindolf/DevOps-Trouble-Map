# -*- coding: utf-8 -*-
# vim: ts=4 sw=4
"""Backend Settings Module"""

import re
import GeoIP
import time
import json
from uuid import uuid4
from dotm_common import *
from dotm_namespace import DOTMNamespace

# Redis namespace configuration
ns = DOTMNamespace()

history_key_set = (ns.nodes, ns.connections, ns.services, ns.checks, ns.config, ns.resolver)


# Default DOTM Settings
settings = {
    'fetch_method':            {'description': 'Fetch method: How to fetch node infos. Possible values are:'
                                ' "agent" (when you have installed dotm_agent) and "ssh" (when you want to'
                                ' rely on root equivalency between the DOTM server and all monitored nodes).',
                                'title': 'Fetch Method',
                                'type': 'single_value',
                                'default': 'ssh',
                                'position': 0},
    'other_internal_networks': {'description': 'Networks that DOTM should consider internal. Note that private'
                                ' networks (127.0.0.0/8 10.0.0.0/8 172.16.0.0/12 192.168.0.0/16) are always'
                                ' considered internal. Separate different networks in CIDR syntax by spaces.',
                                'title': 'Internal Networks',
                                'type': 'array',
                                'add': True,
                                'fields': ['Network'],
                                'position': 1},
    'user_node_aliases':       {'description': 'Node aliases to map node names of your monitoring to a node in DOTM',
                                'title': 'Additional Node Aliases',
                                'type': 'hash',
                                'add': True,
                                'fields': ['Alias', 'Node Name'],
                                'position': 2},
    'nagios_instance':         {'description': 'Nagios/Icinga instance configuration. Currently only one instance'
                                ' is supported. The "url" field should point to your cgi-bin/ location'
                                ' (e.g. "http://my.domain.com/cgi-bin/icinga"). The "expire" field should'
                                ' contain the number of seconds after which to discard old check results.'
                                ' "Use Aliases" specifies wether the nagios host name or alias should be used.'
                                ' "Refresh" specifies the update interval in seconds.',
                                'title': 'Nagios Instance',
                                'type': 'hash',
                                'default': {
                                    'url': 'http://localhost/nagios/cgi-bin/',
                                    'user': 'dotm',
                                    'password': 'changeme',
                                    'expire': 86400,
                                    'use_aliases': 0,
                                    'refresh': 60},
                                'fields': ['Parameter', 'Value'],
                                'position': 3},
    'history':                 {'description': 'How often and if at all to store history snapshots.'
                                ' Default is one snapshot every hour and expiration after 1 week.'
                                ' All values are in seconds.',
                                'title': 'History Snapshots',
                                'type': 'hash',
                                'default': {
                                    'enabled': 1,
                                    'interval': 60*60,
                                    'expire': 7*24*60*60
                                },
                                'fields': ['Parameter', 'Value'],
                                'position': 4},
    'aging':                   {'description': 'Number of seconds after which a services/connections are'
                                ' considered unused. Default is "300"s.',
                                'title': 'Service Aging',
                                'type': 'hash',
                                'default': {
                                    'Services': 5 * 60,
                                    'Connections': 5 * 60},
                                'fields': ['Parameter', 'Value'],
                                'position': 5},
    'expire':                  {'description': 'Number of days after which old data should be forgotten.'
                                ' Default is "0" (never).',
                                'title': 'Data Retention',
                                'type': 'hash',
                                'default': {
                                    'Services': 0,
                                    'Connections': 0,
                                    'Nagios Alerts': 0,
                                },
                                'fields': ['Parameter', 'Value'],
                                'position': 6},
    'hiding':                  {'description': 'Number of days after which old service/connection data should not'
                                ' be displayed in node graph anymore. Default is "7" days.',
                                'title': 'Hiding Old Objects',
                                'type': 'hash',
                                'default': {
                                    'Services': 7,
                                    'Connections': 7},
                                'fields': ['Parameter', 'Value'],
                                'position': 7},
    'service_mapping':         {'description': 'Rules that map Nagios service check names to process names as seen'
                                ' by DOTM. Those rules can be regular expressions. Note that both the service check'
                                ' name as well as the process name can be a regular expression. To enforce exact'
                                ' matching use "^" and "$"! Matching is performed case-insensitive.',
                                'title': 'Mapping Service Checks to Processes',
                                'type': 'hash',
                                'default': {
                                    '^HTTP'			: '^nginx.*|^apache.*|^lighttpd.*',
                                    '^Redis'		: '^redis-server.*',
                                    '^CouchDB'		: '^couch.*',
                                    '^MySQL.*'		: '^mysql.*',
                                    '^Postgres.*'	: '^postmaster.*',
                                    '^PgBouncer.*'	: '^pgbouncer.*',
                                    '^memcached'	: '^memcached.*',
                                    '^node\.?js'	: '^nodejs.*',
                                    '.*DNS.*'		: '^named.*'},
                                'add': True,
                                'fields': ['Service Check Regex', 'Process Regex'],
                                'position': 8},
    'service_port_whitelist':  {'description': 'Comma separated list of port numbers that are to be ignored.'
                                ' This is to avoid presenting basic Unix services (Postfix, any shared filesystem'
                                ' or monitoring agents) as high-level services of interest. Add ports of services'
                                ' you do not care about. Currently only TCP ports are handled.',
                                'title': 'Aggregator: Service Port Whitelist',
                                'type': 'single_value',
                                'default': '53,953,22,5666,4949,4848,25,631,24007,24009,111,2049',
                                'position': 9},
    'service_name_whitelist':  {'description': 'Comma separated list of service names that are to be ignored.'
                                ' This is to avoid presenting basic Unix services (Postfix, any shared filesystem'
                                ' or monitoring agents) as high-level services of interest. Add ports of services'
                                ' you do not care about. Currently only TCP ports are handled.',
                                'title': 'Aggregator: Service Name Whitelist',
                                'type': 'single_value',
                                'default': 'rpc.statd,rpcstatd,rpc.mountd',
                                'position': 10}
}


def get_setting(s, values=None):
    """Get setting from Redis or default settings from settings dict"""
    if settings[s]['type'] == 'single_value':
        values = rdb.get(ns.config + '::' + s)
    elif settings[s]['type'] == 'array':
        values = rdb.lrange(ns.config + '::' + s, 0, -1)
    elif settings[s]['type'] == 'hash':
        values = rdb.hgetall(ns.config + '::' + s)
        # We always get a hash back from hgetall() but it might be incomplete
        # or empty. So we fill in the defaults where needed.
        if 'default' in settings[s]:
            for key in settings[s]['default']:
                if key not in values:
                    values[key] = settings[s]['default'][key]

    # Apply default if one is defined and key was not yet set
    if not values and 'default' in settings[s]:
        values = settings[s]['default']

    return values
