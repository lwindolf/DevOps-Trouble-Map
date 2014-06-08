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
mon_expire = config['monitoring']['expire']  # 86400sec = 1day
mon_nodes_key_pfx = config['monitoring']['nodes_key_prefix']  # dotm::checks::nodes::
mon_services_key_pfx = config['monitoring']['services_key_prefix']  # dotm::checks::services::
mon_config_key = config['monitoring']['config_key']  # dotm::checks::config
mon_config_key_pfx = config['monitoring']['config_key_prefix']  # dotm::checks::config::

redis_host = config['redis']['host']
redis_port = config['redis']['port']

rdb = redis.Redis(redis_host, redis_port)


def resp_or_404(resp=None):
    response.content_type = 'application/json'
    response.set_header('Cache-Control', 'private, max-age=0, no-cache')
    if not resp:
        response.status = 404
        resp = '{"error": {"message": "Not Found", "status_code": 404}}'
    return resp


def vars_to_json(key, val):
    return json.dumps({key: val})


@route('/mon/nodes')
def get_nodes():
    nodes_b = rdb.keys(mon_nodes_key_pfx + '*')
    result = json.dumps([n.decode('utf-8').split('::')[-1]
                        for n in nodes_b]) if nodes_b else None
    return resp_or_404(result)


@route('/mon/nodes/<node>')
def get_node(node):
    node_b = rdb.get(mon_nodes_key_pfx + node)
    result = node_b.decode('utf-8') if node_b else None
    return resp_or_404(result)


@route('/mon/services/<node>')
def get_node_services(node):
    services_b = rdb.get(mon_services_key_pfx + node)
    result = services_b.decode('utf-8') if services_b else None
    return resp_or_404(result)


@route('/mon/nodes/<node>/<key>')
def get_node_key(node, key):
    result = None
    node_b = rdb.get(mon_nodes_key_pfx + node)
    if node_b:
        node_obj = json.loads(node_b.decode('utf-8'))
        if key in node_obj:
            result = vars_to_json(key, node_obj[key])
    return resp_or_404(result)


@route('/mon/reload', method='POST')
def reload():
    result = None
    time_now = int(time.time())
    update_time_key = 'last_updated'
    update_interval = 60
    update_lock_key = mon_config_key_pfx + 'update_running'
    update_lock_expire = 300
    update_time_b = rdb.hget(mon_config_key, update_time_key)
    if update_time_b and not rdb.get(update_lock_key):
        update_time = int(update_time_b)
        if time_now - update_time >= update_interval:
            rdb.setex(update_lock_key, update_lock_expire, 1)
            mon = DOTMMonitor(mon_url, mon_user, mon_paswd)
            for key, val in mon.get_nodes().items():
                rdb.setex(mon_nodes_key_pfx + key, json.dumps(val), mon_expire)
            for key, val in mon.get_services().items():
                rdb.setex(mon_services_key_pfx + key, json.dumps(val), mon_expire)
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
