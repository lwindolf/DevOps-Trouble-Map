#!/usr/bin/python

import json
import redis
from bottle import route, run

@route('/nodes')
def nodes():
	r = redis.Redis()
	# FIXME: Add node interconnections to JSON (but missing in Redis currently)
	return json.dumps(r.lrange("dotm::nodes", 0, -1))

@route('/node/<name>')
def node(name):
	r = redis.Redis()
	services = r.keys('dotm::services::'+name+'*')
	output = 'name=' + name + '(' + ','.join(services) + ')'
	return output

run(host='localhost', port=8080, debug=True)
