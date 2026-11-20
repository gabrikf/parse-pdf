-- A worker starts (or resumes) a run. Compare-and-set on run_id: a stale entry changes nothing.
-- KEYS: 1 doc hash, 2 feed (all), 3 feed active, 4 feed failed, 5 pages, 6 chunks
-- ARGV: 1 run id, 2 max deliveries, 3 updated_at, 4 ttl, 5 document id
-- Returns {outcome, deliveries}: stale | already_final | exhausted | started
if redis.call('EXISTS', KEYS[1]) == 0 then
  return {'stale', 0}
end

local cur = redis.call('HMGET', KEYS[1], 'run_id', 'status', 'deliveries', 'created_ms')
if cur[1] ~= ARGV[1] then
  return {'stale', 0}
end

local status = cur[2]
if status == 'ready' or status == 'no_text' or status == 'dead' then
  return {'already_final', tonumber(cur[3] or '0')}
end
if status ~= 'queued' and status ~= 'processing' then
  return {'stale', 0}
end

local deliveries = tonumber(cur[3] or '0') + 1
redis.call('HSET', KEYS[1], 'deliveries', deliveries, 'updated_at', ARGV[3])

local outcome = 'started'
if deliveries > tonumber(ARGV[2]) then
  outcome = 'exhausted'
  redis.call('HSET', KEYS[1], 'status', 'dead', 'error_code', 'max_deliveries')
  redis.call('ZREM', KEYS[3], ARGV[5])
  redis.call('ZADD', KEYS[4], cur[4], ARGV[5])
  redis.call('DEL', KEYS[6])
else
  redis.call('HSET', KEYS[1], 'status', 'processing')
end

for i = 1, 6 do
  if redis.call('EXISTS', KEYS[i]) == 1 then
    redis.call('EXPIRE', KEYS[i], ARGV[4])
  end
end
return {outcome, deliveries}
