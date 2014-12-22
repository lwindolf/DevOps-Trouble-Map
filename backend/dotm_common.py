# -*- coding: utf-8 -*-
# vim: ts=4 sw=4
""" Shared methods """

import argparse
import redis
import re
from dotm_settings import *
from dotm_namespace import DOTMNamespace

# Redis namespace configuration
ns = DOTMNamespace()

def clean_string(s):
    return re.sub('[^\w]', '', s)


def vars_to_json(key, val):
    return json.dumps({key: val})


def get_json_array(key, start=0, end=-1):
    return [json.loads(el) for el in rdb.lrange(key, start, end)]


def get_service_connections():
    """Return a connection graph for all nodes"""
    connections = {}
    tmp = {}
    for key in rdb.keys(ns.connections + '*'):
        # Remove history prefix before we split the key into a value array
        fields = key.lstrip('01234567890:').split('::')
        if not (not fields[3].isdigit() or fields[4].startswith('127')
                or fields[2].startswith('127')):
            connectionDetails = rdb.hgetall(key)

            source = connectionDetails['process']
            remoteServiceDetails = rdb.hgetall(ns.services + "::" + connectionDetails['remote_host'] + "::" + connectionDetails['remote_port'])
            if 'process' in remoteServiceDetails:
                if source != remoteServiceDetails['process']:
                    connKey = source+"::"+remoteServiceDetails['process']
                    if not connKey in tmp:
                        tmp[connKey] = 1
                        connections[connKey] = {
                            'source': source,
                            'destination': remoteServiceDetails['process']
                        }

    return connections

def get_connections():
    """Return a connection graph for all nodes"""
    connections = {}
    for key in rdb.keys(ns.connections + '*'):
        # Remove history prefix before we split the key into a value array
        fields = key.lstrip('01234567890:').split('::')
        if not (not fields[3].isdigit() or fields[4].startswith('127')
                or fields[2].startswith('127')):
            direction = rdb.hget(key, 'direction')
            if direction == "out":
                source = fields[2]
                destination = fields[4]
            else:
                source = fields[4]
                destination = fields[2]

            if not source == destination:
                name = source + '::' + destination
                if not name in connections:
                    connections[name] = {'source': source, 'destination': destination, 'ports': [int(fields[3])]}
                else:
                    connections[name]['ports'].append(int(fields[3]))
    return connections


def get_node_alerts(node):
    try:
        return json.loads(rdb.get(ns.nodes_checks + '::' + node))
    except TypeError:
        print "No node monitoring..."


def get_service_details(node):
    prefix = ns.services + '::' + node + '::'
    service_details = {}
    services = [s.replace(prefix, '') for s in rdb.keys(prefix + '*')]
    for s in services:
        service_details[s] = rdb.hgetall(prefix + s)
	for x in service_details[s]:
		service_details[s][x] = clean_string(service_details[s][x])
    return service_details


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
