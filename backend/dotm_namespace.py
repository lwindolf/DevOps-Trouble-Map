# -*- coding: utf-8 -*-


class DOTMNamespace(object):
    """Class to automatically generate DOTM Redis namespace on the fly (needed for history feature)"""

    version = '0.2.0'

    def __init__(self, history_key=None):
        self.prefix = 'dotm'
        if history_key:
            self.history_prefix = history_key + '::' + self.prefix
        else:
            self.history_prefix = self.prefix

        self.nodes = self.history_prefix + '::nodes'
        self.connections = self.history_prefix + '::connections'
        self.services = self.history_prefix + '::services'
        self.config = self.history_prefix + '::config'
        self.resolver = self.history_prefix + '::resolver'

        self.checks = self.history_prefix + '::checks'
        self.nodes_checks = self.checks + '::nodes'
        self.services_checks = self.checks + '::services'

        self.queue = self.prefix + '::queue'
        self.history = self.prefix + '::history'