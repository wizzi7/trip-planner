"""
Integration tests for BudgetAgent with mocked LLM.
Verifies cost estimation, budget alerts (over/under), WorldState updates,
and the agent's wait-for-dependencies loop.
"""
import pytest
from unittest.mock import patch
from backend.agents.budget import BudgetAgent
from backend.world_state import WorldState
from backend.event_bus import InMemoryEventBus
from backend.models import (
    UserInput, TripDay, Activity, CulinarySection,
    CulinaryDish, CulinaryVenue, MobilitySection,
    MobilitySystem, RideHailing, WalkingGuide, BikeScooter,
    FerryBoat, CarRental, QuickRecommendations,
)
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


def _make_days():
    return [
        TripDay(
            day=1, date="2024-07-10", theme="Old Town",
            summary="Historic exploration",
            activities=[
                Activity(name="Royal Castle", description="Royal residence.", duration="1.5h"),
                Activity(name="Old Town Square", description="Historic market.", duration="1h"),
            ],
            estimated_cost="80 PLN",
        ),
        TripDay(
            day=2, date="2024-07-11", theme="Modern",
            summary="Modern Warsaw",
            activities=[
                Activity(name="Science Centre", description="Interactive museum.", duration="2h"),
            ],
            estimated_cost="40 PLN",
        ),
    ]


def _make_culinary():
    return CulinarySection(
        main_dishes=[CulinaryDish(name="Pierogi", description="Dumplings", price_range="15-25 PLN")],
        venues_traditional=[CulinaryVenue(name="Zapiecek", price_range="30-60 PLN", district="Old Town")],
    )


def _make_mobility():
    return MobilitySection(
        public_transport=MobilitySystem(
            available_options=["Metro", "Bus"],
            ticket_types="Single ticket (4.40 PLN)",
            approximate_prices="4.40-15 PLN",
            coverage_quality="Good",
            useful_apps=["Jakdojade"],
            best_use_cases="Daily transport",
            price_level="💸 Cheap",
        ),
        taxis=RideHailing(
            available_apps=["Uber", "Bolt"],
            typical_pricing_level="💸💸 Moderate",
            safety_notes="Use licensed apps.",
            when_to_use="Late night",
        ),
        walking=WalkingGuide(is_walkable=True, best_areas=["Old Town"]),
        bikes=BikeScooter(
            available=True, providers=["Veturilo"],
            price_range="Free first 20 min", convenience="Good",
            cautions=["Watch tram tracks"],
        ),
        ferries=FerryBoat(is_relevant=False),
        car_rental=CarRental(recommended=False, parking_difficulty="High", notes="Not recommended."),
        quick_recommendations=QuickRecommendations(
            best_overall="Metro", cheapest="Walking",
            most_convenient="Uber", avoid=["Rush hour"],
        ),
    )


FAKE_BUDGET_WITHIN = {
    "daily_costs": [
        {"day": 1, "cost": "200 PLN"},
        {"day": 2, "cost": "180 PLN"},
    ],
    "total_estimated_cost": 380,
}

FAKE_BUDGET_OVER = {
    "daily_costs": [
        {"day": 1, "cost": "550 PLN"},
        {"day": 2, "cost": "500 PLN"},
    ],
    "total_estimated_cost": 1050,
}


async def _setup_world_and_run(fake_response, budget=500):
    """Helper: prepares WorldState with all dependencies and runs BudgetAgent."""
    fake_llm = FakeLLMProvider(response_data=fake_response)
    agent = BudgetAgent(llm_provider=fake_llm, model_name="fake-model")
    world = WorldState(_make_input(budget=budget))
    world.days = _make_days()
    world.culinary_section = _make_culinary()
    world.mobility_section = _make_mobility()
    world.constraints = {}
    bus = InMemoryEventBus()
    await bus.emit("cost_updated")

    await agent.run(world, bus)
    return world, bus, fake_llm


@pytest.mark.asyncio
async def test_budget_within_limit_generates_good_news():
    """When estimated cost is within budget, alert should say 'Good news'."""
    world, bus, _ = await _setup_world_and_run(FAKE_BUDGET_WITHIN, budget=500)

    assert world.total_cost == 380
    alerts = world.constraints.get("alerts", [])
    assert len(alerts) >= 1
    assert any("Good news" in a for a in alerts)


@pytest.mark.asyncio
async def test_budget_over_limit_generates_warning():
    """When estimated cost exceeds budget, alert should say 'Warning'."""
    world, bus, _ = await _setup_world_and_run(FAKE_BUDGET_OVER, budget=500)

    assert world.total_cost == 1050
    alerts = world.constraints.get("alerts", [])
    assert len(alerts) >= 1
    assert any("Warning" in a for a in alerts)
    assert any("exceeds" in a for a in alerts)


@pytest.mark.asyncio
async def test_budget_updates_day_costs():
    """Budget agent should update estimated_cost on each TripDay."""
    world, _, _ = await _setup_world_and_run(FAKE_BUDGET_WITHIN)

    assert world.days[0].estimated_cost == "200 PLN"
    assert world.days[1].estimated_cost == "180 PLN"


@pytest.mark.asyncio
async def test_budget_emits_plan_stable():
    """After processing, 'plan_stable' event should be emitted."""
    world, bus, _ = await _setup_world_and_run(FAKE_BUDGET_WITHIN)

    result = await bus.subscribe_with_timeout("plan_stable", timeout=0.1)
    assert result is True


@pytest.mark.asyncio
async def test_budget_records_token_usage():
    """Token usage should be recorded under 'BudgetAgent'."""
    world, _, _ = await _setup_world_and_run(FAKE_BUDGET_WITHIN)

    assert "BudgetAgent" in world.token_usage
    assert world.token_usage["BudgetAgent"]["total_tokens"] == 300


@pytest.mark.asyncio
async def test_budget_prompt_includes_mobility_info():
    """Mobility pricing info should appear in the LLM prompt."""
    _, _, fake_llm = await _setup_world_and_run(FAKE_BUDGET_WITHIN)

    user_prompt = fake_llm.calls[0]["user"]
    assert "Cheap" in user_prompt or "Moderate" in user_prompt


@pytest.mark.asyncio
async def test_budget_prompt_includes_food_prices():
    """Food price ranges should appear in the LLM prompt."""
    _, _, fake_llm = await _setup_world_and_run(FAKE_BUDGET_WITHIN)

    user_prompt = fake_llm.calls[0]["user"]
    assert "15-25 PLN" in user_prompt or "30-60 PLN" in user_prompt


@pytest.mark.asyncio
@patch.dict("os.environ", {"ENABLE_BUDGET": "false"})
async def test_budget_disabled_by_env():
    """When disabled, agent should set cost to 0 and emit plan_stable."""
    fake_llm = FakeLLMProvider(response_data=FAKE_BUDGET_WITHIN)
    agent = BudgetAgent(llm_provider=fake_llm, model_name="fake-model")
    world = WorldState(_make_input())
    world.days = _make_days()
    world.culinary_section = _make_culinary()
    world.mobility_section = _make_mobility()
    world.constraints = {}
    bus = InMemoryEventBus()
    await bus.emit("cost_updated")

    await agent.run(world, bus)

    assert world.total_cost == 0.0
    assert len(fake_llm.calls) == 0
    result = await bus.subscribe_with_timeout("plan_stable", timeout=0.1)
    assert result is True
