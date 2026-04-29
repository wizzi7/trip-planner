import pytest
from backend.world_state import WorldState
from backend.models import UserInput, TripDay, Activity, CulinarySection, CityOverview


def _make_input():
    return UserInput(
        destination="Rome", arrival="2024-08-01", departure="2024-08-03",
        guests=2, budget=300, pace="slow", transport=["metro"],
    )


class TestWorldStateInit:
    def test_initial_state(self):
        ws = WorldState(_make_input())
        assert ws.days is None
        assert ws.total_cost == 0.0
        assert ws.constraints == {}
        assert ws.culinary_section is None
        assert ws.mobility_section is None
        assert ws.city_overview is None
        assert ws.token_usage == {}

    def test_stores_user_input(self):
        ui = _make_input()
        ws = WorldState(ui)
        assert ws.user_input.destination == "Rome"
        assert ws.user_input.guests == 2


class TestWorldStateSnapshot:
    @pytest.mark.asyncio
    async def test_empty_snapshot(self):
        ws = WorldState(_make_input())
        snap = await ws.get_snapshot()
        assert snap["days"] == []
        assert snap["total_cost"] == 0.0
        assert snap["constraints"] == {}
        assert snap["culinary_section"] is None
        assert snap["mobility_section"] is None
        assert snap["city_overview"] is None
        assert snap["token_usage"] == {}

    @pytest.mark.asyncio
    async def test_snapshot_with_days(self):
        ws = WorldState(_make_input())
        ws.days = [
            TripDay(day=1, date="2024-08-01", theme="Art", summary="...",
                    activities=[Activity(name="Colosseum", description="...", duration="2h")],
                    estimated_cost="20 EUR"),
        ]
        ws.total_cost = 150.0
        snap = await ws.get_snapshot()
        assert len(snap["days"]) == 1
        assert snap["total_cost"] == 150.0

    @pytest.mark.asyncio
    async def test_snapshot_returns_copies(self):
        ws = WorldState(_make_input())
        ws.constraints = {"pace": "fast"}
        snap = await ws.get_snapshot()
        snap["constraints"]["pace"] = "slow"
        assert ws.constraints["pace"] == "fast"

    @pytest.mark.asyncio
    async def test_snapshot_with_city_overview(self):
        ws = WorldState(_make_input())
        ws.city_overview = CityOverview(
            city_name="Rome", short_description="Eternal City",
            history_summary="...", cultural_identity="...",
        )
        snap = await ws.get_snapshot()
        assert snap["city_overview"].city_name == "Rome"

    @pytest.mark.asyncio
    async def test_snapshot_with_token_usage(self):
        ws = WorldState(_make_input())
        ws.token_usage = {"Agent1": {"input_tokens": 100, "output_tokens": 200}}
        snap = await ws.get_snapshot()
        assert "Agent1" in snap["token_usage"]
