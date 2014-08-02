-- Lua function for Redis to implement missing COPY functionality

local var_type = redis.call('type', KEYS[1])['ok']
if var_type == 'string' then
    redis.call('SET', KEYS[2], redis.call('GET', KEYS[1]))
    return true
elseif var_type == 'hash' then
    redis.call('hmset', KEYS[2], unpack(redis.call('hgetall', KEYS[1])))
    return true
elseif var_type == 'list' then
    redis.call('rpush', KEYS[2], unpack(redis.call('lrange', KEYS[1], 0, -1)))
    return true
end