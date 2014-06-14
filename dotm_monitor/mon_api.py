from bottle import route, run, response, request
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

rdb = redis.Redis(redis_host, redis_port, decode_responses=True)


def resp_json(resp=None):
    response.content_type = 'application/json'
    if not resp:
        response.status = 404
        return '{"error": {"message": "Not Found", "status_code": 404}}'
    return resp


def resp_jsonp(resp=None):
    callback = request.query.get('callback')
    if resp and callback:
        response.content_type = 'application/javascript'
        return '{}({})'.format(callback, resp)
    elif resp:
        response.status = 400
        return '{"error": {"message": "No callback funcrion provided", "status_code": 400}}'
    return '{"error": {"message": "Not Found", "status_code": 404}}'


def resp_or_404(resp=None, resp_type='apptilacion/json'):
    response.set_header('Cache-Control', 'private, max-age=0, no-cache')
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


@route('/mon/nodes')
def get_nodes():
    node_arr = rdb.keys(mon_nodes_key_pfx + '*')
    return resp_or_404(json.dumps([n.split('::')[-1]for n in node_arr])
                       if node_arr else None)


@route('/mon/nodes/<node>')
def get_node(node):
    return resp_or_404(rdb.get(mon_nodes_key_pfx + node))


@route('/mon/services/<node>')
def get_node_services(node):
    return resp_or_404(rdb.get(mon_services_key_pfx + node))


@route('/mon/nodes/<node>/<key>')
def get_node_key(node, key):
    result = None
    node_str = rdb.get(mon_nodes_key_pfx + node)
    if node_str:
        node_obj = json.loads(node_str)
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
                # TODO: move services to lists, will be needed for pagination
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
