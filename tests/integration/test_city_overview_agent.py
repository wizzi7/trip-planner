"""
Integration tests for CityOverviewAgent with mocked LLM.
Verifies that the agent correctly writes city overview data to WorldState
and records token usage.
"""
import pytest
from unittest.mock import patch
from backend.agents.city_overview import CityOverviewAgent
from backend.world_state import WorldState
from backend.event_bus import InMemoryEventBus
from backend.models import UserInput, CityOverview
from tests.conftest import FakeLLMProvider


def _make_input():
    return UserInput(
        destination="Warsaw, Poland",
        arrival="2024-07-10",
        departure="2024-07-12",
        guests=2,
        budget=500,
        pace="medium",
        transport=["metro", "bus"],
    )


FAKE_CITY_RESPONSE = {
    "city_name": "Warsaw",
    "short_description": "Capital of Poland, a vibrant city blending history and modernity.",
    "history_summary": "Warsaw has a rich history spanning over 700 years, from its medieval origins through devastating WWII destruction to remarkable post-war reconstruction.",
    "cultural_identity": "Warsaw pulses with creative energy — from its thriving art scene and jazz clubs to its café culture and innovative culinary landscape.",
}


@pytest.mark.asyncio
async def test_city_overview_writes_to_world():
    """Agent should write CityOverview to world.city_overview and record usage."""
    fake_llm = FakeLLMProvider(response_data=FAKE_CITY_RESPONSE)
    agent = CityOverviewAgent(llm_provider=fake_llm, model_name="fake-model")
    world = WorldState(_make_input())
    bus = InMemoryEventBus()

    await agent.run(world, bus)

    assert world.city_overview is not None
    assert isinstance(world.city_overview, CityOverview)
    assert world.city_overview.city_name == "Warsaw"
    assert "Capital" in world.city_overview.short_description
    assert "CityOverviewAgent" in world.token_usage


@pytest.mark.asyncio
async def test_city_overview_records_token_usage():
    """Token usage stats should contain expected keys."""
    fake_llm = FakeLLMProvider(response_data=FAKE_CITY_RESPONSE)
    agent = CityOverviewAgent(llm_provider=fake_llm, model_name="fake-model")
    world = WorldState(_make_input())
    bus = InMemoryEventBus()

    await agent.run(world, bus)

    usage = world.token_usage["CityOverviewAgent"]
    assert usage["input_tokens"] == 100
    assert usage["output_tokens"] == 200
    assert usage["cost"] == 0.001


@pytest.mark.asyncio
async def test_city_overview_llm_receives_destination():
    """The LLM should receive the destination in the user prompt."""
    fake_llm = FakeLLMProvider(response_data=FAKE_CITY_RESPONSE)
    agent = CityOverviewAgent(llm_provider=fake_llm, model_name="fake-model")
    world = WorldState(_make_input())
    bus = InMemoryEventBus()

    await agent.run(world, bus)

    assert len(fake_llm.calls) == 1
    assert "Warsaw" in fake_llm.calls[0]["user"]


@pytest.mark.asyncio
async def test_city_overview_none_response_uses_fallback():
    """When LLM returns None, agent should set a fallback CityOverview."""
    fake_llm = FakeLLMProvider(response_data=None)
    agent = CityOverviewAgent(llm_provider=fake_llm, model_name="fake-model")
    world = WorldState(_make_input())
    bus = InMemoryEventBus()

    await agent.run(world, bus)

    assert world.city_overview is not None
    assert "unavailable" in world.city_overview.short_description.lower()


@pytest.mark.asyncio
@patch.dict("os.environ", {"ENABLE_CITY_OVERVIEW": "false"})
async def test_city_overview_disabled_by_env():
    """When ENABLE_CITY_OVERVIEW=false, agent should skip and set None."""
    fake_llm = FakeLLMProvider(response_data=FAKE_CITY_RESPONSE)
    agent = CityOverviewAgent(llm_provider=fake_llm, model_name="fake-model")
    world = WorldState(_make_input())
    bus = InMemoryEventBus()

    await agent.run(world, bus)

    assert world.city_overview is None
    assert len(fake_llm.calls) == 0  # LLM should NOT be called
