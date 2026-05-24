"""
Integration tests for GastronomyAgent with mocked LLM.
Verifies culinary section generation, normalization logic, WorldState writing,
and event emission.
"""
import pytest
from unittest.mock import patch
from backend.agents.gastronomy import GastronomyAgent
from backend.world_state import WorldState
from backend.event_bus import InMemoryEventBus
from backend.models import UserInput, CulinarySection
from tests.conftest import FakeLLMProvider


def _make_input(**overrides):
    defaults = dict(
        destination="Warsaw, Poland",
        arrival="2024-07-10",
        departure="2024-07-12",
        guests=2,
        budget=500,
        pace="medium",
        transport=["metro"],
    )
    defaults.update(overrides)
    return UserInput(**defaults)


FAKE_CULINARY_RESPONSE = {
    "main_dishes": [
        {"name": "Pierogi", "description": "Traditional Polish dumplings.", "price_range": "15-25 PLN"},
        {"name": "Bigos", "description": "Hunter's stew with sauerkraut.", "price_range": "20-30 PLN"},
        {"name": "Schabowy", "description": "Breaded pork cutlet.", "price_range": "25-35 PLN"},
        {"name": "Gołąbki", "description": "Cabbage rolls with meat.", "price_range": "18-28 PLN"},
        {"name": "Placki ziemniaczane", "description": "Potato pancakes.", "price_range": "12-20 PLN"},
        {"name": "Żurek w chlebku", "description": "Sour rye soup in bread bowl.", "price_range": "15-22 PLN"},
    ],
    "soups": [
        {"name": "Żurek", "description": "Sour rye soup with egg and sausage.", "price_range": "10-18 PLN"},
        {"name": "Barszcz czerwony", "description": "Beetroot soup, clear or with uszka.", "price_range": "8-15 PLN"},
    ],
    "desserts": [
        {"name": "Sernik", "description": "Polish cheesecake.", "price_range": "10-18 PLN"},
        {"name": "Pączki", "description": "Filled doughnuts.", "price_range": "5-10 PLN"},
    ],
    "drinks": [
        {"name": "Vodka", "description": "Poland's national spirit.", "price_range": "8-20 PLN"},
        {"name": "Local Beer", "description": "Polish craft and lager beers.", "price_range": "8-15 PLN"},
    ],
    "venues_traditional": [
        {"name": "Zapiecek", "district": "Old Town", "type": "Traditional Polish", "price_range": "30-60 PLN", "signature_items": "Pierogi, Bigos"},
        {"name": "U Fukiera", "district": "Old Town", "type": "Fine Dining Polish", "price_range": "80-150 PLN", "signature_items": "Duck, Venison"},
        {"name": "Gospoda Koko", "district": "Praga", "type": "Traditional", "price_range": "25-45 PLN", "signature_items": "Schabowy, Żurek"},
        {"name": "Bar Mleczny Prasowy", "district": "City Center", "type": "Milk Bar", "price_range": "10-20 PLN", "signature_items": "Pierogi, Naleśniki"},
    ],
    "venues_cafes": [
        {"name": "Café Bristol", "district": "Krakowskie Przedmieście", "type": "Café", "price_range": "20-40 PLN", "signature_items": "Coffee, Sernik"},
        {"name": "Relax Café", "district": "Mokotów", "type": "Café", "price_range": "15-30 PLN", "signature_items": "Latte, Pastries"},
        {"name": "Green Caffè Nero", "district": "Various", "type": "Chain Café", "price_range": "12-25 PLN", "signature_items": "Espresso, Muffins"},
        {"name": "Charlotte", "district": "Plac Zbawiciela", "type": "French-Polish Café", "price_range": "20-40 PLN", "signature_items": "Croissants, Tarts"},
    ],
    "venues_bars": [
        {"name": "Piw Paw", "district": "City Center", "type": "Craft Beer", "price_range": "12-25 PLN", "signature_items": "Polish Craft IPA"},
        {"name": "Kufle i Kapsle", "district": "Żoliborz", "type": "Craft Beer", "price_range": "10-22 PLN", "signature_items": "Rotating taps"},
        {"name": "Bubbles Bar", "district": "Nowy Świat", "type": "Cocktail Bar", "price_range": "25-45 PLN", "signature_items": "Champagne cocktails"},
        {"name": "Plan B", "district": "Plac Zbawiciela", "type": "Dive Bar", "price_range": "8-18 PLN", "signature_items": "Beer, Vodka shots"},
    ],
}


@pytest.mark.asyncio
async def test_gastronomy_writes_culinary_section():
    """Agent should write CulinarySection to world.culinary_section."""
    fake_llm = FakeLLMProvider(response_data=FAKE_CULINARY_RESPONSE)
    agent = GastronomyAgent(llm_provider=fake_llm, model_name="fake-model")
    world = WorldState(_make_input())
    world.constraints = {"dietary_restrictions": [], "gastronomy_hints": ""}
    bus = InMemoryEventBus()
    await bus.emit("constraints_ready")

    await agent.run(world, bus)

    assert world.culinary_section is not None
    assert isinstance(world.culinary_section, CulinarySection)
    assert len(world.culinary_section.main_dishes) >= 6
    assert len(world.culinary_section.venues_traditional) >= 4


@pytest.mark.asyncio
async def test_gastronomy_emits_cost_updated():
    """After completion, 'cost_updated' should be emitted."""
    fake_llm = FakeLLMProvider(response_data=FAKE_CULINARY_RESPONSE)
    agent = GastronomyAgent(llm_provider=fake_llm, model_name="fake-model")
    world = WorldState(_make_input())
    world.constraints = {"dietary_restrictions": [], "gastronomy_hints": ""}
    bus = InMemoryEventBus()
    await bus.emit("constraints_ready")

    await agent.run(world, bus)

    result = await bus.subscribe_with_timeout("cost_updated", timeout=0.1)
    assert result is True


@pytest.mark.asyncio
async def test_gastronomy_records_token_usage():
    """Token usage should be recorded under 'GastronomyAgent'."""
    fake_llm = FakeLLMProvider(response_data=FAKE_CULINARY_RESPONSE)
    agent = GastronomyAgent(llm_provider=fake_llm, model_name="fake-model")
    world = WorldState(_make_input())
    world.constraints = {"dietary_restrictions": [], "gastronomy_hints": ""}
    bus = InMemoryEventBus()
    await bus.emit("constraints_ready")

    await agent.run(world, bus)

    assert "GastronomyAgent" in world.token_usage


@pytest.mark.asyncio
async def test_gastronomy_none_response_uses_empty_section():
    """When LLM returns None, agent should set empty CulinarySection."""
    fake_llm = FakeLLMProvider(response_data=None)
    agent = GastronomyAgent(llm_provider=fake_llm, model_name="fake-model")
    world = WorldState(_make_input())
    world.constraints = {"dietary_restrictions": [], "gastronomy_hints": ""}
    bus = InMemoryEventBus()
    await bus.emit("constraints_ready")

    await agent.run(world, bus)

    assert world.culinary_section is not None
    assert world.culinary_section.main_dishes == []


@pytest.mark.asyncio
async def test_gastronomy_passes_dietary_restrictions():
    """Dietary restrictions should appear in the LLM prompt."""
    fake_llm = FakeLLMProvider(response_data=FAKE_CULINARY_RESPONSE)
    agent = GastronomyAgent(llm_provider=fake_llm, model_name="fake-model")
    world = WorldState(_make_input())
    world.constraints = {"dietary_restrictions": ["vegan", "gluten-free"], "gastronomy_hints": "No pork"}
    bus = InMemoryEventBus()
    await bus.emit("constraints_ready")

    await agent.run(world, bus)

    user_prompt = fake_llm.calls[0]["user"]
    assert "vegan" in user_prompt
    assert "gluten-free" in user_prompt
    assert "No pork" in user_prompt


@pytest.mark.asyncio
@patch.dict("os.environ", {"ENABLE_GASTRONOMY": "false"})
async def test_gastronomy_disabled_by_env():
    """When disabled, agent should set empty CulinarySection and emit event."""
    fake_llm = FakeLLMProvider(response_data=FAKE_CULINARY_RESPONSE)
    agent = GastronomyAgent(llm_provider=fake_llm, model_name="fake-model")
    world = WorldState(_make_input())
    world.constraints = {}
    bus = InMemoryEventBus()
    await bus.emit("constraints_ready")

    await agent.run(world, bus)

    assert world.culinary_section is not None
    assert world.culinary_section.main_dishes == []
    assert len(fake_llm.calls) == 0
