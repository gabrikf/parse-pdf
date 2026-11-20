-- Reparse or requeue: queue a final document again with a new run and no old results.
-- KEYS: 1 doc hash, 2 pages, 3 chunks, 4 feed (all), 5 feed parsed, 6 feed failed,
--       7 feed active, 8 stream
-- ARGV: 1 allowed statuses (comma separated), 2 new run id, 3 parser, 4 updated_at, 5 ttl,
--       6 document id, 7 object key
-- Returns 1 queued, 0 missing, -1 status not allowed (someone else changed it first)
local cur = redis.call('HMGET', KEYS[1], 'status', 'created_ms')
if not cur[1] then
  return 0
end

local allowed = false
for status in string.gmatch(ARGV[1], '[^,]+') do
  if status == cur[1] then
    allowed = true
  end
end
if not allowed then
  return -1
end

redis.call('HSET', KEYS[1], 'status', 'queued', 'run_id', ARGV[2], 'parser', ARGV[3],
  'deliveries', 0, 'updated_at', ARGV[4])
redis.call('HDEL', KEYS[1], 'summary', 'error_code', 'hint')
redis.call('DEL', KEYS[2], KEYS[3])
redis.call('ZREM', KEYS[5], ARGV[6])
redis.call('ZREM', KEYS[6], ARGV[6])
redis.call('ZADD', KEYS[7], cur[2], ARGV[6])
redis.call('XADD', KEYS[8], '*', 'document_id', ARGV[6], 'object_key', ARGV[7], 'run_id', ARGV[2])
for _, i in ipairs({1, 4, 7}) do
  redis.call('EXPIRE', KEYS[i], ARGV[5])
end
return 1
