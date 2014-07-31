#!/usr/bin/env python
# vim: ts=4 sw=4
# -*- coding: utf-8 -*-

from bottle import route, run, response, request, debug, static_file

# Backend Web API local imports
# FIXME: import only what is needed instead of *
from settings import *
from dotm_queue import QResponse


# JSON Response helper functions
def json_error(message="Not Found", status_code=404):
    return '{"error": {"message": "' + message + '", "status_code": ' + str(status_code) + '}}'


def resp_json(resp=None):
    response.content_type = 'application/json'
    if not resp:
        response.status = 404
        return json_error()
    return resp


def resp_jsonp(resp=None):
    response.content_type = 'application/javascript'
    callback = request.query.get('callback')
    if resp and callback:
        return '{}({})'.format(callback, resp)
    elif callback:
        return '{}({})'.format(callback, json_error())
    response.content_type = 'application/json'
    response.status = 400
    return json_error("No callback function provided")


def resp_or_404(resp=None, resp_type='application/json', cache_control='max-age=30, must-revalidate'):
    response.set_header('Cache-Control', cache_control)
    accepted_resp = ('application/json', 'application/javascript')
    resp_type_arr = request.headers.get('Accept').split(',')
    if resp_type_arr:
        for resp_type in resp_type_arr:
            if resp_type in accepted_resp:
                break
    if resp_type == 'application/javascript':
        return resp_jsonp(resp)
    return resp_json(resp)


# Redis helper functions
def get_connections():
    prefix = 'dotm::connections::'
    key_arr = []
    for key in rdb.keys(prefix + '*'):
        field_arr = key.split('::')
        if not (field_arr[3].isdigit() or field_arr[4].startswith('127')
                or field_arr[2].startswith('127')):
            key_arr.append({'source': field_arr[2], 'destination': field_arr[4]})
    return key_arr


def get_node_alerts(node):
    try:
        return json.loads(rdb.get(mon_nodes_key_pfx + node))
    except TypeError:
        print "No node monitoring..."


# Backend Queue helper functions
def queue_func(fn, *args, **kwargs):
    rkey = '{}::result::{}'.format(queue_key_pfx, str(uuid4()))
    qresp = QResponse(rdb, rkey, logger=None)
    qresp.queue(fn, args, kwargs)
    qresp.pending()
    return rkey


# Bottle HTTP routing
@route('/geo/nodes')
def get_geo_nodes():
    prefix = 'dotm::resolver::ip_to_node::'
    ips = rdb.keys(prefix + '*')
    nodes = rdb.mget(ips)
    ips = [ip.replace(prefix, '') for ip in ips]
    geo = []
    for i, ip in enumerate(ips):
        try:
            result = gi.record_by_addr(ip)
            serviceAlerts = []
            for s in rdb.lrange(mon_services_key_pfx + nodes[i], 0, -1):
                serviceAlerts.extend(json.loads(s))
            geo.append({
                'data': {
                    'node': nodes[i],
                    'monitoring': {
                        'node': get_node_alerts(nodes[i]),
                        'services': serviceAlerts},
                    'ip': ip},
                'lat': result['latitude'],
                'lng': result['longitude']})
        except:
            pass

    return resp_or_404(json.dumps({'locations': geo}))


@route('/backend/nodes', method='GET')
@route('/nodes', method='GET')
def get_nodes():
    monitoring = {}
    nodes = rdb.lrange("dotm::nodes", 0, -1)
    for node in nodes:
        monitoring[node] = get_node_alerts(node)
    return resp_or_404(json.dumps({'nodes': nodes,
                                   'monitoring': monitoring,
                                   'connections': get_connections()}))

@route('/backend/nodes', method='POST')
@route('/nodes', method='POST')
def add_node():
    # FIXME: validate name
    rdb.lpush(nodes_key_pfx, request.forms.get('name'))


@route('/nodes/<name>', method='GET')
def get_node(name):
    prefix = nodes_key_pfx + '::' + name
    nodeDetails = rdb.hgetall(prefix)
    serviceDetails = get_service_details(name)

    # Fetch all connection details and expand known services
    # with their name and state details
    prefix = connections_key_pfx + '::' + name + '::'
    connectionDetails = {}
    connections = [c.replace(prefix, '') for c in rdb.keys(prefix + '*')]
    for c in connections:
        cHash = rdb.hgetall(prefix + c)
        # If remote host name is not an IP and port is not a high port
        # try to resolve service info
        try:
            if cHash['remote_port'] != 'high' and cHash['remote_host'] not in ('Internet', '127.0.0.1'):
                cHash['remote_service'] = rdb.hgetall('dotm::services::{}::{}'.format(cHash['remote_host'],
                                                                                      cHash['remote_port']))
                cHash['remote_service_id'] = 'dotm::services::{}::{}'.format(cHash['remote_host'],
                                                                             cHash['remote_port'])
        except KeyError:
            print "Bad: key missing, could be a migration issue..."
        connectionDetails[c] = cHash

    serviceAlerts = []
    for s in rdb.lrange(mon_services_key_pfx + name, 0, -1):
        serviceAlerts.extend(json.loads(s))

    return resp_or_404(json.dumps({'name': name,
                                   'status': nodeDetails,
                                   'services': serviceDetails,
                                   'connections': connectionDetails,
                                   'monitoring': {
                                       'node': get_node_alerts(name),
                                       'services': serviceAlerts},
                                   'settings': {
                                       'aging': get_setting('aging')}}))


@route('/backend/settings/<action>/<key>', method='POST')
@route('/settings/<action>/<key>', method='POST')
# NOTE: imho ideologically incorrect API interface. My suggestion would be to
# implement API as /settings/key, when it is needed make use of
# /settings/key&type=hash. As HTML5 at the moment is limited to forms methods
# ["GET"|"POST"] we can add /settings/key&type=hash&action=<action>, but at the
# same time support HTTP methods ["GET"|"POST"|"PUT"|"DELETE"] for actions.
def change_settings(action, key):
    if key in settings:
        if action == 'set' and settings[key]['type'] == 'simple_value':
                rdb.set(config_key_pfx + '::' + key, request.forms.get('value'))
        elif action == 'add' and settings[key]['type'] == 'array':
                rdb.lpush(config_key_pfx + '::' + key, request.forms.get('value'))
        elif action == 'remove' and settings[key]['type'] == 'array':
                rdb.lrem(config_key_pfx + '::' + key, request.forms.get('key'), 1)
        elif action == 'setHash' and settings[key]['type'] == 'hash':
                # setHash might set multiple enumerated keys, e.g. to set all
                # Nagios instance settings, therefore we need to loop here
                i = 1
                while request.forms.get('key' + str(i)):
                    rdb.hset(config_key_pfx + '::' + key,
                             request.forms.get('key' + str(i)),
                             request.forms.get('value' + str(i)))
                    i += 1
        elif action == 'delHash' and settings[key]['type'] == 'hash':
                rdb.hdel(config_key_pfx + '::' + key, request.forms.get('key'))
        else:
            return json_error("This is not a valid command and settings type combination", 400)
        return "OK"
    else:
        return json_error("This is not a valid settings key or settings command", 400)


@route('/backend/settings', method='GET')
@route('/settings', method='GET')
def get_settings():
    for s in settings:
        settings[s]['values'] = get_setting(s)
    return resp_or_404(json.dumps(settings), 'application/javascript', 'no-cache, no-store, must-revalidate')


@route('/mon/nodes')
def get_mon_nodes():
    node_arr = rdb.keys(mon_nodes_key_pfx + '*')
    return resp_or_404(json.dumps([n.split('::')[-1] for n in node_arr])
                       if node_arr else None)


@route('/mon/nodes/<node>')
def get_mon_node(node):
    return resp_or_404(rdb.get(mon_nodes_key_pfx + node))


@route('/mon/services/<node>')
def get_mon_node_services(node):
    return resp_or_404(rdb.lrange(mon_services_key_pfx + node, 0, -1))


@route('/mon/nodes/<node>/<key>')
def get_mon_node_key(node, key):
    result = None
    node_str = rdb.get(mon_nodes_key_pfx + node)
    if node_str:
        node_obj = json.loads(node_str)
        if key in node_obj:
            result = vars_to_json(key, node_obj[key])
    return resp_or_404(result)


# FIXME: Ugly implementation just as POC, callback should be stored in a session.
# Unfortunately bottle-sessions is not included in to Ubuntu repo...
@route('/mon/reload', method='POST')
def mon_reload():
    response.status = 303
    response.set_header('Location', '/queue/result/' + queue_func('reload'))
    return


@route('/queue/result/'
       '<key:re:dotm::queue::result::[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}\Z>',
       method=['GET', 'POST'])
def queue_result(key):
    return resp_or_404(rdb.get(key))


@route('/config', method='GET')
def get_config():
    return resp_or_404(json.dumps(rdb.hgetall(config_key_pfx)))


@route('/config/<variable>', method='GET')
def get_config_variable(variable):
    value = rdb.hget(config_key_pfx, variable)
    if value:
        return resp_or_404(vars_to_json(variable, value))
    return resp_or_404()


@route('/config', method='POST')
def set_config():
    try:
        data_obj = json.loads(request.body.readlines()[0])
        if not isinstance(data_obj, dict):
            raise ValueError
        if not data_obj.viewkeys():
            raise ValueError
    except (ValueError, IndexError):
        response.status = 400
        return json_error("Wrong POST data format", 400)

    for key, val in data_obj.items():
        # TODO: allow only defined variable names with defined value type and
        # maximum length
        rdb.hset(config_key_pfx, key, val)
    return resp_or_404(json.dumps(data_obj))


# Serve static content to eliminate the need of apache in development env.
# For this to work additional routes for /backend/* paths were added because
# they are used in the frontend.
@route('/')
@route('/<filename:path>')
def static(filename="index.htm"):
    return static_file(filename, "../frontend/static/")


if __name__ == '__main__':
    debug(mode=True)
    run(host='localhost', port=8080, reloader=True)
