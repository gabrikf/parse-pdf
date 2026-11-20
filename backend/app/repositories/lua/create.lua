-- Create a document record, index it in its session's feed and, when asked, queue it.
-- One script, so a record is never visible without its stream entry or the reverse (door 1).
-- KEYS: 1 doc hash, 2 session feed (all), 3 session feed group, 4 stream
-- ARGV: 1 ttl, 2 score, 3 document id, 4 enqueue (1/0), 5 object key, 6 run id, 7.. field/value
if redis.call('EXISTS', KEYS[1]) == 1 then
  return 0
end

local fields = {}
for i = 7, #ARGV do
  fields[#fields + 1] = ARGV[i]
end
redis.call('HSET', KEYS[1], unpack(fields))

for i = 2, 3 do
  redis.call('ZADD', KEYS[i], ARGV[2], ARGV[3])
end
for i = 1, 3 do
  redis.call('EXPIRE', KEYS[i], ARGV[1])
end

if ARGV[4] == '1' then
  redis.call('XADD', KEYS[4], '*', 'document_id', ARGV[3], 'object_key', ARGV[5], 'run_id', ARGV[6])
end
return 1
