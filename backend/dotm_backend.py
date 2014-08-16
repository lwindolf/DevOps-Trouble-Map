#!/usr/bin/env python
# -*- coding: utf-8 -*-

import signal
import sys
import logging

# Backend local imports
# FIXME: import only what is needed instead of *
from settings import *
from dotm_queue import QResponse
from dotm_monitor import DOTMMonitor


# Handle SIGINT in Debug mode
def signal_handler(signal, frame):
    print 'Exit on SIGINT'
    sys.exit(1)

signal.signal(signal.SIGINT, signal_handler)

# Logging configuration
log_file = '/tmp/dotm_backend.log'
log_level = logging.INFO
log_format = logging.Formatter("%(asctime)s %(levelname)-8s %(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

if cl_args.log:
    log_file = cl_args.log
if cl_args.debug:
    log_level = logging.DEBUG
    # Additionally log to console in DEBUG mode
    log_ch = logging.StreamHandler()
    log_ch.setFormatter(log_format)
    log_ch.setLevel(log_level)
    logger.addHandler(log_ch)

log_fh = logging.FileHandler(log_file)
log_fh.setFormatter(log_format)
log_fh.setLevel(log_level)
logger.addHandler(log_fh)

# Lua function for Redis to implement missing COPY functionality
redis_copy = rdb.script_load("""local var_type = redis.call('type', KEYS[1])['ok']
if var_type == 'string' then
    redis.call('SET', KEYS[2], redis.call('GET', KEYS[1]))
    return true
elseif var_type == 'hash' then
    redis.call('hmset', KEYS[2], unpack(redis.call('hgetall', KEYS[1])))
    return true
elseif var_type == 'list' then
    redis.call('rpush', KEYS[2], unpack(redis.call('lrange', KEYS[1], 0, -1)))
    return true
end""")

def process_queue():
    """Process Redis message queue"""
    logger.info('DOTM Backend Started')
    while True:
        try:
            msg_data = rdb.blpop(ns.queue)
        except Exception as e:
            logger.error('Error getting message from the queue: {}'.format(e))
            continue

        try:
            msg_obj = json.loads(msg_data[1])
            logger.debug('Message received for processing: {}'.format(msg_obj))
        except Exception as e:
            logger.warning('Message discarded (Bad message format)')
            logger.debug('Message: {}\nException: {}'.format(msg_data, e))
            continue

        try:
            if msg_obj and msg_obj['fn'] == 'reload':
                msg_key = msg_obj['id']
                qresp = QResponse(rdb, msg_key, logger)
                qresp.processing()
                logger.info('Reloading monitoring data')
                result = monitoring_reload()
                qresp.ready(result)
        except TypeError as e:
            logger.critical('Wrong message type in the queue! Skipping...')
            logger.debug('Message: {}\nException: {}'.format(msg_data, e))
            continue


def func_on_keys(func, prefix):
    """Run passed function on a set of keys defined by prefix"""
    i = 0
    while True:
        i, keys = rdb.execute_command('SCAN', int(i), 'COUNT', 100, 'MATCH', prefix + '*')
        func(keys)
        if int(i) == 0:
            break


def history_add():
    """Copy keys to history (<timestamp>::<key>) while resetting expiration"""

    time_now = int(time.time())
    logger.info("Adding history snapshot " + str(time_now))

    def copy_keys_to_history(keys):
        for key in keys:
            for pat in history_key_set:
                if key.startswith(pat):
                    rdb.evalsha(redis_copy, 2, key, str(time_now) + '::' + key)
                    break

    func_on_keys(copy_keys_to_history, ns.prefix)
    rdb.rpush(ns.history, time_now)


def history_rotate(keep_sec=0):
    """Rotate history by removing old keys (default: 0 - do not keep history)"""
    time_now = int(time.time())
    time_limit = time_now - keep_sec

    def delete_keys(keys):
        for key in keys:
            rdb.delete(key)

    while True:
        try:
            hist_first = rdb.lrange(ns.history, 0, 1)[0]
        except IndexError:
            break
        if int(hist_first) < time_limit:
            func_on_keys(delete_keys, hist_first)
            rdb.lpop(ns.history)
        else:
            break

def update_history():
    now = int(time.time())
    settings = get_setting('history')
    if int(settings['enabled']) == 1:
        last_snapshot = rdb.get(ns.state + '::last_snapshot')
        if not last_snapshot or now - int(last_snapshot) >= int(settings['interval']):
            history_add()
            history_rotate(int(settings['expire']))
            rdb.set(ns.state + '::last_snapshot', now)
        else:
            logger.debug("Creating no snapshot yet as last one was done before "+str(now - int(last_snapshot))+ "s and interval is "+str(settings['interval'])+"s")

def monitoring_reload():
    # FIXME: add logging to monitoring_reload()
    service_aging = int(get_setting('aging')['Services'])
    service_mapping = get_setting('service_mapping')
    config = get_setting('nagios_instance')
    time_now = int(time.time())
    update_time_key = ns.state + '::last_updated'
    update_lock_key = ns.state + '::update_running'
    update_lock_expire = config['refresh'] * 5
    update_time_str = rdb.get(update_time_key)
    if update_time_str and not rdb.get(update_lock_key):
        update_time = int(update_time_str)
        if time_now - update_time >= int(config['refresh']):
            rdb.setex(update_lock_key, update_lock_expire, 1)
            mon = DOTMMonitor(config['url'], config['user'], config['password'], logger=logger)

            # FIXME: not sure this is a good way. Planning on moving reload lock and history operation
            # higher up the call chain.

            # Put keys to history before reloading monitoring
            update_history()

            # Track broken mapped services per node to later save them into node alert info
            tmp_services_broken = {}

            # 1. Process and save services
            for key, val in mon.get_services().items():
                # Apply user defined node mapping or overwrite hostname given by Nagios
                node = rdb.hget(ns.config + "::user_node_aliases", key) or key

                service_details = get_service_details(node)
                if service_details:
                    # FIXME: Refactor for/for/for (Andrej)
                    for service_regexp in service_mapping:
                        for s in service_details:
                            # Do time diff to indicate out-dated services
                            age = 'old'
                            if 'last_connection' in service_details[s]:
                                if time_now - int(service_details[s]['last_connection']) < service_aging:
                                    age = 'fresh'
                            rdb.hset(ns.services + '::' + node + '::' + s, 'age', age)

                            # Map node alerts to services and store service
                            # alert summary into node alerts, these are two
                            # denormalizations used to simplify the /nodes
                            # and the /node/<name> callback.
                            for sa in val:
                                if re.match(service_regexp, sa['service']):
                                    if re.match(service_mapping[service_regexp],
                                                service_details[s]['process'],
                                                re.IGNORECASE):
                                        rdb.hset(ns.services + '::' + node + '::' + s, 'alert_status', sa['status'])
                                        sa['mapping'] = service_details[s]['process']
                                        # Add non-OK services to it's nodes alert info
                                        if sa['status'] != 'OK':
                                            if not node in tmp_services_broken:
                                                tmp_services_broken[node] = {}
                                            tmp_services_broken[node][service_details[s]['process']] = sa['status']

                # And store in list...
                rdb.delete(ns.services_checks + '::' + node)
                for v in val:
                    rdb.lpush(ns.services_checks + '::' + node, json.dumps(v))
                rdb.expire(ns.services_checks + '::' + node, config['expire'])

            # 2. Merge broken services into node info and save it
            for key, val in mon.get_nodes().items():
                # Apply user defined node mapping
                tmp = rdb.hget(ns.config + '::user_node_aliases', key)
                if tmp:
                    val['node'] = tmp   # Overwrite hostname given by Nagios
                # Merge broken services summary
                if val['node'] in tmp_services_broken:
                    val['services_alerts'] = tmp_services_broken[val['node']]

                # And store in string...
                rdb.setex(ns.nodes_checks + '::' + val['node'], json.dumps(val), config['expire'])

            time_now = int(time.time())
            rdb.set(update_time_key, time_now)
            update_time = time_now
            rdb.delete(update_lock_key)
        return {update_time_key.split('::')[-1]: update_time}
    elif update_time_str:
        update_time = int(update_time_str)
        return {update_time_key.split('::')[-1]: update_time}
    else:
        rdb.set(update_time_key, 0)
    return None


if __name__ == '__main__':
    process_queue()
