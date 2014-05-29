# -*- coding: utf-8 -*-
import requests
import json

class DOTMMonitor:

	version = '0.1.2'

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
			service = elem['service']
			if hostname not in rjs:
				rjs[hostname] = {}
			rjs[hostname][service] = {
				'status': elem['status'],
				'last_check': elem['last_check'],
				'duration': elem['duration'],
				'status_information': elem['status_information']
			}
		return rjs

	def get_json(self):
		"""
		Returned json format:

		{
			"hostname01": {
				"Service01 name": {
					"status": "OK",
					"last_check": "<timedate>",
					"duration": "<nagios guration format>", #FIXME: figure out the way to unify it
					"status_information": "Service01 status information"
				},
				"Service02 name": {
					"status": "CRITICAL",
					"last_check": "<timedate>",
					"duration": "<nagios guration format>",
					"status_information": "Service02 status information"
				},
			},
			"hostname02": {
				.
				.
				.
			},
			.
			.
			.
		}
		"""
		if self.provider == 'icinga':
			return self._get_json_icinga()
		elif provider == 'nagios':
			#TODO: implement more providers for Monitoring.get_json()
			pass

