-- Sliding-window limit on a sorted set of hit timestamps (door 8).
-- KEYS: 1 window key   ARGV: 1 now ms, 2 window ms, 3 limit, 4 unique member
-- Returns {1, 0} when the hit is counted, {0, retry_after_ms} when it is not.
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', now - window)
if redis.call('ZCARD', KEYS[1]) < tonumber(ARGV[3]) then
  redis.call('ZADD', KEYS[1], now, ARGV[4])
  redis.call('PEXPIRE', KEYS[1], window)
  return {1, 0}
end
local oldest = redis.call('ZRANGE', KEYS[1], 0, 0, 'WITHSCORES')
return {0, tonumber(oldest[2]) + window - now}
