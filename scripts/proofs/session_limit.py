"""Criterion 17 through nginx: a client-written X-Forwarded-For never picks the rate-limit key.

Creates as many sessions from this machine as the per-IP limit allows (20, or the stack's
``SESSIONS_PER_MINUTE_PER_IP``), each with a new first hop, plus one: the last must be 429. Then
one more with a first hop never used before: it must still be 429. Then waits for the 60 s window to
pass, so the proofs that run next can open sessions again. Prints only statuses.

    python3 scripts/proofs/session_limit.py http://localhost:8081 [limit]
"""

import sys
import time
import urllib.error
import urllib.request

DEFAULT_LIMIT = 20
WINDOW_S = 60


def new_session(base: str, forwarded_for: str) -> int:
    """POST /api/v1/sessions with no cookie and the given X-Forwarded-For; return the status."""
    request = urllib.request.Request(  # noqa: S310 - the base is the local e2e stack
        f"{base}/api/v1/sessions", method="POST", headers={"X-Forwarded-For": forwarded_for}
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:  # noqa: S310
            return int(response.status)
    except urllib.error.HTTPError as error:
        return int(error.code)


def main() -> int:
    """Run the proof and print the verdict."""
    base = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8081"
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_LIMIT
    hops = [f"10.{n // 65536}.{n // 256 % 256}.{n % 256}" for n in range(limit + 1)]
    statuses = [new_session(base, hop) for hop in hops]
    counts = {status: statuses.count(status) for status in sorted(set(statuses))}
    sys.stdout.write(f"limit {limit}; {len(statuses)} sessions, a new first hop each: {counts}\n")
    sys.stdout.write(f"the last of them: {statuses[-1]}\n")
    spoofed = new_session(base, "198.51.100.77")
    sys.stdout.write(f"one more with an unused first hop: {spoofed}\n")

    deadline = time.monotonic() + WINDOW_S + 15
    while time.monotonic() < deadline and new_session(base, "192.0.2.1") == 429:
        time.sleep(2)

    passed = statuses[-1] == 429 and spoofed == 429
    sys.stdout.write(f"result: {'PASSED' if passed else 'FAILED'}\n")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
