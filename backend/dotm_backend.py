#!/usr/bin/env python
# -*- coding: utf-8 -*-

import daemon
import logging

# Backend local imports
# FIXME: import only what is needed instead of *
from settings import *
from dotm_monitor import DOTMMonitor


def monitor_queue():
    print "Started!"
    # TODO: Implement logging
    while True:
        try:
            msg = json.loads(rdb.blpop(queue_key_pfx)[1])
        except Exception as e:
            #logging.critical(e)
            print e
            continue
        if msg and msg['fn'] == 'reload':
            # TODO: move queue_result_expire variable to settings
            print msg
            result = mon_reload()
            print result
            rdb.setex(msg['id'], result, 300)


def mon_reload():
    service_mapping = get_setting('service_mapping')
    config = get_setting('nagios_instance')
    time_now = int(time.time())
    update_time_key = 'last_updated'
    update_lock_key = mon_config_key_pfx + 'update_running'
    update_lock_expire = config['refresh'] * 5
    update_time_str = rdb.hget(mon_config_key, update_time_key)
    if update_time_str and not rdb.get(update_lock_key):
        update_time = int(update_time_str)
        if time_now - update_time >= int(config['refresh']):
            rdb.setex(update_lock_key, update_lock_expire, 1)
            mon = DOTMMonitor(config['url'], config['user'], config['password'])

            # Track broken mapped services per node to later save them into node alert info
            tmp_services_broken = {}

            # 1. Process and save services
            for key, val in mon.get_services().items():
                # Apply user defined node mapping
                node = rdb.hget(config_key_pfx + "::user_node_aliases", key)
                if not node:
                    node = key  # Overwrite hostname given by Nagios

                # Map node alerts to services and store service
                # alert summary into node alerts, these are two
                # denormalizations used to simplify the /nodes
                # and the /node/<name> callback.
                serviceDetails = get_service_details(node)
                if serviceDetails:
                    # FIXME: Refactor for/for/for (Andrej)
                    for service_regexp in service_mapping:
                        for s in serviceDetails:
                            for sa in val:
                                if re.match(service_regexp, sa['service']):
                                    if re.match(service_mapping[service_regexp],
                                                serviceDetails[s]['process'],
                                                re.IGNORECASE):
                                        rdb.hset('dotm::services::' + node + '::' + s, 'alert_status', sa['status'])
                                        sa['mapping'] = serviceDetails[s]['process']
                                        # Add non-OK services to it's nodes alert info
                                        if sa['status'] != 'OK':
                                            if not node in tmp_services_broken:
                                                tmp_services_broken[node] = {}
                                            tmp_services_broken[node][serviceDetails[s]['process']] = sa['status']

                # And store...
                with rdb.pipeline() as pipe:
                    pipe.delete(mon_services_key_pfx + node)
                    pipe.lpush(mon_services_key_pfx + node, json.dumps(val))
                    pipe.expire(mon_services_key_pfx + node, config['expire'])
                    pipe.execute()

            # 2. Merge broken services into node info and save it
            for key, val in mon.get_nodes().items():
                # Apply user defined node mapping
                tmp = rdb.hget(config_key_pfx + "::user_node_aliases", key)
                if tmp:
                    val['node'] = tmp   # Overwrite hostname given by Nagios
                # Merge broken services summary
                # FIXME: This is failing due to KeyError exception, need to investigate (commented)
                #val['services_alerts'] = tmp_services_broken[val['node']]

                # And store...
                rdb.setex(mon_nodes_key_pfx + val['node'], json.dumps(val), config['expire'])

            time_now = int(time.time())
            rdb.hset(mon_config_key, update_time_key, time_now)
            update_time = time_now
            rdb.delete(update_lock_key)
        return vars_to_json(update_time_key, update_time)
    elif update_time_str:
        update_time = int(update_time_str)
        return vars_to_json(update_time_key, update_time)
    else:
        rdb.hset(mon_config_key, update_time_key, 0)
    return None

if __name__ == '__main__':
    if cl_args.debug:
        monitor_queue()
    else:
        with daemon.DaemonContext():
            monitor_queue()