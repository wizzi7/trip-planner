"""
Integration tests for AttractionsAgent with mocked LLM.
Verifies itinerary generation, WorldState updates, event emission,
and edge cases with mock data.
"""
import pytest
from unittest.mock import patch
from backend.agents.attractions import AttractionsAgent
from backend.world_state import WorldState
from backend.event_bus import InMemoryEventBus
from backend.models import UserInput, TripDay
from tests.conftest import FakeLLMProvider


def _make_input(**overrides):
    defaults = dict(
        destination="Warsaw, Poland",
        arrival="2024-07-10",
        departure="2024-07-12",
        guests=2,
        budget=500,
        pace="medium",
        transport=["metro", "bus"],
    )
    defaults.update(overrides)
    return UserInput(**defaults)


FAKE_ATTRACTIONS_RESPONSE = [
    {
        "day": 1,
        "date": "2024-07-10",
        "theme": "Old Town Heritage",
        "summary": "Exploring Warsaw's reconstructed Old Town and Royal Route.",
        "activities": [
            {"name": "Royal Castle", "description": "Reconstructed baroque royal residence.", "duration": "1.5h"},
            {"name": "Old Town Market Square", "description": "Heart of the historic district.", "duration": "45 min"},
            {"name": "St. John's Cathedral", "description": "Oldest church in Warsaw.", "duration": "30 min"},
        ],
        "estimated_cost": "80 PLN",
    },
    {
        "day": 2,
        "date": "2024-07-11",
        "theme": "Modern Warsaw",
        "summary": "Contemporary culture and science.",
        "activities": [
            {"name": "Palace of Culture", "description": "Iconic Soviet-era skyscraper.", "duration": "1h"},
            {"name": "Copernicus Science Centre", "description": "Interactive science museum.", "duration": "2h"},
        ],
        "estimated_cost": "60 PLN",
    },
    {
        "day": 3,
        "date": "2024-07-12",
        "theme": "Parks & Nature",
        "summary": "Green spaces and relaxation.",
        "activities": [
            {"name": "Łazienki Park", "description": "Largest park in Warsaw.", "duration": "1.5h"},
        ],
        "estimated_cost": "0 PLN",
    },
]


@pytest.mark.asyncio
async def test_attractions_produces_days():
    """Agent should produce TripDay objects and write them to WorldState."""
    fake_llm = FakeLLMProvider(response_data=FAKE_ATTRACTIONS_RESPONSE)
    agent = AttractionsAgent(llm_provider=fake_llm, model_name="fake-model")
    world = WorldState(_make_input())
    world.constraints = {"interest_tags": [], "pace": "medium", "accessibility": "none"}
    bus = InMemoryEventBus()
    await bus.emit("constraints_ready")

    await agent.run(world, bus)

    assert world.days is not None
    assert len(world.days) == 3
    assert all(isinstance(d, TripDay) for d in world.days)


@pytest.mark.asyncio
async def test_attractions_day_themes():
    """Each day should have the theme from the mock response."""
    fake_llm = FakeLLMProvider(response_data=FAKE_ATTRACTIONS_RESPONSE)
    agent = AttractionsAgent(llm_provider=fake_llm, model_name="fake-model")
    world = WorldState(_make_input())
    world.constraints = {"interest_tags": [], "pace": "medium", "accessibility": "none"}
    bus = InMemoryEventBus()
    await bus.emit("constraints_ready")

    await agent.run(world, bus)

    themes = [d.theme for d in world.days]
    assert "Old Town Heritage" in themes
    assert "Modern Warsaw" in themes
    assert "Parks & Nature" in themes


@pytest.mark.asyncio
async def test_attractions_emits_days_planned():
    """After completion, 'days_planned' event should be emitted."""
    fake_llm = FakeLLMProvider(response_data=FAKE_ATTRACTIONS_RESPONSE)
    agent = AttractionsAgent(llm_provider=fake_llm, model_name="fake-model")
    world = WorldState(_make_input())
    world.constraints = {"interest_tags": [], "pace": "medium", "accessibility": "none"}
    bus = InMemoryEventBus()
    await bus.emit("constraints_ready")

    await agent.run(world, bus)

    # days_planned should be set - subscribing should not block
    result = await bus.subscribe_with_timeout("days_planned", timeout=0.1)
    assert result is True


@pytest.mark.asyncio
async def test_attractions_emits_cost_updated():
    """After completion, 'cost_updated' event should be emitted."""
    fake_llm = FakeLLMProvider(response_data=FAKE_ATTRACTIONS_RESPONSE)
    agent = AttractionsAgent(llm_provider=fake_llm, model_name="fake-model")
    world = WorldState(_make_input())
    world.constraints = {"interest_tags": [], "pace": "medium", "accessibility": "none"}
    bus = InMemoryEventBus()
    await bus.emit("constraints_ready")

    await agent.run(world, bus)

    result = await bus.subscribe_with_timeout("cost_updated", timeout=0.1)
    assert result is True


@pytest.mark.asyncio
async def test_attractions_records_token_usage():
    """Token usage should be recorded under 'AttractionsAgent'."""
    fake_llm = FakeLLMProvider(response_data=FAKE_ATTRACTIONS_RESPONSE)
    agent = AttractionsAgent(llm_provider=fake_llm, model_name="fake-model")
    world = WorldState(_make_input())
    world.constraints = {"interest_tags": [], "pace": "medium", "accessibility": "none"}
    bus = InMemoryEventBus()
    await bus.emit("constraints_ready")

    await agent.run(world, bus)

    assert "AttractionsAgent" in world.token_usage
    assert world.token_usage["AttractionsAgent"]["total_tokens"] == 300


@pytest.mark.asyncio
async def test_attractions_passes_constraints_to_prompt():
    """Constraints like interests and pace should appear in the LLM prompt."""
    fake_llm = FakeLLMProvider(response_data=FAKE_ATTRACTIONS_RESPONSE)
    agent = AttractionsAgent(llm_provider=fake_llm, model_name="fake-model")
    world = WorldState(_make_input())
    world.constraints = {
        "interest_tags": ["history", "art"],
        "pace": "slow",
        "accessibility": "wheelchair_accessible",
        "attractions_hints": "Focus on museums",
    }
    bus = InMemoryEventBus()
    await bus.emit("constraints_ready")

    await agent.run(world, bus)

    user_prompt = fake_llm.calls[0]["user"]
    assert "history" in user_prompt
    assert "art" in user_prompt
    assert "slow" in user_prompt
    assert "wheelchair_accessible" in user_prompt
    assert "Focus on museums" in user_prompt


@pytest.mark.asyncio
async def test_attractions_none_response_returns_empty():
    """When LLM returns None, days should be an empty list (fallback)."""
    fake_llm = FakeLLMProvider(response_data=None)
    agent = AttractionsAgent(llm_provider=fake_llm, model_name="fake-model")
    world = WorldState(_make_input())
    world.constraints = {"interest_tags": [], "pace": "medium", "accessibility": "none"}
    bus = InMemoryEventBus()
    await bus.emit("constraints_ready")

    await agent.run(world, bus)

    assert world.days == []


@pytest.mark.asyncio
@patch.dict("os.environ", {"ENABLE_ATTRACTIONS": "false"})
async def test_attractions_disabled_by_env():
    """When disabled by env, agent should set empty days and emit events."""
    fake_llm = FakeLLMProvider(response_data=FAKE_ATTRACTIONS_RESPONSE)
    agent = AttractionsAgent(llm_provider=fake_llm, model_name="fake-model")
    world = WorldState(_make_input())
    world.constraints = {}
    bus = InMemoryEventBus()
    await bus.emit("constraints_ready")

    await agent.run(world, bus)

    assert world.days == []
    assert len(fake_llm.calls) == 0
    result = await bus.subscribe_with_timeout("days_planned", timeout=0.1)
    assert result is True
