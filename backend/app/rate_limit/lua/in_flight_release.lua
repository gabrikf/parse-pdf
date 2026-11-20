-- Give one in-flight slot back (door 8). KEYS: 1 counter
-- One script, so no acquire runs between the DECR and the DEL and loses its count.
local count = redis.call('DECR', KEYS[1])
if count <= 0 then
  redis.call('DEL', KEYS[1])
end
return count
