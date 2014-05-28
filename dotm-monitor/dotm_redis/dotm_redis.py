# -*- coding: utf-8 -*-
import redis

class DOTMRedis:

	version = '0.1.1'

	def __init__(self, name, host='localhost', port=6379, **kw):
		self.name = name
		self.conn = redis.Redis(host=host, port=port, **kw)

	def clear(self):
		self.conn.delete(self.name)

	def keys(self, substring):
		return self.conn.keys(substring) or []

	def hkeys(self):
		return self.conn.hkeys(self.name) or []

	def get(self, key):
		return self.conn.hget(self.name, key)

	def iter(self):
		for k in self.keys():
			yield k

	def __iter__(self):
		return self.iter()

	def __len__(self):
		return self.conn.hlen(self.name) or 0

	def __getitem__(self, key):
		val = self.get(key)
		if val: return val
		raise KeyError

	def __setitem__(self, key, value):
		self.conn.hset(self.name, key, value)

	def __delitem__(self, key):
		self.conn.hdel(self.name, key)

	def __contains__(self, key):
		return self.conn.hexists(self.name, key)

	def lrange(self, key, start=0, stop=-1):
		return self.conn.lrange(key, start, stop)

