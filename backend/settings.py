# -*- coding: utf-8 -*-
"""Backend Settings Module"""

import argparse
import re
import redis
import GeoIP
import time
import json
from uuid import uuid4


# Namespace configuration
general_prefix = 'dotm'
nodes_key_pfx = general_prefix + '::nodes'
connections_key_pfx = general_prefix + '::connections'
queue_key_pfx = general_prefix + '::queue'
config_key_pfx = general_prefix + '::config'
services_key_pfx = general_prefix + '::services'
mon_nodes_key_pfx = general_prefix + '::checks::nodes::'
mon_services_key_pfx = general_prefix + '::checks::services::'
mon_config_key = general_prefix + '::checks::config'
mon_config_key_pfx = general_prefix + '::checks::config::'


# Default Settings
settings = {
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
    'aging':                   {'description': 'Number of seconds after which a services/connections are'
                                ' considered unused. Default is "300"s.',
                                'title': 'Service Aging',
                                'type': 'hash',
                                'default': {
                                    'Services': 5 * 60,
                                    'Connections': 5 * 60},
                                'fields': ['Parameter', 'Value'],
                                'position': 4},
    'expire':                  {'description': 'Number of days after which old data should be forgotten.'
                                ' Default is "0" (never).',
                                'title': 'Data Retention',
                                'type': 'hash',
                                'default': {
                                    'Services': 0,
                                    'Connections': 0,
                                    'Nagios Alerts': 0},
                                'fields': ['Parameter', 'Value'],
                                'position': 5},
    'hiding':                  {'description': 'Number of days after which old service/connection data should not'
                                ' be displayed in node graph anymore. Default is "7" days.',
                                'title': 'Hiding Old Objects',
                                'type': 'hash',
                                'default': {
                                    'Services': 7,
                                    'Connections': 7},
                                'fields': ['Parameter', 'Value'],
                                'position': 6},
    'service_mapping':         {'description': 'Rules that map Nagios service check names to process names as seen'
                                ' by DOTM. Those rules can be regular expressions. Note that both the service check'
                                ' name as well as the process name can be a regular expression. To enforce exact'
                                ' matching use "^" and "$"! Matching is performed case-insensitive.',
                                'title': 'Mapping Service Checks to Processes',
                                'type': 'hash',
                                'default': {
                                    '^HTTP': '^nginx.*|^apache.*|^lighttpd.*',
                                    '^Redis': '^redis-server.*',
                                    '^MySQL.*': '^mysql.*',
                                    '^Postgres.*': '^postmaster.*'},
                                'add': True,
                                'fields': ['Service Check Regex', 'Process Regex'],
                                'position': 7},
    'service_port_whitelist':  {'description': 'Comma separated list of port numbers that are to be ignored.'
                                ' This is to avoid presenting basic Unix services (Postfix, any shared filesystem'
                                ' or monitoring agents) as high-level services of interest. Add ports of services'
                                ' you do not care about. Currently only TCP ports are handled.',
                                'title': 'Aggregator: Service Port Whitelist',
                                'type': 'single_value',
                                'default': '53,22,5666,4949,4848,25,631',
                                'position': 8}
}


# Return value(s) or defaults(s) of a settings key
#
# s     key name
def get_setting(s, values=None):
    """Get setting from Redis or default settings from settings dict"""
    if settings[s]['type'] == 'single_value':
        values = rdb.get(config_key_pfx + '::' + s)
    elif settings[s]['type'] == 'array':
        values = rdb.lrange(config_key_pfx + '::' + s, 0, -1)
    elif settings[s]['type'] == 'hash':
        values = rdb.hgetall(config_key_pfx + '::' + s)
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


def get_service_details(node):
    prefix = services_key_pfx + '::' + node + '::'
    service_details = {}
    services = [s.replace(prefix, '') for s in rdb.keys(prefix + '*')]
    for s in services:
        service_details[s] = rdb.hgetall(prefix + s)
    return service_details


def vars_to_json(key, val):
    return json.dumps({key: val})


# Command-line argument parsing
cl_parser = argparse.ArgumentParser(description='DOTM Backend')
cl_parser.add_argument('-r', '--redis-server', help='Redis Server', type=str, default='localhost')
cl_parser.add_argument("-P", '--redis-port', help='Redis Port', type=int, default=6379)
cl_parser.add_argument("-d", '--redis-db', help='Redis Database', type=int, default=0)
cl_parser.add_argument("-p", '--redis-password', help='Redis Password', type=str, default=None)
cl_parser.add_argument("-D", '--debug', help='DEBUG Mode On', action="store_true")
cl_parser.add_argument("-l", '--log', help='Log file', type=str, default=None)
cl_args = cl_parser.parse_args()


try:
    # Redis connection initialization
    rdb = redis.Redis(host=cl_args.redis_server,
                      port=cl_args.redis_port,
                      db=cl_args.redis_db,
                      password=cl_args.redis_password)

    # GeoIP Database setup
    gi = GeoIP.open("/usr/share/GeoIP/GeoIPCity.dat", 0)

except Exception as e:
    print e