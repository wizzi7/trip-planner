"""
Integration tests for PreferencesAgent with mocked LLM.
Verifies constraint extraction, WorldState writing, event emission,
rule-based fallback, and env disable.
"""
import pytest
from unittest.mock import patch
from backend.agents.preferences import PreferencesAgent
from backend.world_state import WorldState
from backend.event_bus import InMemoryEventBus
from backend.models import UserInput
from tests.conftest import FakeLLMProvider


def _make_input(**overrides):
    defaults = dict(
        destination="Rome, Italy",
        arrival="2024-08-01",
        departure="2024-08-04",
        guests=2,
        budget=600,
        pace="slow",
        transport=["metro"],
    )
    defaults.update(overrides)
    return UserInput(**defaults)


FAKE_PREFERENCES_RESPONSE = {
    "dietary_restrictions": ["vegetarian"],
    "accessibility": "none",
    "attractions_hints": "Focus on ancient ruins and Renaissance art galleries.",
    "gastronomy_hints": "Prefer trattorias with vegetarian pasta options.",
    "transport_hints": "Prefer walking and metro for short distances.",
    "general_notes": "The travelers enjoy quiet, less crowded areas.",
}


@pytest.mark.asyncio
async def test_preferences_writes_constraints():
    """Agent should write parsed constraints to WorldState."""
    fake_llm = FakeLLMProvider(response_data=FAKE_PREFERENCES_RESPONSE)
    agent = PreferencesAgent(llm_provider=fake_llm, model_name="fake-model")
    world = WorldState(_make_input(extra_req="I'm vegetarian and love ancient ruins"))
    bus = InMemoryEventBus()

    await agent.run(world, bus)

    assert world.constraints is not None
    assert world.constraints["dietary_restrictions"] == ["vegetarian"]
    assert world.constraints["accessibility"] == "none"
    assert "ancient ruins" in world.constraints["attractions_hints"]
    assert "vegetarian" in world.constraints["gastronomy_hints"]


@pytest.mark.asyncio
async def test_preferences_emits_constraints_ready():
    """After completion, 'constraints_ready' event should be emitted."""
    fake_llm = FakeLLMProvider(response_data=FAKE_PREFERENCES_RESPONSE)
    agent = PreferencesAgent(llm_provider=fake_llm, model_name="fake-model")
    world = WorldState(_make_input(extra_req="I like museums"))
    bus = InMemoryEventBus()

    await agent.run(world, bus)

    result = await bus.subscribe_with_timeout("constraints_ready", timeout=0.1)
    assert result is True


@pytest.mark.asyncio
async def test_preferences_records_token_usage():
    """Token usage should be recorded for LLM-based parsing."""
    fake_llm = FakeLLMProvider(response_data=FAKE_PREFERENCES_RESPONSE)
    agent = PreferencesAgent(llm_provider=fake_llm, model_name="fake-model")
    world = WorldState(_make_input(extra_req="I need wheelchair access"))
    bus = InMemoryEventBus()

    await agent.run(world, bus)

    assert "PreferencesAgent" in world.token_usage
    assert world.token_usage["PreferencesAgent"]["total_tokens"] == 300


@pytest.mark.asyncio
async def test_preferences_no_extra_req_skips_llm():
    """Without extra_req, agent should not call LLM and use empty defaults."""
    fake_llm = FakeLLMProvider(response_data=FAKE_PREFERENCES_RESPONSE)
    agent = PreferencesAgent(llm_provider=fake_llm, model_name="fake-model")
    world = WorldState(_make_input())
    bus = InMemoryEventBus()

    await agent.run(world, bus)

    assert len(fake_llm.calls) == 0
    assert world.constraints["dietary_restrictions"] == []
    assert world.constraints["accessibility"] == "none"
    assert world.constraints["attractions_hints"] == ""


@pytest.mark.asyncio
async def test_preferences_llm_returns_none_falls_back():
    """When LLM returns None, agent should fall back to rule-based parsing."""
    fake_llm = FakeLLMProvider(response_data=None)
    agent = PreferencesAgent(llm_provider=fake_llm, model_name="fake-model")
    world = WorldState(_make_input(extra_req="I'm vegan and need wheelchair access"))
    bus = InMemoryEventBus()

    await agent.run(world, bus)

    # Rule-based parser should detect keywords
    assert "vegan" in world.constraints["dietary_restrictions"]
    assert world.constraints["accessibility"] == "wheelchair_accessible"


@pytest.mark.asyncio
async def test_preferences_includes_interests_in_constraints():
    """User interests should appear in the final constraints."""
    fake_llm = FakeLLMProvider(response_data=FAKE_PREFERENCES_RESPONSE)
    agent = PreferencesAgent(llm_provider=fake_llm, model_name="fake-model")
    world = WorldState(_make_input(
        interests=["history", "food"],
        extra_req="I love history",
    ))
    bus = InMemoryEventBus()

    await agent.run(world, bus)

    assert "history" in world.constraints["interest_tags"]
    assert "food" in world.constraints["interest_tags"]


@pytest.mark.asyncio
@patch.dict("os.environ", {"ENABLE_PREFERENCES": "false"})
async def test_preferences_disabled_by_env():
    """When disabled, agent should emit constraints_ready with empty constraints."""
    fake_llm = FakeLLMProvider(response_data=FAKE_PREFERENCES_RESPONSE)
    agent = PreferencesAgent(llm_provider=fake_llm, model_name="fake-model")
    world = WorldState(_make_input(extra_req="anything"))
    bus = InMemoryEventBus()

    await agent.run(world, bus)

    assert world.constraints == {}
    assert len(fake_llm.calls) == 0
    result = await bus.subscribe_with_timeout("constraints_ready", timeout=0.1)
    assert result is True
