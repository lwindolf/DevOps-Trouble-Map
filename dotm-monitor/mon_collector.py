import configparser
from dotm_mon import DOTMMonitor
from dotm_redis import DOTMRedis

config = configparser.ConfigParser()
config.read('.mr.developer.cfg')

mon_url = config['monitoring']['url']
mon_user = config['monitoring']['user']
mon_paswd = config['monitoring']['paswd']

m = DOTMMonitor(mon_url, mon_user, mon_paswd)
r = DOTMRedis('mon')

for k,v in m.get_json().items():
	r[k] = v
