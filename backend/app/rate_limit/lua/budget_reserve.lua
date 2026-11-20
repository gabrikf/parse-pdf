-- Count model pages if the day's total stays within the cap (AD-013).
-- KEYS: 1 day counter   ARGV: 1 pages, 2 cap, 3 ttl s.  Returns 1 counted, 0 refused.
local used = tonumber(redis.call('GET', KEYS[1]) or '0')
if used + tonumber(ARGV[1]) > tonumber(ARGV[2]) then
  return 0
end
redis.call('INCRBY', KEYS[1], ARGV[1])
redis.call('EXPIRE', KEYS[1], ARGV[3])
return 1
