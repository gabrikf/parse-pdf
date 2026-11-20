-- Save a run's pages, summary and final status in one step, if the run is still current.
-- KEYS: 1 doc hash, 2 pages, 3 chunks, 4 feed (all), 5 feed active, 6 feed target group
-- ARGV: 1 run id, 2 status, 3 updated_at, 4 ttl, 5 document id, 6 summary, 7 error code,
--       8 hint, 9.. page json
local cur = redis.call('HMGET', KEYS[1], 'run_id', 'status', 'created_ms')
if cur[1] ~= ARGV[1] or cur[2] ~= 'processing' then
  return 0
end

redis.call('DEL', KEYS[2], KEYS[3])
local batch = {}
for i = 9, #ARGV do
  batch[#batch + 1] = ARGV[i]
  if #batch == 500 then
    redis.call('RPUSH', KEYS[2], unpack(batch))
    batch = {}
  end
end
if #batch > 0 then
  redis.call('RPUSH', KEYS[2], unpack(batch))
end

redis.call('HSET', KEYS[1], 'status', ARGV[2], 'updated_at', ARGV[3])
local optional = {summary = ARGV[6], error_code = ARGV[7], hint = ARGV[8]}
for field, value in pairs(optional) do
  if value == '' then
    redis.call('HDEL', KEYS[1], field)
  else
    redis.call('HSET', KEYS[1], field, value)
  end
end

redis.call('ZREM', KEYS[5], ARGV[5])
redis.call('ZADD', KEYS[6], cur[3], ARGV[5])
for _, i in ipairs({1, 2, 4, 6}) do
  if redis.call('EXISTS', KEYS[i]) == 1 then
    redis.call('EXPIRE', KEYS[i], ARGV[4])
  end
end
return 1
