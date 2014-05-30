import configparser
from dotm_mon import DOTMMonitor
from dotm_redis import DOTMRedis

def collect():
	config = configparser.ConfigParser()
	config.read('.mr.developer.cfg')

	mon_url = config['monitoring']['url']
	mon_user = config['monitoring']['user']
	mon_paswd = config['monitoring']['paswd']
	mon_hosts_key = config['monitoring']['hosts_key'] # dotm::mon::hosts
	mon_services_key = config['monitoring']['services_key'] # dotm::mon::services

	mon = DOTMMonitor(mon_url, mon_user, mon_paswd)
	rdb_hosts = DOTMRedis(mon_hosts_key)
	rdb_services = DOTMRedis(mon_services_key)

	for key,value in mon.get_hosts().items():
		rdb_hosts[key] = value

	for key,value in mon.get_services().items():
		rdb_services[key] = value


if __name__ == "__main__":
	collect()
