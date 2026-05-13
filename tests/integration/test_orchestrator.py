"""
Integration test for OrchestratorAgent with mocked LLM.
Verifies that the full pipeline (all agents) produces a complete TripPlan
when all agents use a FakeLLMProvider.

This is the most comprehensive integration test — it exercises the entire
agent coordination through WorldState and EventBus without calling a real LLM.
"""
import pytest
from unittest.mock import patch
from backend.agents.orchestrator import OrchestratorAgent
from backend.models import UserInput, LLMSettings, TripPlan


CITY_OVERVIEW_RESPONSE = {
    "city_name": "Warsaw",
    "short_description": "Capital of Poland, blending rich history with modern energy.",
    "history_summary": "Warsaw rose from WWII ashes, rebuilding its Old Town brick by brick.",
    "cultural_identity": "A vibrant mix of art, music, and entrepreneurial spirit.",
}

PREFERENCES_RESPONSE = {
    "dietary_restrictions": ["vegetarian"],
    "accessibility": "none",
    "attractions_hints": "Focus on historical sites",
    "gastronomy_hints": "Prefer vegetarian options",
    "transport_hints": "",
    "general_notes": "",
}

ATTRACTIONS_RESPONSE = [
    {
        "day": 1, "date": "2024-07-10", "theme": "Old Town Heritage",
        "summary": "Historic Warsaw exploration.",
        "activities": [
            {"name": "Royal Castle", "description": "Baroque royal residence.", "duration": "1.5h"},
            {"name": "Old Town Square", "description": "Heart of Warsaw.", "duration": "1h"},
        ],
        "estimated_cost": "50 PLN",
    },
    {
        "day": 2, "date": "2024-07-11", "theme": "Modern Warsaw",
        "summary": "Contemporary culture and science.",
        "activities": [
            {"name": "Copernicus Centre", "description": "Interactive science museum.", "duration": "2h"},
        ],
        "estimated_cost": "30 PLN",
    },
    {
        "day": 3, "date": "2024-07-12", "theme": "Green Warsaw",
        "summary": "Parks and nature.",
        "activities": [
            {"name": "Łazienki Park", "description": "Largest park in Warsaw.", "duration": "1.5h"},
        ],
        "estimated_cost": "0 PLN",
    },
]

CULINARY_RESPONSE = {
    "main_dishes": [
        {"name": "Pierogi", "description": "Polish dumplings.", "price_range": "15-25 PLN"},
        {"name": "Bigos", "description": "Hunter's stew.", "price_range": "20-30 PLN"},
        {"name": "Schabowy", "description": "Pork cutlet.", "price_range": "25-35 PLN"},
        {"name": "Gołąbki", "description": "Cabbage rolls.", "price_range": "18-28 PLN"},
        {"name": "Placki", "description": "Potato pancakes.", "price_range": "12-20 PLN"},
        {"name": "Żurek", "description": "Sour rye soup in bread.", "price_range": "15-22 PLN"},
    ],
    "soups": [{"name": "Barszcz", "description": "Beetroot soup.", "price_range": "8-15 PLN"}],
    "desserts": [{"name": "Sernik", "description": "Cheesecake.", "price_range": "10-18 PLN"}],
    "drinks": [{"name": "Local Beer", "description": "Polish beer.", "price_range": "8-15 PLN"}],
    "venues_traditional": [
        {"name": "Zapiecek", "district": "Old Town", "type": "Traditional", "price_range": "30-60 PLN", "signature_items": "Pierogi"},
    ],
    "venues_cafes": [
        {"name": "Café Bristol", "district": "Center", "type": "Café", "price_range": "20-40 PLN", "signature_items": "Coffee"},
    ],
    "venues_bars": [
        {"name": "Piw Paw", "district": "Center", "type": "Craft Beer", "price_range": "12-25 PLN", "signature_items": "IPA"},
    ],
}

MOBILITY_RESPONSE = {
    "public_transport": {
        "available_options": ["Metro", "Bus", "Tram"],
        "ticket_types": "Single 4.40 PLN, 24h 15 PLN",
        "approximate_prices": "4.40-36 PLN",
        "coverage_quality": "Excellent",
        "useful_apps": ["Jakdojade"],
        "best_use_cases": "Daily transport",
        "price_level": "💸 Cheap",
        "website_url": "https://www.wtp.waw.pl",
    },
    "taxis": {
        "available_apps": ["Uber", "Bolt"],
        "typical_pricing_level": "💸💸 Moderate",
        "safety_notes": "Use licensed apps.",
        "when_to_use": "Late night",
    },
    "walking": {"is_walkable": True, "best_areas": ["Old Town"]},
    "bikes": {
        "available": True, "providers": ["Veturilo"],
        "price_range": "Free first 20 min",
        "convenience": "Good", "cautions": ["Watch trams"],
    },
    "ferries": {"is_relevant": False, "routes": "", "cost_level": "", "tourist_vs_commuter": ""},
    "car_rental": {"recommended": False, "parking_difficulty": "High", "notes": "Not recommended."},
    "quick_recommendations": {
        "best_overall": "Metro", "cheapest": "Walking",
        "most_convenient": "Uber", "avoid": ["Rush hour"],
    },
}

BUDGET_RESPONSE = {
    "daily_costs": [
        {"day": 1, "cost": "250 PLN"},
        {"day": 2, "cost": "200 PLN"},
        {"day": 3, "cost": "150 PLN"},
    ],
    "total_estimated_cost": 600,
}


class SequentialFakeLLMProvider:
    def __init__(self):
        self._responses = [
            PREFERENCES_RESPONSE,
            CITY_OVERVIEW_RESPONSE,
            ATTRACTIONS_RESPONSE,
            CULINARY_RESPONSE,
            MOBILITY_RESPONSE,
            BUDGET_RESPONSE,
        ]
        self._call_idx = 0
        self.calls = []

    def generate_content(self, system_prompt, user_prompt, **kwargs):
        self.calls.append({"system": system_prompt, "user": user_prompt, "kwargs": kwargs})
        if "Preferences Analyst" in system_prompt:
            data = PREFERENCES_RESPONSE
        elif "Destination Analyser" in system_prompt:
            data = CITY_OVERVIEW_RESPONSE
        elif "expert Travel Agent" in system_prompt:
            data = ATTRACTIONS_RESPONSE
        elif "Culinary Guide" in system_prompt:
            data = CULINARY_RESPONSE
        elif "Mobility Guide" in system_prompt:
            data = MOBILITY_RESPONSE
        elif "Budget Planner" in system_prompt:
            data = BUDGET_RESPONSE
        elif "Feedback Analyst" in system_prompt:
            data = {"budget_modifier": 1.0, "pace_override": "", "rerun_agents": []}
        else:
            data = {}

        usage = {
            "input_tokens": 100, "output_tokens": 200,
            "total_tokens": 300, "cost": 0.001, "model": "fake-model",
        }
        return data, usage


@pytest.mark.asyncio
async def test_orchestrator_returns_complete_plan():
    """Full pipeline with mocked LLM should produce a valid TripPlan."""
    fake_llm = SequentialFakeLLMProvider()

    user_input = UserInput(
        destination="Warsaw, Poland",
        arrival="2024-07-10",
        departure="2024-07-12",
        guests=2,
        budget=500,
        pace="medium",
        transport=["metro"],
        extra_req="I love history and I'm vegetarian",
        llm_settings=LLMSettings(provider="gemini", model="fake-model"),
    )

    with patch("backend.llm.factory.LLMFactory.create_provider", return_value=fake_llm):
        orchestrator = OrchestratorAgent()
        plan = await orchestrator.run(user_input)

    assert plan is not None
    assert isinstance(plan, TripPlan)
    assert plan.destination == "Warsaw, Poland"


@pytest.mark.asyncio
async def test_orchestrator_produces_days():
    """The plan should contain the expected number of trip days."""
    fake_llm = SequentialFakeLLMProvider()

    user_input = UserInput(
        destination="Warsaw, Poland",
        arrival="2024-07-10",
        departure="2024-07-12",
        guests=2,
        budget=500,
        pace="medium",
        transport=["metro"],
        extra_req="I love history",
        llm_settings=LLMSettings(provider="gemini", model="fake-model"),
    )

    with patch("backend.llm.factory.LLMFactory.create_provider", return_value=fake_llm):
        orchestrator = OrchestratorAgent()
        plan = await orchestrator.run(user_input)

    assert len(plan.days) == 3
    assert plan.days[0].theme == "Old Town Heritage"


@pytest.mark.asyncio
async def test_orchestrator_has_usage_stats():
    """Plan should contain usage stats from each agent."""
    fake_llm = SequentialFakeLLMProvider()

    user_input = UserInput(
        destination="Warsaw, Poland",
        arrival="2024-07-10",
        departure="2024-07-12",
        guests=2,
        budget=500,
        pace="medium",
        transport=["metro"],
        extra_req="History please",
        llm_settings=LLMSettings(provider="gemini", model="fake-model"),
    )

    with patch("backend.llm.factory.LLMFactory.create_provider", return_value=fake_llm):
        orchestrator = OrchestratorAgent()
        plan = await orchestrator.run(user_input)

    assert len(plan.usage_stats) > 0
    # At least some agents should have recorded usage
    agent_names = list(plan.usage_stats.keys())
    assert any("Agent" in name for name in agent_names)


@pytest.mark.asyncio
async def test_orchestrator_has_culinary_section():
    """Plan should contain the culinary section from GastronomyAgent."""
    fake_llm = SequentialFakeLLMProvider()

    user_input = UserInput(
        destination="Warsaw, Poland",
        arrival="2024-07-10",
        departure="2024-07-12",
        guests=2,
        budget=500,
        pace="medium",
        transport=["metro"],
        extra_req="I love food",
        llm_settings=LLMSettings(provider="gemini", model="fake-model"),
    )

    with patch("backend.llm.factory.LLMFactory.create_provider", return_value=fake_llm):
        orchestrator = OrchestratorAgent()
        plan = await orchestrator.run(user_input)

    assert plan.culinary_section is not None
    assert len(plan.culinary_section.main_dishes) >= 1


@pytest.mark.asyncio
async def test_orchestrator_has_mobility_section():
    """Plan should contain the mobility section from TransportationAgent."""
    fake_llm = SequentialFakeLLMProvider()

    user_input = UserInput(
        destination="Warsaw, Poland",
        arrival="2024-07-10",
        departure="2024-07-12",
        guests=2,
        budget=500,
        pace="medium",
        transport=["metro"],
        llm_settings=LLMSettings(provider="gemini", model="fake-model"),
    )

    with patch("backend.llm.factory.LLMFactory.create_provider", return_value=fake_llm):
        orchestrator = OrchestratorAgent()
        plan = await orchestrator.run(user_input)

    assert plan.mobility_section is not None
    assert plan.mobility_section.public_transport is not None


@pytest.mark.asyncio
async def test_orchestrator_has_city_overview():
    """Plan should contain the city overview from CityOverviewAgent."""
    fake_llm = SequentialFakeLLMProvider()

    user_input = UserInput(
        destination="Warsaw, Poland",
        arrival="2024-07-10",
        departure="2024-07-12",
        guests=2,
        budget=500,
        pace="medium",
        transport=["metro"],
        llm_settings=LLMSettings(provider="gemini", model="fake-model"),
    )

    with patch("backend.llm.factory.LLMFactory.create_provider", return_value=fake_llm):
        orchestrator = OrchestratorAgent()
        plan = await orchestrator.run(user_input)

    assert plan.city_overview is not None
    assert plan.city_overview.city_name == "Warsaw"
