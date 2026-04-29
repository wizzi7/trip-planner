import pytest
from datetime import datetime
from backend.agents.attractions import (
    _parse_datetime,
    _available_hours,
    _hours_to_instruction,
    AttractionsAgent,
    _SIGHTSEEING_START_HOUR,
    _SIGHTSEEING_END_HOUR,
)

class TestParseDatetime:
    def test_date_only(self):
        dt = _parse_datetime("2024-07-10")
        assert dt == datetime(2024, 7, 10, 0, 0)

    def test_datetime_with_seconds(self):
        dt = _parse_datetime("2024-07-10 14:30:00")
        assert dt == datetime(2024, 7, 10, 14, 30, 0)

    def test_datetime_without_seconds(self):
        dt = _parse_datetime("2024-07-10 09:15")
        assert dt.hour == 9
        assert dt.minute == 15

    def test_iso_format_with_T(self):
        dt = _parse_datetime("2024-07-10T18:00")
        assert dt.hour == 18

    def test_whitespace_stripped(self):
        dt = _parse_datetime("  2024-07-10  ")
        assert dt == datetime(2024, 7, 10)

    def test_invalid_raises_value_error(self):
        with pytest.raises(ValueError, match="Cannot parse datetime"):
            _parse_datetime("not-a-date")

    def test_empty_string_raises(self):
        with pytest.raises(ValueError):
            _parse_datetime("")

    def test_partial_date_raises(self):
        with pytest.raises(ValueError):
            _parse_datetime("2024-07")


class TestAvailableHours:
    def test_arrival_early_morning(self):
        dt = datetime(2024, 7, 10, 7, 0)
        assert _available_hours(dt, is_arrival=True) == 12.0

    def test_arrival_at_start(self):
        dt = datetime(2024, 7, 10, 9, 0)
        assert _available_hours(dt, is_arrival=True) == 12.0

    def test_arrival_noon(self):
        dt = datetime(2024, 7, 10, 12, 0)
        assert _available_hours(dt, is_arrival=True) == 9.0

    def test_arrival_late_evening(self):
        dt = datetime(2024, 7, 10, 20, 0)
        assert _available_hours(dt, is_arrival=True) == 1.0

    def test_arrival_at_end(self):
        dt = datetime(2024, 7, 10, 21, 0)
        assert _available_hours(dt, is_arrival=True) == 0.0

    def test_arrival_after_end(self):
        dt = datetime(2024, 7, 10, 23, 0)
        assert _available_hours(dt, is_arrival=True) == 0.0

    def test_departure_early(self):
        dt = datetime(2024, 7, 10, 10, 0)
        assert _available_hours(dt, is_arrival=False) == 1.0

    def test_departure_noon(self):
        dt = datetime(2024, 7, 10, 12, 0)
        assert _available_hours(dt, is_arrival=False) == 3.0

    def test_departure_evening(self):
        dt = datetime(2024, 7, 10, 21, 0)
        assert _available_hours(dt, is_arrival=False) == 12.0

    def test_departure_late_night(self):
        dt = datetime(2024, 7, 10, 23, 0)
        assert _available_hours(dt, is_arrival=False) == 12.0

    def test_departure_before_start(self):
        dt = datetime(2024, 7, 10, 8, 0)
        assert _available_hours(dt, is_arrival=False) == 0.0

    def test_arrival_with_minutes(self):
        dt = datetime(2024, 7, 10, 14, 30)
        assert _available_hours(dt, is_arrival=True) == 6.5


class TestHoursToInstruction:
    def test_zero_hours(self):
        result = _hours_to_instruction(0)
        assert "NO attractions" in result
        assert "travel day" in result.lower()

    def test_negative_hours(self):
        result = _hours_to_instruction(-1)
        assert "NO attractions" in result

    def test_two_hours(self):
        result = _hours_to_instruction(2)
        assert "2" in result

    def test_four_hours(self):
        result = _hours_to_instruction(4)
        assert "3-4" in result

    def test_six_hours(self):
        result = _hours_to_instruction(6)
        assert "5-6" in result

    def test_nine_hours(self):
        result = _hours_to_instruction(9)
        assert "7-9" in result

    def test_full_day(self):
        result = _hours_to_instruction(12)
        assert "minimum 10" in result

    def test_all_tiers_are_distinct(self):
        values = [0, 1, 3, 5, 8, 12]
        instructions = [_hours_to_instruction(v) for v in values]
        assert len(set(instructions)) == len(instructions)


class TestParseDays:
    def setup_method(self):
        self.agent = AttractionsAgent()

    def test_valid_single_day(self):
        raw = [{
            "day": 1, "date": "2024-07-10", "theme": "Old Town",
            "summary": "Exploring the historic center",
            "activities": [
                {"name": "Royal Castle", "description": "Historic royal residence", "duration": "1.5h"},
                {"name": "Market Square", "description": "Central square", "duration": "30 min"},
            ],
            "estimated_cost": "50 PLN",
        }]
        days = self.agent._parse_days(raw)
        assert len(days) == 1
        assert days[0].day == 1
        assert days[0].theme == "Old Town"
        assert len(days[0].activities) == 2
        assert days[0].activities[0].name == "Royal Castle"

    def test_valid_multi_day(self):
        raw = [
            {"day": 1, "date": "2024-07-10", "theme": "Day 1", "summary": "...",
             "activities": [{"name": "A", "description": "...", "duration": "1h"}], "estimated_cost": "30 PLN"},
            {"day": 2, "date": "2024-07-11", "theme": "Day 2", "summary": "...",
             "activities": [{"name": "B", "description": "...", "duration": "2h"}], "estimated_cost": "40 PLN"},
            {"day": 3, "date": "2024-07-12", "theme": "Day 3", "summary": "...",
             "activities": [{"name": "C", "description": "...", "duration": "1h"}], "estimated_cost": "20 PLN"},
        ]
        days = self.agent._parse_days(raw)
        assert len(days) == 3
        assert [d.day for d in days] == [1, 2, 3]

    def test_none_returns_empty(self):
        assert self.agent._parse_days(None) == []

    def test_empty_list_returns_empty(self):
        assert self.agent._parse_days([]) == []

    def test_invalid_structure_uses_fallback(self):
        raw = [{"day": 1, "invalid_key": "no theme or activities"}]
        days = self.agent._parse_days(raw)
        assert days == []
