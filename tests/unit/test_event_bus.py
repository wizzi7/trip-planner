import pytest
import asyncio
from backend.event_bus import InMemoryEventBus


class TestEventBusEmitSubscribe:
    @pytest.mark.asyncio
    async def test_subscribe_after_emit_returns_immediately(self):
        bus = InMemoryEventBus()
        await bus.emit("ready")
        await bus.subscribe("ready")

    @pytest.mark.asyncio
    async def test_subscribe_blocks_until_emit(self):
        bus = InMemoryEventBus()
        result = []

        async def waiter():
            await bus.subscribe("go")
            result.append("done")

        task = asyncio.create_task(waiter())
        await asyncio.sleep(0.05)
        assert result == []

        await bus.emit("go")
        await task
        assert result == ["done"]

    @pytest.mark.asyncio
    async def test_multiple_subscribers_unblock(self):
        bus = InMemoryEventBus()
        results = []

        async def waiter(label):
            await bus.subscribe("start")
            results.append(label)

        tasks = [asyncio.create_task(waiter(f"w{i}")) for i in range(3)]
        await asyncio.sleep(0.05)
        assert results == []

        await bus.emit("start")
        await asyncio.gather(*tasks)
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_independent_events(self):
        bus = InMemoryEventBus()
        await bus.emit("event_a")
        ok = await bus.subscribe_with_timeout("event_b", timeout=0.1)
        assert ok is False


class TestEventBusTimeout:
    @pytest.mark.asyncio
    async def test_timeout_expires(self):
        bus = InMemoryEventBus()
        ok = await bus.subscribe_with_timeout("never_emitted", timeout=0.1)
        assert ok is False

    @pytest.mark.asyncio
    async def test_timeout_succeeds_when_already_set(self):
        bus = InMemoryEventBus()
        await bus.emit("fast")
        ok = await bus.subscribe_with_timeout("fast", timeout=1.0)
        assert ok is True

    @pytest.mark.asyncio
    async def test_timeout_succeeds_when_emitted_during_wait(self):
        bus = InMemoryEventBus()

        async def delayed_emit():
            await asyncio.sleep(0.05)
            await bus.emit("delayed")

        asyncio.create_task(delayed_emit())
        ok = await bus.subscribe_with_timeout("delayed", timeout=2.0)
        assert ok is True


class TestEventBusClear:
    @pytest.mark.asyncio
    async def test_clear_resets_event(self):
        bus = InMemoryEventBus()
        await bus.emit("ev")
        await bus.clear("ev")
        ok = await bus.subscribe_with_timeout("ev", timeout=0.1)
        assert ok is False

    @pytest.mark.asyncio
    async def test_clear_then_re_emit(self):
        bus = InMemoryEventBus()
        await bus.emit("ev")
        await bus.clear("ev")
        await bus.emit("ev")
        await bus.subscribe("ev")

    @pytest.mark.asyncio
    async def test_clear_nonexistent_event(self):
        bus = InMemoryEventBus()
        await bus.clear("nonexistent")


class TestEventBusIsolation:
    @pytest.mark.asyncio
    async def test_separate_bus_instances_are_independent(self):
        bus1 = InMemoryEventBus()
        bus2 = InMemoryEventBus()
        await bus1.emit("shared_name")
        ok = await bus2.subscribe_with_timeout("shared_name", timeout=0.1)
        assert ok is False
