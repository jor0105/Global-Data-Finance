from importlib import import_module
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from globaldatafinance.brazil.b3_data.historical_quotes import (
    ProcessingModeEnumB3,
)
from globaldatafinance.core import ResourceState
from tests.brazil.b3_data.historical_quotes.conftest import FakeResourceMonitor

resource_policy_module = import_module(
    'globaldatafinance.brazil.b3_data.historical_quotes.extraction_service.resource_policy'
)
ResourcePolicyB3 = resource_policy_module.ResourcePolicyB3

pytestmark = pytest.mark.unit


def _policy(
    monkeypatch,
    monitor: FakeResourceMonitor,
    mode: ProcessingModeEnumB3 = ProcessingModeEnumB3.FAST,
) -> Any:
    monkeypatch.setattr(
        'globaldatafinance.brazil.b3_data.historical_quotes.extraction_service.resource_policy.ResourceMonitor',
        lambda: monitor,
    )
    return ResourcePolicyB3(mode)


@pytest.mark.asyncio
async def test_critical_resources_force_gc_after_short_wait(monkeypatch):
    monitor = FakeResourceMonitor(states=[ResourceState.CRITICAL])
    policy = _policy(monkeypatch, monitor)

    with (
        patch(
            'globaldatafinance.brazil.b3_data.historical_quotes.extraction_service.resource_policy.asyncio.sleep',
            new_callable=AsyncMock,
        ) as sleep,
        patch(
            'globaldatafinance.brazil.b3_data.historical_quotes.extraction_service.resource_policy.gc.collect'
        ) as collect,
    ):
        await policy.check_and_wait_for_resources()

    sleep.assert_awaited_once_with(0.1)
    collect.assert_called_once_with()


@pytest.mark.asyncio
@pytest.mark.parametrize('recovered', [True, False])
async def test_exhausted_resources_recovery_contract(monkeypatch, recovered):
    monitor = FakeResourceMonitor(states=[ResourceState.EXHAUSTED])
    policy = _policy(monkeypatch, monitor)
    monkeypatch.setattr(
        policy,
        'wait_for_resources',
        AsyncMock(return_value=recovered),
    )

    if recovered:
        await policy.check_and_wait_for_resources()
    else:
        with pytest.raises(MemoryError, match='Unable to recover'):
            await policy.check_and_wait_for_resources()

    policy.wait_for_resources.assert_awaited_once_with(timeout_seconds=30)


@pytest.mark.asyncio
async def test_wait_for_resources_returns_after_healthy_state(monkeypatch):
    monitor = FakeResourceMonitor(
        states=[ResourceState.CRITICAL, ResourceState.HEALTHY]
    )
    policy = _policy(monkeypatch, monitor)
    monotonic_values = iter([0.0, 0.0, 1.0])

    with (
        patch(
            'globaldatafinance.brazil.b3_data.historical_quotes.extraction_service.resource_policy.time.monotonic',
            side_effect=lambda: next(monotonic_values),
        ),
        patch(
            'globaldatafinance.brazil.b3_data.historical_quotes.extraction_service.resource_policy.asyncio.sleep',
            new_callable=AsyncMock,
        ) as sleep,
    ):
        result = await policy.wait_for_resources(timeout_seconds=5)

    assert result is True
    sleep.assert_awaited_once_with(1)
    assert monitor.check_calls == 2


@pytest.mark.asyncio
async def test_wait_for_resources_returns_false_at_patched_deadline(
    monkeypatch,
):
    monitor = FakeResourceMonitor(states=[ResourceState.CRITICAL])
    policy = _policy(monkeypatch, monitor)
    monotonic_values = iter([0.0, 0.0, 1.0, 2.0])

    with (
        patch(
            'globaldatafinance.brazil.b3_data.historical_quotes.extraction_service.resource_policy.time.monotonic',
            side_effect=lambda: next(monotonic_values),
        ),
        patch(
            'globaldatafinance.brazil.b3_data.historical_quotes.extraction_service.resource_policy.asyncio.sleep',
            new_callable=AsyncMock,
        ) as sleep,
    ):
        result = await policy.wait_for_resources(timeout_seconds=2)

    assert result is False
    assert sleep.await_count == 2
    assert monitor.check_calls == 2


def test_adjust_batch_sizes_clamps_flush_and_parse_minimums(monkeypatch):
    monitor = FakeResourceMonitor(
        safe_batch_size=1, states=[ResourceState.HEALTHY]
    )
    policy = _policy(monkeypatch, monitor)

    policy.adjust_batch_sizes()

    assert policy.flush_batch_size == policy.MIN_FLUSH_BATCH
    assert policy.parse_batch_size == policy.MIN_PARSE_BATCH
    assert monitor.batch_calls == [policy.FLUSH_BATCH_SIZE]


@pytest.mark.parametrize('memory_mb, expected', [(999, False), (1000, True)])
def test_memory_flush_threshold_includes_both_sides(
    monkeypatch, memory_mb, expected
):
    monitor = FakeResourceMonitor(process_memory_mb=memory_mb)
    policy = _policy(monkeypatch, monitor, ProcessingModeEnumB3.SLOW)

    assert policy.should_flush_by_memory() is expected
