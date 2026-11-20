"""Criterion 32: backoff, Retry-After, and 6 attempts before the job is left pending."""

import pytest

from app.documents.domain.job_errors import TransientFailure
from app.models.retry_policy import RetryableError, RetryPolicy


def _policy(sleeps: list[float]) -> RetryPolicy:
    async def sleep(seconds: float) -> None:
        sleeps.append(seconds)

    return RetryPolicy(sleep=sleep, jitter=lambda low, high: high)


async def test_delays_double_from_1s_and_cap_at_60s() -> None:
    policy = _policy([])

    assert [policy.delay(attempt, None) for attempt in range(8)] == [1, 2, 4, 8, 16, 32, 60, 60]


async def test_full_jitter_draws_between_zero_and_the_backoff() -> None:
    drawn: list[tuple[float, float]] = []

    def jitter(low: float, high: float) -> float:
        drawn.append((low, high))
        return 0.0

    policy = RetryPolicy(jitter=jitter)

    assert policy.delay(3, None) == 0.0
    assert drawn == [(0, 8)]


async def test_retry_after_is_a_floor() -> None:
    policy = RetryPolicy(jitter=lambda low, high: 0.0)

    assert policy.delay(0, 7.0) == 7.0


async def test_retry_after_is_capped_like_the_backoff() -> None:
    policy = RetryPolicy(jitter=lambda low, high: 0.0)

    assert policy.delay(0, 3600.0) == 60.0


async def test_success_after_two_failures_makes_three_calls() -> None:
    sleeps: list[float] = []
    calls = 0

    async def flaky() -> str:
        nonlocal calls
        calls += 1
        if calls < 3:
            raise RetryableError("429")
        return "ok"

    assert await _policy(sleeps).run(flaky) == "ok"
    assert calls == 3
    assert sleeps == [1, 2]


async def test_six_failures_raise_transient_failure() -> None:
    sleeps: list[float] = []
    calls = 0

    async def always_429() -> str:
        nonlocal calls
        calls += 1
        raise RetryableError("429", retry_after_s=None)

    with pytest.raises(TransientFailure):
        await _policy(sleeps).run(always_429)
    assert calls == 6
    assert len(sleeps) == 5
