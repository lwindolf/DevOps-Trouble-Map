#!/usr/bin/python

import re
import json
import redis
import datetime
from bottle import route, run, response

def get_connections(r):
	prefix = 'dotm::connections::'
	tmp = [re.sub('::[0-9]+::', '::', k.replace(prefix, '')) for k in r.keys(prefix+'*')]
	keys = []
	for t in sorted(set(tmp)):
		fields = t.split('::')
		if len(fields) == 2:
			# Filter out local host addresses
			if not (fields[0].startswith('127') or fields[1].startswith('127')):
				keys.append({'source': fields[0], 'destination': fields[1]})
	return keys

@route('/nodes')
def nodes():
	response.set_header('Cache-Control', 'max-age=30,must-revalidate')
	r = redis.Redis()
	return json.dumps({'nodes':r.lrange("dotm::nodes", 0, -1), 'connections': get_connections(r)})

@route('/node/<name>')
def node(name):
	response.set_header('Cache-Control', 'max-age=30,must-revalidate')
	r = redis.Redis()

	prefix = 'dotm::nodes::'+name
	nodeDetails = r.hgetall(prefix)

	prefix = 'dotm::services::'+name+'::'
	serviceDetails = {}
	services = [s.replace(prefix, '') for s in r.keys(prefix+'*')]
	for s in services:
		serviceDetails[s] = r.hgetall(prefix+s)  

	prefix = 'dotm::connections::'+name+'::'
	connectionDetails = {}
	connections = [c.replace(prefix, '') for c in r.keys(prefix+'*')]
	for c in connections:
		tmp = c.split('::')
		if len(tmp) == 2:
			cHash = r.hgetall(prefix+c)
			cHash['localPort'] = tmp[0]
			cHash['remoteHost'] = tmp[1]
			connectionDetails[c] = cHash

	# FIXME: Add node interconnections for this node (but missing in data model currently)

	return json.dumps({'name': name, 'status': nodeDetails, 'services': serviceDetails, 'connections': connectionDetails})

run(host='localhost', port=8080, debug=True)
