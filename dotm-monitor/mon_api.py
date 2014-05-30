from bottle import route, run, response
from dotm_redis import DOTMRedis
import configparser
import json

config = configparser.ConfigParser()
config.read('.mr.developer.cfg')

mon_hosts_key = config['monitoring']['hosts_key'] # dotm::mon::hosts
mon_services_key = config['monitoring']['services_key'] # dotm::mon::services

rdb_hosts = DOTMRedis(mon_hosts_key)
rdb_services = DOTMRedis(mon_services_key)

@route('/mon/get/<host>')
def get_host(host):
	result = None
	response.content_type = 'application/json'
	host_b = rdb_hosts.get(host)
	if host_b:
		result = json.dumps(host_b.decode('utf-8')).strip('"')
	if not result:
		response.status = 404
	return result

@route('/mon/get/<host>/service_status')
def get_host_services(host):
	result = None
	response.content_type = 'application/json'
	service_b = rdb_services.get(host)
	if service_b:
		result = json.dumps(service_b.decode('utf-8')).strip('"')
	if not result:
		response.status = 404
	return result

@route('/mon/get/<host>/<key>')
def get_host_key(host, key):
	result = None
	response.content_type = 'application/json'
	host_b = rdb_hosts.get(host)
	if host_b:
		host_obj = json.loads(host_b.decode('utf-8').replace('\'', '"'))
		if key in host_obj:
			result = host_obj[key]
	if not result:
		response.status = 404
	return result

if __name__ == "__main__":
	run(host='localhost', port=8081, reloader=True, debug=True)
