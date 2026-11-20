-- Delete a document and every key and feed entry it owns, unless a worker is processing it.
-- KEYS: 1 doc hash, 2 pages, 3 chunks, 4 feed (all), 5 parsed, 6 failed, 7 active
-- ARGV: 1 document id.  Returns 1 deleted, 0 missing, -1 processing
local status = redis.call('HGET', KEYS[1], 'status')
if not status then
  return 0
end
if status == 'processing' then
  return -1
end
redis.call('DEL', KEYS[1], KEYS[2], KEYS[3])
for i = 4, 7 do
  redis.call('ZREM', KEYS[i], ARGV[1])
end
return 1
