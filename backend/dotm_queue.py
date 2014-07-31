# -*- coding: utf-8 -*-
import json


class QResponse(object):
    """Queue response helper class"""

    version = '0.1.0'

    def __init__(self, rdb, key, logger=None, expire=300):
        self.rdb = rdb
        self.key = key
        self.expire = expire
        self.logger = logger

    def _qresp(self, status, msg=None):
        # Put response to the queue
        try:
            resp = json.dumps({'status': status, 'result': msg})
        except TypeError:
            if self.logger:
                self.logger.critical('Wrong message format: {}'.format(msg))
            else:
                print('Wrong message format: {}'.format(msg))
            return None

        if self.logger:
            self.logger.debug('Queued response: {} => {}'.format(self.key, resp))
        self.rdb.setex(self.key, resp, self.expire)

    def queue(self, action, *args, **kwargs):
        qobj = {"id": self.key, "fn": action, "args": [a for a in args], "kwargs": kwargs}
        try:
            qjson = json.dumps(qobj)
        except TypeError:
            if self.logger:
                self.logger.critical('Wrong message format: {}'.format(qobj))
            else:
                print('Wrong message format: {}'.format(qobj))
            return None

        self.rdb.rpush(self.key.rsplit('::', 2)[0], qjson)

    def pending(self):
        """Set response state to 'pending'"""
        self._qresp('pending')

    def processing(self):
        """Set response state to 'processing'"""
        self._qresp('processing')

    def ready(self, msg):
        """Set response state to 'ready' and return the result"""
        self._qresp('ready', msg)
