from bottle import route, run, response
from dotm_redis import DOTMRedis
import configparser
import json

config = configparser.ConfigParser()
config.read('.mr.developer.cfg')

mon_hosts_key = config['monitoring']['hosts_key'] # dotm::mon::hosts
mon_services_key = config['monitoring']['services_key'] # dotm::mon::services

rdb = DOTMRedis()

def resp_or_404(resp):
	response.content_type = 'application/json'
	if not resp:
		response.status = 404
	return resp

@route('/mon/get/<host>')
def get_host(host):
	result = None
	rdb.name = mon_hosts_key
	if host in rdb and rdb[host]:
		result = json.dumps(rdb[host].decode('utf-8')).strip('"')
	return resp_or_404(result)

@route('/mon/get/<host>/service_status')
def get_host_services(host):
	result = None
	rdb.name = mon_services_key
	if host in rdb and rdb[host]:
		result = json.dumps(rdb[host].decode('utf-8')).strip('"')
	return resp_or_404(result)

@route('/mon/get/<host>/<key>')
def get_host_key(host, key):
	result = None
	rdb.name = mon_hosts_key
	if host in rdb and rdb[host]:
		host_obj = json.loads(rdb[host].decode('utf-8').replace('\'', '"'))
		if key in host_obj:
			result = host_obj[key]
	return resp_or_404(result)

if __name__ == "__main__":
	run(host='localhost', port=8081, reloader=True, debug=True)
