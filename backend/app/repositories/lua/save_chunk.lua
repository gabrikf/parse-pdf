-- Checkpoint one model chunk, only while the run is still current and processing.
-- KEYS: 1 doc hash, 2 chunks hash   ARGV: 1 run id, 2 chunk index, 3 pages json, 4 ttl
local cur = redis.call('HMGET', KEYS[1], 'run_id', 'status')
if cur[1] ~= ARGV[1] or cur[2] ~= 'processing' then
  return 0
end
redis.call('HSET', KEYS[2], ARGV[2], ARGV[3])
redis.call('EXPIRE', KEYS[2], ARGV[4])
return 1
