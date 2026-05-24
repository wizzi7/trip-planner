"""
Integration tests for TransportationAgent with mocked LLM.
Verifies mobility section generation, WorldState updates, and event emission.
"""
import pytest
from unittest.mock import patch
from backend.agents.transport import TransportationAgent
from backend.world_state import WorldState
from backend.event_bus import InMemoryEventBus
from backend.models import UserInput, MobilitySection
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


FAKE_MOBILITY_RESPONSE = {
    "public_transport": {
        "available_options": ["Metro", "Bus", "Tram"],
        "ticket_types": "Single ticket (4.40 PLN), 24h pass (15 PLN), 72h pass (36 PLN)",
        "approximate_prices": "4.40-36 PLN depending on ticket type",
        "coverage_quality": "Excellent in central Warsaw, good in suburbs",
        "useful_apps": ["Jakdojade", "Google Maps", "mKomunikacja"],
        "best_use_cases": "Daily commuting and reaching major attractions",
        "price_level": "💸 Cheap",
        "website_url": "https://www.wtp.waw.pl",
    },
    "taxis": {
        "available_apps": ["Uber", "Bolt", "Free Now"],
        "typical_pricing_level": "💸💸 Moderate",
        "safety_notes": "Use only licensed apps, avoid unmarked cabs.",
        "when_to_use": "Late night returns or reaching outskirts",
    },
    "walking": {
        "is_walkable": True,
        "best_areas": ["Old Town", "Royal Route", "Łazienki Park"],
    },
    "bikes": {
        "available": True,
        "providers": ["Veturilo", "Lime"],
        "price_range": "First 20 min free with Veturilo, then 1-4 PLN/20min",
        "convenience": "Good bike lanes in city center",
        "cautions": ["Watch for tram tracks", "Lock bike securely"],
    },
    "ferries": {
        "is_relevant": True,
        "routes": "Vistula river crossings (summer only)",
        "cost_level": "Free (municipal ferries)",
        "tourist_vs_commuter": "Both — scenic and practical",
    },
    "car_rental": {
        "recommended": False,
        "parking_difficulty": "High in city center, limited zones",
        "notes": "Not recommended for city-only trips due to traffic and parking issues.",
    },
    "quick_recommendations": {
        "best_overall": "Metro + walking combination",
        "cheapest": "Walking + Veturilo (free first 20 min)",
        "most_convenient": "Uber/Bolt for door-to-door",
        "avoid": ["Unlicensed taxis", "Rush hour driving"],
    },
}


@pytest.mark.asyncio
async def test_transport_writes_mobility_section():
    """Agent should write MobilitySection to WorldState."""
    fake_llm = FakeLLMProvider(response_data=FAKE_MOBILITY_RESPONSE)
    agent = TransportationAgent(llm_provider=fake_llm, model_name="fake-model")
    world = WorldState(_make_input())
    world.constraints = {"transport_hints": ""}
    bus = InMemoryEventBus()
    await bus.emit("constraints_ready")

    await agent.run(world, bus)

    assert world.mobility_section is not None
    assert isinstance(world.mobility_section, MobilitySection)
    assert world.mobility_section.public_transport is not None
    assert "Metro" in world.mobility_section.public_transport.available_options


@pytest.mark.asyncio
async def test_transport_walking_info():
    """Walking section should reflect mock data."""
    fake_llm = FakeLLMProvider(response_data=FAKE_MOBILITY_RESPONSE)
    agent = TransportationAgent(llm_provider=fake_llm, model_name="fake-model")
    world = WorldState(_make_input())
    world.constraints = {"transport_hints": ""}
    bus = InMemoryEventBus()
    await bus.emit("constraints_ready")

    await agent.run(world, bus)

    assert world.mobility_section.walking.is_walkable is True
    assert "Old Town" in world.mobility_section.walking.best_areas


@pytest.mark.asyncio
async def test_transport_emits_cost_updated():
    """After completion, 'cost_updated' should be emitted."""
    fake_llm = FakeLLMProvider(response_data=FAKE_MOBILITY_RESPONSE)
    agent = TransportationAgent(llm_provider=fake_llm, model_name="fake-model")
    world = WorldState(_make_input())
    world.constraints = {"transport_hints": ""}
    bus = InMemoryEventBus()
    await bus.emit("constraints_ready")

    await agent.run(world, bus)

    result = await bus.subscribe_with_timeout("cost_updated", timeout=0.1)
    assert result is True


@pytest.mark.asyncio
async def test_transport_records_token_usage():
    """Token usage should be recorded under 'TransportationAgent'."""
    fake_llm = FakeLLMProvider(response_data=FAKE_MOBILITY_RESPONSE)
    agent = TransportationAgent(llm_provider=fake_llm, model_name="fake-model")
    world = WorldState(_make_input())
    world.constraints = {"transport_hints": ""}
    bus = InMemoryEventBus()
    await bus.emit("constraints_ready")

    await agent.run(world, bus)

    assert "TransportationAgent" in world.token_usage


@pytest.mark.asyncio
async def test_transport_passes_hints_to_prompt():
    """Transport hints from constraints should appear in the LLM prompt."""
    fake_llm = FakeLLMProvider(response_data=FAKE_MOBILITY_RESPONSE)
    agent = TransportationAgent(llm_provider=fake_llm, model_name="fake-model")
    world = WorldState(_make_input())
    world.constraints = {"transport_hints": "Prefer cycling over public transport"}
    bus = InMemoryEventBus()
    await bus.emit("constraints_ready")

    await agent.run(world, bus)

    user_prompt = fake_llm.calls[0]["user"]
    assert "Prefer cycling" in user_prompt


@pytest.mark.asyncio
async def test_transport_none_response_uses_empty_section():
    """When LLM returns None, agent should set an empty MobilitySection."""
    fake_llm = FakeLLMProvider(response_data=None)
    agent = TransportationAgent(llm_provider=fake_llm, model_name="fake-model")
    world = WorldState(_make_input())
    world.constraints = {"transport_hints": ""}
    bus = InMemoryEventBus()
    await bus.emit("constraints_ready")

    await agent.run(world, bus)

    assert world.mobility_section is not None
    assert world.mobility_section.public_transport is None


@pytest.mark.asyncio
@patch.dict("os.environ", {"ENABLE_TRANSPORT": "false"})
async def test_transport_disabled_by_env():
    """When disabled, agent should set empty MobilitySection and emit event."""
    fake_llm = FakeLLMProvider(response_data=FAKE_MOBILITY_RESPONSE)
    agent = TransportationAgent(llm_provider=fake_llm, model_name="fake-model")
    world = WorldState(_make_input())
    world.constraints = {}
    bus = InMemoryEventBus()
    await bus.emit("constraints_ready")

    await agent.run(world, bus)

    assert world.mobility_section is not None
    assert len(fake_llm.calls) == 0
