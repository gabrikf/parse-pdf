-- Take one in-flight slot (door 8). KEYS: 1 counter   ARGV: 1 maximum, 2 safety ttl s
local count = redis.call('INCR', KEYS[1])
redis.call('EXPIRE', KEYS[1], ARGV[2])
if count > tonumber(ARGV[1]) then
  redis.call('DECR', KEYS[1])
  return 0
end
return 1
