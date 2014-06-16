#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ConfigParser
import json
import redis
import time
from bottle import route, run, response, request, debug

from dotm_monitor import DOTMMonitor

# Configuration
config = ConfigParser.ConfigParser()
config.read('.mr.developer.cfg')

mon_url = config.get('monitoring', 'url')
mon_user = config.get('monitoring', 'user')
mon_paswd = config.get('monitoring', 'paswd')
mon_expire = config.getint('monitoring', 'expire')  # 86400sec = 1day
mon_nodes_key_pfx = config.get('monitoring', 'nodes_key_prefix')  # dotm::checks::nodes::
mon_services_key_pfx = config.get('monitoring', 'services_key_prefix')  # dotm::checks::services::
mon_config_key = config.get('monitoring', 'config_key')  # dotm::checks::config
mon_config_key_pfx = config.get('monitoring', 'config_key_prefix')  # dotm::checks::config::

redis_host = config.get('redis', 'host')
redis_port = config.getint('redis', 'port')

rdb = redis.Redis(redis_host, redis_port)


def resp_json(resp=None):
    response.content_type = 'application/json'
    if not resp:
        response.status = 404
        return '{"error": {"message": "Not Found", "status_code": 404}}'
    return resp


def resp_jsonp(resp=None, resp_type='apptilacion/javascript'):
    callback = request.query.get('callback')
    if resp and callback:
        return '{}({})'.format(callback, resp)
    elif callback:
        return '{}({})'.format(callback, '{"error": {"message": "Not Found", "status_code": 404}}')
    response.content_type = 'application/json'
    response.status = 400
    return '{"error": {"message": "No callback funcrion provided", "status_code": 400}}'


def resp_or_404(resp=None, resp_type='apptilacion/json'):
    response.set_header('Cache-Control', 'max-age=30, must-revalidate')
    accepted_resp = ('apptilacion/json', 'application/javascript')
    resp_type_arr = request.headers.get('Accept').split(',')
    if resp_type_arr:
        for resp_type in resp_type_arr:
            if resp_type in accepted_resp:
                break
    if resp_type == 'application/javascript':
        return resp_jsonp(resp)
    return resp_json(resp)


def vars_to_json(key, val):
    return json.dumps({key: val})


def get_connections():
    prefix = 'dotm::connections::'
    key_arr = []
    for key in rdb.keys(prefix + '*'):
        field_arr = key.split('::')
        if not (field_arr[3].isdigit() or field_arr[4].startswith('127')
                or field_arr[2].startswith('127')):
            key_arr.append({'source': field_arr[2], 'destination': field_arr[4]})
    return key_arr


@route('/nodes')
def get_nodes():
    return resp_or_404(json.dumps({'nodes': rdb.lrange("dotm::nodes", 0, -1),
                                   'connections': get_connections()}))


@route('/nodes/<name>')
def get_node(name):
    prefix = 'dotm::nodes::' + name
    nodeDetails = rdb.hgetall(prefix)
    prefix = 'dotm::services::' + name + '::'
    serviceDetails = {}
    services = [s.replace(prefix, '') for s in rdb.keys(prefix + '*')]
    for s in services:
        serviceDetails[s] = rdb.hgetall(prefix + s)

    prefix = 'dotm::connections::' + name + '::'
    connectionDetails = {}
    connections = [c.replace(prefix, '') for c in rdb.keys(prefix + '*')]
    for c in connections:
        tmp = c.split('::')
        if len(tmp) == 2:
            cHash = rdb.hgetall(prefix + c)
            cHash['localPort'] = tmp[0]
            cHash['remoteHost'] = tmp[1]
            connectionDetails[c] = cHash

    return resp_or_404(json.dumps({'name': name,
                                   'status': nodeDetails,
                                   'services': serviceDetails,
                                   'connections': connectionDetails,
                                   'monitoring':rdb.get(mon_nodes_key_pfx + name)}))


@route('/mon/nodes')
def get_mon_nodes():
    node_arr = rdb.keys(mon_nodes_key_pfx + '*')
    return resp_or_404(json.dumps([n.split('::')[-1]for n in node_arr])
                       if node_arr else None)


@route('/mon/nodes/<node>')
def get_mon_node(node):
    return resp_or_404(rdb.get(mon_nodes_key_pfx + node))


@route('/mon/services/<node>')
def get_mon_node_services(node):
    return resp_or_404(rdb.lrange(mon_services_key_pfx + node, 0, -1))


@route('/mon/nodes/<node>/<key>')
def get_mon_node_key(node, key):
    result = None
    node_str = rdb.get(mon_nodes_key_pfx + node)
    if node_str:
        node_obj = json.loads(node_str)
        if key in node_obj:
            result = vars_to_json(key, node_obj[key])
    return resp_or_404(result)


@route('/mon/reload', method='POST')
def mon_reload():
    time_now = int(time.time())
    update_time_key = 'last_updated'
    update_interval = 60
    update_lock_key = mon_config_key_pfx + 'update_running'
    update_lock_expire = 300
    update_time_str = rdb.hget(mon_config_key, update_time_key)
    if update_time_str and not rdb.get(update_lock_key):
        update_time = int(update_time_str)
        if time_now - update_time >= update_interval:
            rdb.setex(update_lock_key, update_lock_expire, 1)
            mon = DOTMMonitor(mon_url, mon_user, mon_paswd)
            for key, val in mon.get_nodes().items():
                rdb.setex(mon_nodes_key_pfx + key, json.dumps(val), mon_expire)
            for key, val in mon.get_services().items():
                with rdb.pipeline() as pipe:
                    pipe.lpush(mon_services_key_pfx + key, json.dumps(val))
                    pipe.expire(mon_services_key_pfx + key, mon_expire)
                    pipe.execute()
            time_now = int(time.time())
            rdb.hset(mon_config_key, update_time_key, time_now)
            update_time = time_now
            rdb.delete(update_lock_key)
        return resp_or_404(vars_to_json(update_time_key, update_time))
    elif update_time_str:
        update_time = int(update_time_str)
        return resp_or_404(vars_to_json(update_time_key, update_time))
    else:
        rdb.hset(mon_config_key, update_time_key, 0)
    return resp_or_404(None)

if __name__ == '__main__':
    debug(mode=True)
    run(host='localhost', port=8080, reloader=True)
