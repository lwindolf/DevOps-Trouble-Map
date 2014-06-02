#!/usr/bin/python

import json
import redis
import datetime
from bottle import route, run

@route('/nodes')
def nodes():
	r = redis.Redis()
	# FIXME: Add node interconnections to JSON (but missing in data model currently)
	return json.dumps(r.lrange("dotm::nodes", 0, -1))

@route('/node/<name>')
def node(name):
	r = redis.Redis()
	prefix = 'dotm::services::'+name+'::'
	serviceDetails = {}
	services = [s.replace(prefix, '') for s in r.keys(prefix+'*')]
	for s in services:
		serviceDetails[s] = r.hgetall(prefix+s)  
	# FIXME: Add connections for this node
	# FIXME: Add node interconnections for this node (but missing in data model currently)
	return json.dumps({'name': name, 'services': serviceDetails})

run(host='localhost', port=8080, debug=True)
