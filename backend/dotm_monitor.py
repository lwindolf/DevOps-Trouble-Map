# -*- coding: utf-8 -*-
import requests
import json
import time


class DOTMMonitor(object):
    """Class to deliver monitoring data"""

    version = '0.2.1'

    def __init__(self, mon_url, user=None, paswd=None, provider='icinga', logger=None):
        self.user = user
        self.paswd = paswd
        self.provider = provider
        self.logger = logger
        if provider == 'icinga':
            self.mon_url = mon_url.rstrip('/') + '/status.cgi?style=hostservicedetail&jsonoutput'
        elif provider == 'nagios':
            # TODO: implement more providers for DOTMMonitor.mon_url
            pass
        else:
            raise NameError('Unknown provider')

    def _output(self, msg, level=40):
        # Use logger for output if defined, otherwise print to console
        if self.logger:
            self.logger.log(level, msg)
        else:
            print(msg)

    def _get_req(self):
        # Get request object from monitoring server
        try:
            if self.user and self.paswd:
                return requests.get(self.mon_url, auth=(self.user, self.paswd), verify=False, timeout=10)
            return requests.get(self.mon_url, verify=False)
        except Exception as e:
            self._output(e)

    def get_data(self):
        """Get text data from monitoring server"""
        req = self._get_req()
        if 'req' not in locals() or req is None:
            self._output('Connection to {} failed'.format(self.mon_url))
            return None
        if req.ok:
            return req.text
        else:
            self._output('Error getting Monitoring data from {}'
                         ' (status_code: {})'.format(self.mon_url, req.status_code))

    @staticmethod
    def _nagios_last_check_converter(last_check):
        # Convert nagios "last check" format to timestamp
        return int(time.mktime(time.strptime(last_check, "%Y-%m-%d %H:%M:%S")))

    @staticmethod
    def _nagios_duration_converter(last_check_epoch, duration):
        # Convert nagios "duration" format to timestamp
        m = ''.join(filter(lambda x: x.isdigit() or x.isspace(), duration)).split()
        return last_check_epoch - (int(m[0]) * 86400 + int(m[1]) * 3600 + int(m[2]) * 60 + int(m[3]))

    def _get_nodes_icinga(self):
        # Get nodes status from Icinga
        data = self.get_data()
        try:
            json_data = json.loads(data.replace('\t', ' '))
        except (ValueError, AttributeError):
            self._output('Value returned by Monitoring server is not in JSON format')
            return {}
        js = json_data['status']['host_status']
        rjs = {}
        for elem in js:
            last_check = self._nagios_last_check_converter(elem['last_check'])
            last_status_change = self._nagios_duration_converter(last_check, elem['duration'])
            rjs[elem['host']] = {
                'node': elem['host'],
                'status': elem['status'],
                'last_check': last_check,
                'last_status_change': last_status_change,
                'status_information': elem['status_information']
            }
        return rjs

    def _get_services_icinga(self):
        # Get services status from Icinga
        data = self.get_data()
        try:
            json_data = json.loads(data.replace('\t', ' '))
        except (ValueError, AttributeError):
            self._output('Value returned by Monitoring server is not in JSON format')
            return {}
        js = json_data['status']['service_status']
        rjs = {}
        for elem in js:
            hostname = elem['host']
            if hostname not in rjs:
                rjs[hostname] = []
            last_check = self._nagios_last_check_converter(elem['last_check'])
            last_status_change = self._nagios_duration_converter(last_check, elem['duration'])
            rjs[hostname].append({
                'node': hostname,
                'service': elem['service'],
                'status': elem['status'],
                'last_check': last_check,
                'last_status_change': last_status_change,
                'status_information': elem['status_information']
            })
        return rjs

    def get_nodes(self):
        """
        Get nodes status from monitoring server
        Returns JSON of format:
        {
            "hostname01": {
                "node": "hostname01",
                "status": "UP",
                "last_check": <timestamp>,
                "last_status_change": <timestamp>,
                "status_information": "hostname01 status information"
            },
            "hostname02": {
                "node": "hostname02",
                "status": "DOWN",
                "last_check": <timestamp>,
                "last_status_change": <timestamp>,
                "status_information": "hostname01 status information"
            },
            .
            .
            .
        }
        """
        if self.provider == 'icinga':
            return self._get_nodes_icinga()
        elif self.provider == 'nagios':
            # TODO: implement more providers for DOTMMonitor.get_hosts()
            pass

    def get_services(self):
        """
        Get services status from monitoring server
        Returns JSON of format:
        {
            "hostname01": [
                {
                    "node": "hostname01"
                    "service": "Service01 name",
                    "status": "OK",
                    "last_check": <timestamp>,
                    "last_status_change": <timestamp>,
                    "status_information": "Service01 status information"
                },
                {
                    "node": "hostname01"
                    "service": "Service02 name",
                    "status": "CRITICAL",
                    "last_check": <timestamp>,
                    "last_status_change": <timestamp>,
                    "status_information": "Service02 status information"
                },
            ],
            "hostname02": [
                .
                .
                .
            ],
            .
            .
            .
        }
        """
        if self.provider == 'icinga':
            return self._get_services_icinga()
        elif self.provider == 'nagios':
            # TODO: implement more providers for DOTMMonitor.get_services()
            pass
