from bottle import route, run, response
import redis
import configparser
import json
import time

from dotm_mon import DOTMMonitor

config = configparser.ConfigParser()
config.read('.mr.developer.cfg')

mon_url = config['monitoring']['url']
mon_user = config['monitoring']['user']
mon_paswd = config['monitoring']['paswd']
mon_hosts_key = config['monitoring']['hosts_key'] # dotm::mon::hosts
mon_services_key = config['monitoring']['services_key'] # dotm::mon::services
mon_config_key = config['monitoring']['config_key'] # dotm::mon::config
mon_config_key_prefix = config['monitoring']['config_key_prefix'] # dotm::mon::config::

redis_host = config['redis']['host']
redis_port = config['redis']['port']

rdb = redis.Redis(redis_host, redis_port)

def resp_or_404(resp=None):
	response.content_type = 'application/json'
	if not resp:
		response.status = 404
		resp = '{"error": {"message": "Not Found", "status_code": 404}}'
	return resp

def vars_to_json(key, val):
	return '{{"{}": {}}}'.format(key, val)

@route('/mon/hosts/<host>')
def get_host(host):
	result = None
	host_b = rdb.hget(mon_hosts_key, host)
	if host_b:
		result = vars_to_json(host, host_b.decode('utf-8'))
	return resp_or_404(result)

@route('/mon/services/<host>')
def get_host_services(host):
	result = None
	services_b = rdb.hget(mon_services_key, host)
	if services_b:
		result = vars_to_json(host, services_b.decode('utf-8'))
	return resp_or_404(result)

@route('/mon/hosts/<host>/<key>')
def get_host_key(host, key):
	result = None
	host_b = rdb.hget(mon_hosts_key, host)
	if host_b:
		host_obj = json.loads(host_b.decode('utf-8'))
		if key in host_obj:
			result = vars_to_json(key, '"{}"'.format(host_obj[key]))
	return resp_or_404(result)

@route('/mon/reload', method='POST')
def reload():
	result = None
	time_now = int(time.time())
	update_time_key = 'last_updated'
	update_interval = 60
	update_lock_key = mon_config_key_prefix + 'update_running'
	update_lock_expire = 300
	update_time_b = rdb.hget(mon_config_key, update_time_key)
	if update_time_b and not rdb.get(update_lock_key):
		update_time = int(update_time_b)
		if time_now - update_time >= update_interval:
			rdb.setex(update_lock_key, update_lock_expire, 1)
			mon = DOTMMonitor(mon_url, mon_user, mon_paswd)
			for key,value in mon.get_hosts().items():
				rdb.hset(mon_hosts_key, key, json.dumps(value))
			for key,value in mon.get_services().items():
				rdb.hset(mon_services_key, key, json.dumps(value))
			time_now = int(time.time())
			rdb.hset(mon_config_key, update_time_key, time_now)
			update_time = time_now
			rdb.delete(update_lock_key)
		result = vars_to_json(update_time_key, update_time)
	elif update_time_b:
		update_time = int(update_time_b)
		result = vars_to_json(update_time_key, update_time)
	else:
		rdb.hset(mon_config_key, update_time_key, 0)
	return resp_or_404(result)

if __name__ == '__main__':
	run(host='localhost', port=8081, reloader=True, debug=True)

