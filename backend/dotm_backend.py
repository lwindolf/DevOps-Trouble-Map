#!/usr/bin/env python
# vim: ts=4 sw=4
# -*- coding: utf-8 -*-

import json
import redis
import time
import re
from bottle import route, run, response, request, debug

from dotm_monitor import DOTMMonitor

# Namespace configuration
general_prefix = 'dotm'
config_key_pfx = general_prefix + '::config'
mon_nodes_key_pfx = general_prefix + '::checks::nodes::'
mon_services_key_pfx = general_prefix + '::checks::services::'
mon_config_key = general_prefix + '::checks::config'
mon_config_key_pfx = general_prefix + '::checks::config::'

settings = {
    'other_internal_networks': {'description': 'Networks that DOTM should consider internal. Note that private'
                                ' networks (127.0.0.0/8 10.0.0.0/8 172.16.0.0/12 192.168.0.0/16) are always'
                                ' considered internal. Separate different networks in CIDR syntax by spaces.',
                                'title': 'Internal Networks',
                                'type': 'array',
                                'add': True,
                                'fields': ['Network'],
                                'position': 1},
    'user_node_aliases':       {'description': 'Node aliases to map node names of your monitoring to a node in DOTM',
                                'title': 'Additional Node Aliases',
                                'type': 'hash',
                                'add': True,
                                'fields': ['Alias', 'Node Name'],
                                'position': 2},
    'nagios_instance':         {'description': 'Nagios/Icinga instance configuration. Currently only one instance'
                                ' is supported. The "url" field should point to your cgi-bin/ location'
                                ' (e.g. "http://my.domain.com/icinga/cgi-bin/"). The "expire" field should'
                                ' contain the number of seconds after which to discard old check results.'
                                ' "Use Aliases" specifies wether the nagios host name or alias should be used.'
                                ' "Refresh" specifices the update interval in seconds.',
                                'title': 'Nagios Instance',
                                'type': 'hash',
                                'default': {
                                    'url': 'http://localhost/nagios/cgi-bin/',
                                    'user': 'dotm',
                                    'password': 'changeme',
                                    'expire': 86400,
                                    'use_aliases': 0,
                                    'refresh': 60},
                                'fields': ['Parameter', 'Value'],
                                'position': 3},
    'aging':                   {'description': 'Number of seconds after which a services/connections are'
                                ' considered unused. Default is "300"s.',
                                'title': 'Service Aging',
                                'type': 'hash',
                                'default': {
                                    'Services': 5 * 60,
                                    'Connections': 5 * 60},
                                'fields': ['Parameter', 'Value'],
                                'position': 4},
    'expire':                  {'description': 'Number of days after which old data should be forgotten.'
                                ' Default is "0" (never).',
                                'title': 'Data Retention',
                                'type': 'hash',
                                'default': {
                                    'Services': 0,
                                    'Connections': 0,
                                    'Nagios Alerts': 0},
                                'fields': ['Parameter', 'Value'],
                                'position': 5},
    'hiding':                  {'description': 'Number of days after which old service/connection data should not'
                                ' be displayed in node graph anymore. Default is "7" days.',
                                'title': 'Hiding Old Objects',
                                'type': 'hash',
                                'default': {
                                    'Services': 7,
                                    'Connections': 7},
                                'fields': ['Parameter', 'Value'],
                                'position': 6},
    'service_mapping':         {'description': 'Rules that map Nagios service check names to process names as seen'
                                ' by DOTM. Those rules can be regular expressions. Note that both the service check'
                                ' name as well as the process name can be a regular expression. To enforce exact'
                                ' matching use "^" and "$"! Matching is performed case-insensitive.',
                                'title': 'Mapping Service Checks to Processes',
                                'type': 'hash',
                                'default': {
                                    '^HTTP': '^nginx.*|^apache.*|^lighttpd.*',
                                    '^Redis': '^redis-server.*',
                                    '^MySQL.*': '^mysql.*',
                                    '^Postgres.*': '^postmaster.*'},
                                'add': True,
                                'fields': ['Service Check Regex', 'Process Regex'],
                                'position': 7},
    'service_port_whitelist':  {'description': 'Comma separated list of port numbers that are to be ignored.'
                                ' This is to avoid presenting basic Unix services (Postfix, any shared filesystem'
                                ' or monitoring agents) as high-level services of interest. Add ports of services'
                                ' you do not care about. Currently only TCP ports are handled.',
                                'title': 'Aggregator: Service Port Whitelist',
                                'type': 'single_value',
                                'default': '53,22,5666,4949,4848,25,631',
                                'position': 8}
}

rdb = redis.Redis()  # FIXME: provide command line switches and feed them from init script


def json_error(message="Not Found", status_code=404):
    return '{"error": {"message": "' + message + '", "status_code": ' + str(status_code) + '}}'


def resp_json(resp=None):
    response.content_type = 'application/json'
    if not resp:
        response.status = 404
        return json_error()
    return resp


def resp_jsonp(resp=None):
    response.content_type = 'apptilacion/javascript'
    callback = request.query.get('callback')
    if resp and callback:
        return '{}({})'.format(callback, resp)
    elif callback:
        return '{}({})'.format(callback, json_error())
    response.content_type = 'application/json'
    response.status = 400
    return json_error("No callback function provided")


def resp_or_404(resp=None, resp_type='apptilacion/json', cache_control='max-age=30, must-revalidate'):
    response.set_header('Cache-Control', cache_control)
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


def get_connections():
    prefix = 'dotm::connections::'
    key_arr = []
    for key in rdb.keys(prefix + '*'):
        field_arr = key.split('::')
        if not (field_arr[3].isdigit() or field_arr[4].startswith('127')
                or field_arr[2].startswith('127')):
            key_arr.append({'source': field_arr[2], 'destination': field_arr[4]})
    return key_arr


# Return value(s) or defaults(s) of a settings key
#
# s     key name
def get_setting(s):
    if settings[s]['type'] == 'single_value':
        values = rdb.get(config_key_pfx + '::' + s)
    elif settings[s]['type'] == 'array':
        values = rdb.lrange(config_key_pfx + '::' + s, 0, -1)
    elif settings[s]['type'] == 'hash':
        values = rdb.hgetall(config_key_pfx + '::' + s)
        # We always get a hash back from hgetall() but it might be incomplete
        # or empty. So we fill in the defaults where needed.
        if 'default' in settings[s]:
            for key in settings[s]['default']:
                if key not in values:
                    values[key] = settings[s]['default'][key]

    # Apply default if one is defined and key was not yet set
    if 'default' in settings[s] and not values:
        values = settings[s]['default']

    return values


@route('/nodes')
def get_nodes():
    return resp_or_404(json.dumps({'nodes': rdb.lrange("dotm::nodes", 0, -1),
                                   'connections': get_connections()}))


@route('/nodes/<name>')
def get_node(name):
    prefix = 'dotm::nodes::' + name
    nodeDetails = rdb.hgetall(prefix)
    prefix = 'dotm::services::' + name + '::'
    serviceDetails = {}
    services = [s.replace(prefix, '') for s in rdb.keys(prefix + '*')]
    for s in services:
        serviceDetails[s] = rdb.hgetall(prefix + s)

    prefix = 'dotm::connections::' + name + '::'
    connectionDetails = {}
    connections = [c.replace(prefix, '') for c in rdb.keys(prefix + '*')]
    for c in connections:
        tmp = c.split('::')
        if len(tmp) == 2:
            cHash = rdb.hgetall(prefix + c)
            cHash['localPort'] = tmp[0]
            cHash['remoteHost'] = tmp[1]
            connectionDetails[c] = cHash

    serviceAlerts = []
    for s in rdb.lrange(mon_services_key_pfx + name, 0, -1):
        serviceAlerts.extend(json.loads(s))

    # Map node alerts to services
    # NOTE: This for->for->for doesn't look good :)
    service_mapping = get_setting('service_mapping')
    for service_regexp in service_mapping:
        for sa in serviceAlerts:
            if re.match(service_regexp, sa['service']):
                for s in serviceDetails:
                    if re.match(service_mapping[service_regexp], serviceDetails[s]['process'], re.IGNORECASE):
                        serviceDetails[s]['alert_status'] = sa['status']
                        sa['mapping'] = serviceDetails[s]['process']

    return resp_or_404(json.dumps({'name': name,
                                   'status': nodeDetails,
                                   'services': serviceDetails,
                                   'connections': connectionDetails,
                                   'monitoring': {
                                       'node': rdb.get(mon_nodes_key_pfx + name),
                                       'services': serviceAlerts
                                   },
                                   'settings': {
                                       'aging': get_setting('aging'),
                                   }}))


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


@route('/settings', method='GET')
def get_settings():
    for s in settings:
        settings[s]['values'] = get_setting(s)

    return resp_or_404(json.dumps(settings), 'application/javascript', 'no-cache, no-store, must-revalidate')


@route('/mon/nodes')
def get_mon_nodes():
    node_arr = rdb.keys(mon_nodes_key_pfx + '*')
    return resp_or_404(json.dumps([n.split('::')[-1]for n in node_arr])
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


@route('/mon/reload', method='POST')
def mon_reload():
    config = get_setting('nagios_instance')
    time_now = int(time.time())
    update_time_key = 'last_updated'
    update_lock_key = mon_config_key_pfx + 'update_running'
    update_lock_expire = config['refresh'] * 5
    update_time_str = rdb.hget(mon_config_key, update_time_key)
    if update_time_str and not rdb.get(update_lock_key):
        update_time = int(update_time_str)
        if time_now - update_time >= config['refresh']:
            rdb.setex(update_lock_key, update_lock_expire, 1)
            mon = DOTMMonitor(config['url'], config['user'], config['password'])
            for key, val in mon.get_nodes().items():
                # Apply user defined node mapping
                tmp = rdb.hget(config_key_pfx + "::user_node_aliases", key)
                if tmp:
                    val['node'] = tmp   # Overwrite hostname given by Nagios

                # And store...
                rdb.setex(mon_nodes_key_pfx + val['node'], json.dumps(val), config['expire'])
            for key, val in mon.get_services().items():
                # Apply user defined node mapping
                node = rdb.hget(config_key_pfx + "::user_node_aliases", key)
                if not node:
                    node = key  # Overwrite hostname given by Nagios

                # And store...
                with rdb.pipeline() as pipe:
                    pipe.delete(mon_services_key_pfx + node)
                    pipe.lpush(mon_services_key_pfx + node, json.dumps(val))
                    pipe.expire(mon_services_key_pfx + node, config['expire'])
                    pipe.execute()
            time_now = int(time.time())
            rdb.hset(mon_config_key, update_time_key, time_now)
            update_time = time_now
            rdb.delete(update_lock_key)
        return resp_or_404(vars_to_json(update_time_key, update_time))
    elif update_time_str:
        update_time = int(update_time_str)
        return resp_or_404(vars_to_json(update_time_key, update_time))
    else:
        rdb.hset(mon_config_key, update_time_key, 0)
    return resp_or_404()


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


if __name__ == '__main__':
    debug(mode=True)
    run(host='localhost', port=8080, reloader=True)
