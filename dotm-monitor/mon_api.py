from bottle import route, run, response
from dotm_redis import DOTMRedis
import json

rdb = DOTMRedis('mon')

@route('/mon/get/<host>')
def get_host(host):
	response.content_type = 'application/json'
	result = rdb.get(host) or b'{}'
	return json.dumps(result.decode('utf-8'), ensure_ascii=False).strip('"')
	
if __name__ == "__main__":
	run(host='localhost', port=8081, debug=True)
