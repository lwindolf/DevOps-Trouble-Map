# -*- coding: utf-8 -*-
import requests
import json
import time


class DOTMMonitor:

    version = '0.1.6'

    def __init__(self, mon_url, user=None, paswd=None, provider='icinga'):
        self.user = user
        self.paswd = paswd
        self.provider = provider
        if provider == 'icinga':
            self.mon_url = mon_url.rstrip('/') + '/cgi-bin/icinga/status.cgi?style=hostservicedetail&jsonoutput'
        elif provider == 'nagios':
            # TODO: implement more providers for Monitoring.mon_url
            pass
        else:
            raise NameError('Unknown provider')

    def _get_req(self):
        if self.user and self.paswd:
            return requests.get(self.mon_url, auth=(self.user, self.paswd), verify=False)
        else:
            return requests.get(self.mon_url, verify=False)

    def get_data(self):
        return self._get_req().text

    def _nagios_last_check_converter(self, last_check):
        return int(time.mktime(time.strptime(last_check, "%Y-%m-%d %H:%M:%S")))

    def _nagios_duration_converter(self, last_check_epoch, duration):
        m = ''.join(filter(lambda x: x.isdigit() or x.isspace(), duration)).split()
        return last_check_epoch - (int(m[0]) * 86400 + int(m[1]) * 3600 + int(m[2]) * 60 + int(m[3]))

    def _get_nodes_icinga(self):
        data = self.get_data()
        jsonData = json.loads(data.replace('\t', ' '))
        js = jsonData.get('status').get('host_status')
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
        data = self.get_data()
        jsonData = json.loads(data.replace('\t', ' '))
        js = jsonData.get('status').get('service_status')
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
        Return JSON format:

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
            # TODO: implement more providers for Monitoring.get_hosts()
            pass

    def get_services(self):
        """
        Returned JSON format:

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
            # TODO: implement more providers for Monitoring.get_services()
            pass
