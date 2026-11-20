-- A delivery failed and the entry stays pending: remember why, for the hint when the tries run out.
-- Compare-and-set on run_id, so a stale worker never writes over a newer run.
-- KEYS: 1 doc hash
-- ARGV: 1 run id, 2 cause
-- Returns 1 noted, 0 stale
local cur = redis.call('HMGET', KEYS[1], 'run_id', 'status')
if cur[1] ~= ARGV[1] or cur[2] ~= 'processing' then
  return 0
end
redis.call('HSET', KEYS[1], 'last_error', ARGV[2])
return 1
