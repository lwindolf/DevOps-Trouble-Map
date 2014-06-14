#!/usr/bin/env python3

import json
import redis
from bottle import route, run, response

rdb = redis.Redis(decode_responses=True)


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
def nodes():
    response.set_header('Cache-Control', 'max-age=30,must-revalidate')
    response.content_type = 'application/json'
    return json.dumps({'nodes': rdb.lrange("dotm::nodes", 0, -1),
                       'connections': get_connections()})


@route('/node/<name>')
def node(name):
    response.set_header('Cache-Control', 'max-age=30,must-revalidate')
    response.content_type = 'application/json'
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

    return json.dumps({'name': name, 'status': nodeDetails, 'services': serviceDetails,
                       'connections': connectionDetails})

if __name__ == '__main__':
    run(host='localhost', port=8080, reloader=True, debug=True)
