import pytest
from pydantic import ValidationError
from backend.models import (
    UserInput, LLMSettings, Activity, TripDay, TripPlan,
    CulinarySection, CulinaryDish, CulinaryVenue,
    MobilitySection, MobilityOption, MobilitySystem,
    CityOverview, UsageStats, UpdateRequest,
)

class TestUserInput:
    def test_requires_destination(self):
        with pytest.raises(ValidationError):
            UserInput(
                arrival="2024-07-10", departure="2024-07-12",
                guests=2, budget=500, pace="medium", transport=["bus"],
            )

    def test_requires_transport(self):
        with pytest.raises(ValidationError):
            UserInput(
                destination="Paris", arrival="2024-07-10",
                departure="2024-07-12", guests=2, budget=500, pace="medium",
            )

    def test_defaults(self, sample_user_input):
        ui = sample_user_input
        assert ui.llm_settings is None
        assert ui.interests == []
        assert ui.extra_req is None
        assert ui.accommodation is None
        assert len(ui.active_agents) > 0
        assert "AttractionsAgent" in ui.active_agents
        assert "BudgetAgent" in ui.active_agents

    def test_all_default_agents_present(self, sample_user_input):
        expected = {
            "PreferencesAgent", "AttractionsAgent", "GastronomyAgent",
            "TransportationAgent", "BudgetAgent", "CityOverviewAgent",
        }
        assert set(sample_user_input.active_agents) == expected

    def test_custom_llm_settings(self):
        settings = LLMSettings(provider="openai", model="gpt-4o", temperature=0.5, max_tokens=3000)
        ui = UserInput(
            destination="Berlin", arrival="2024-07-10", departure="2024-07-12",
            guests=1, budget=200, pace="fast", transport=["taxi"],
            llm_settings=settings,
        )
        assert ui.llm_settings.provider == "openai"
        assert ui.llm_settings.model == "gpt-4o"

    def test_extra_req_optional(self):
        ui = UserInput(
            destination="Rome", arrival="2024-08-01", departure="2024-08-03",
            guests=1, budget=300, pace="slow", transport=["metro"],
            extra_req="I love art museums",
        )
        assert ui.extra_req == "I love art museums"


class TestLLMSettings:
    def test_defaults(self):
        s = LLMSettings()
        assert s.provider == "gemini"
        assert s.temperature == 0.7
        assert s.max_tokens == 2000


class TestActivity:
    def test_minimal(self):
        a = Activity(name="Castle", description="Medieval castle", duration="1.5h")
        assert a.time is None
        assert a.name == "Castle"

    def test_with_time(self):
        a = Activity(name="Park", description="City park", duration="45 min", time="10:00")
        assert a.time == "10:00"


class TestTripDay:
    def test_roundtrip_serialization(self):
        day = TripDay(
            day=1, date="2024-07-10", theme="History", summary="Old town exploration",
            activities=[
                Activity(name="Castle", description="Medieval castle", duration="1.5h"),
                Activity(name="Square", description="Main square", duration="30 min"),
            ],
            estimated_cost="120 PLN",
        )
        data = day.model_dump()
        rebuilt = TripDay(**data)
        assert rebuilt.theme == "History"
        assert len(rebuilt.activities) == 2
        assert rebuilt.activities[0].name == "Castle"
        assert rebuilt.estimated_cost == "120 PLN"

    def test_no_activities(self):
        day = TripDay(
            day=1, date="2024-07-10", theme="Travel Day",
            summary="Arrival", activities=[], estimated_cost="0 PLN",
        )
        assert day.activities == []


class TestCulinarySection:
    def test_empty_defaults(self):
        cs = CulinarySection()
        assert cs.main_dishes == []
        assert cs.soups == []
        assert cs.desserts == []
        assert cs.drinks == []
        assert cs.venues_traditional == []
        assert cs.venues_cafes == []
        assert cs.venues_bars == []

    def test_with_data(self):
        cs = CulinarySection(
            main_dishes=[CulinaryDish(name="Pierogi", description="Polish dumplings", price_range="15-25 PLN")],
            venues_traditional=[CulinaryVenue(name="Zapiecek", price_range="30-60 PLN")],
        )
        assert len(cs.main_dishes) == 1
        assert cs.main_dishes[0].name == "Pierogi"


class TestCityOverview:
    def test_creation(self):
        co = CityOverview(
            city_name="Warsaw",
            short_description="Capital of Poland.",
            history_summary="Rich history spanning centuries.",
            cultural_identity="Vibrant and resilient culture.",
        )
        assert co.city_name == "Warsaw"


class TestTripPlan:
    def test_minimal(self):
        plan = TripPlan(destination="Warsaw", total_cost=0.0, days=[])
        assert plan.destination == "Warsaw"
        assert plan.usage_stats == {}
        assert plan.culinary_section is None
        assert plan.mobility_section is None
        assert plan.city_overview is None
        assert plan.metadata == {}

    def test_complete(self):
        plan = TripPlan(
            destination="Warsaw",
            total_cost=750.0,
            days=[
                TripDay(day=1, date="2024-07-10", theme="Old Town", summary="...",
                        activities=[Activity(name="Castle", description="...", duration="1h")],
                        estimated_cost="250 PLN"),
            ],
            usage_stats={"agent1": UsageStats(input_tokens=100, output_tokens=200, total_tokens=300, cost=0.01, model="test")},
            culinary_section=CulinarySection(),
            city_overview=CityOverview(city_name="Warsaw", short_description="...", history_summary="...", cultural_identity="..."),
            metadata={"constraints": {"pace": "medium"}},
        )
        assert plan.total_cost == 750.0
        assert len(plan.days) == 1
        assert "agent1" in plan.usage_stats


class TestUsageStats:
    def test_creation(self):
        us = UsageStats(input_tokens=100, output_tokens=200, total_tokens=300, cost=0.005, model="gpt-4o")
        assert us.total_tokens == 300
        assert us.cost == 0.005
