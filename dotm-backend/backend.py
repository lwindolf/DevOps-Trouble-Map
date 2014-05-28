#!/usr/bin/python

# To start run from root dir 'PYTHONPATH=dotm-monitor dotm-backend/backend.py'

import json
from bottle import route, run
from dotm_redis import DOTMRedis

@route('/nodes')
def nodes():
	redis = DOTMRedis('mon')
	# FIXME: Add node interconnections to JSON (but missing in Redis currently)
	return json.dumps(redis.lrange("dotm::nodes"))

@route('/node/<name>')
def node(name):
	redis = DOTMRedis('mon')
	services = redis.keys('dotm::services::'+name+'*')
	output = 'name=' + name + '(' + ','.join(services) + ')'
	return output

run(host='localhost', port=8080, debug=True)
