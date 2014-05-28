# -*- coding: utf-8 -*-
import requests
import json
from hashlib import md5

class DOTMMonitor:

	version = '0.1.0'

	def __init__(self, mon_url, user=None, paswd=None, provider='icinga'):
		self.user = user
		self.paswd = paswd
		self.provider = provider
		if provider == 'icinga':
			self.mon_url = mon_url.rstrip('/') + '/cgi-bin/icinga/status.cgi?&style=detail&jsonoutput'
		elif provider == 'nagios':
			#TODO: implement more providers for Monitoring.mon_url
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

	def _get_json_icinga(self):
		data = self.get_data()
		jsonData = json.loads(data.replace('\t', ' '))
		js = jsonData.get('status').get('service_status')
		rjs = {}
		for elem in js:
			hostname = elem['host']
			if hostname not in rjs:
				rjs[hostname] = {
						'OK': [],
						'WARNING': [],
						'CRITICAL': [],
						'UNKNOWN': []
						}
			hostname_hash = hostname + '_' + md5(bytes(elem['service'], encoding='utf-8')).hexdigest()
			if hostname_hash in rjs:
				raise KeyError('Duplicate hash')
			if elem['status'] in rjs[hostname]:
				rjs[hostname][elem['status']].append(hostname_hash)
			else:
				rjs[hostname]['UNKNOWN'].append(hostname_hash)
			rjs[hostname_hash] = {
					'service': elem['service'],
					'status': elem['status'],
					'last_check': elem['last_check'],
					'duration': elem['duration'],
					'status_information': elem['status_information']
					}
		return rjs
		

	def get_json(self):
		"""
		Returned json format:
		$hostname: { “OK”: ["$hostnem_$hash1”, "$hostname_$hash3”], “CRITICAL”: [“$hostname_$hash2”], …  }
		$hostname_$hash1: {
			"service": "uwsgi 9006”,
			"status": “OK”,
			"last_check": "2014-05-26 18:49:46”,
			"duration": "12d  7h 44m 24s”,
			"status_information": "TCP OK - 0.000 second response time on port 9006"
		}
		$hostname_$hash2: {
			"service": “Backups”,
			"status": "CRITICAL”,
			"last_check": "2014-05-26 18:08:19”,
			"duration": "0d  0h 42m 53s”,
			"status_information": "Backup is not in S3 (test-2014-05-27 not found)"
		}

		states: OK, WARNING, CRITICAL, UNKNOWN
		"""
		if self.provider == 'icinga':
			return self._get_json_icinga()
		elif provider == 'nagios':
			#TODO: implement more providers for Monitoring.get_json()
			pass

