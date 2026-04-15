from typing import List
from backend.models import TripDay
from backend.agents.base import BaseAgent
from datetime import datetime, timedelta
import os

TRIP_DAY_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "day":            {"type": "integer"},
            "date":           {"type": "string"},
            "theme":          {"type": "string"},
            "summary":        {"type": "string"},
            "activities": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "name":        {"type": "string"},
                        "description": {"type": "string"},
                        "duration":    {"type": "string"},
                    },
                    "required": ["name", "description", "duration"],
                },
            },
            "estimated_cost": {"type": "string"},
        },
        "required": ["day", "date", "theme", "summary", "activities", "estimated_cost"],
    },
}

_SIGHTSEEING_START_HOUR = 9
_SIGHTSEEING_END_HOUR = 21


def _parse_datetime(dt_str: str) -> datetime:
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(dt_str.strip(), fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse datetime: {dt_str!r}")


def _available_hours(dt: datetime, is_arrival: bool) -> float:
    if is_arrival:
        start = max(dt.hour + dt.minute / 60, _SIGHTSEEING_START_HOUR)
        return max(0.0, _SIGHTSEEING_END_HOUR - start)
    else:
        end = min(dt.hour + dt.minute / 60, _SIGHTSEEING_END_HOUR)
        return max(0.0, end - _SIGHTSEEING_START_HOUR)


def _hours_to_instruction(hours: float) -> str:
    if hours <= 0:
        return "0h available — NO attractions (travel day only, do NOT add any activities)"
    if hours <= 2:
        return f"{hours:.0f}h available — maximum 2 quick attractions only"
    if hours <= 4:
        return f"{hours:.0f}h available — maximum 3-4 attractions"
    if hours <= 6:
        return f"{hours:.0f}h available — maximum 5-6 attractions"
    if hours <= 9:
        return f"{hours:.0f}h available — 7-9 attractions"
    return f"{hours:.0f}h available — full day, minimum 10 attractions"


class AttractionsAgent(BaseAgent):
    def __init__(self, llm_provider=None, model_name=None):
        super().__init__(name="AttractionsAgent", llm_provider=llm_provider, model_name=model_name)

    async def run(self, world: "WorldState", bus: "EventBus"):
        self.logger.info("Waiting for constraints...")
        await bus.subscribe("constraints_ready")

        if os.environ.get("ENABLE_ATTRACTIONS", "true").lower() == "false":
             self.logger.info("Attractions Agent disabled by ENABLE_ATTRACTIONS flag.")
             async with world.lock:
                 world.days = []
             await bus.emit("days_planned")
             return

        async with world.lock:
            user_input = world.user_input
            constraints = world.constraints

        self.logger.info(f"Generating itinerary for {user_input.destination} with constraints {constraints}")

        try:
            arrival_dt   = _parse_datetime(user_input.arrival)
            departure_dt = _parse_datetime(user_input.departure)
            start_date   = arrival_dt.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date     = departure_dt.replace(hour=0, minute=0, second=0, microsecond=0)
            num_days     = (end_date - start_date).days + 1
        except Exception as e:
            self.logger.error(f"Date parsing error: {e}. Defaulting to 3 days.")
            arrival_dt   = datetime.now().replace(hour=9, minute=0)
            departure_dt = arrival_dt + timedelta(days=3)
            start_date   = arrival_dt.replace(hour=0, minute=0)
            num_days     = 3

        dates = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(num_days)]

        day_notes = []
        for i, date_str in enumerate(dates):
            if i == 0 and i == num_days - 1:
                avail = min(
                    _available_hours(arrival_dt, is_arrival=True),
                    _available_hours(departure_dt, is_arrival=False),
                )
                note = f"Day 1 ({date_str}) [arrival {arrival_dt.strftime('%H:%M')} & departure {departure_dt.strftime('%H:%M')}]: {_hours_to_instruction(avail)}"
            elif i == 0:
                avail = _available_hours(arrival_dt, is_arrival=True)
                note = f"Day 1 ({date_str}) [arrival {arrival_dt.strftime('%H:%M')}]: {_hours_to_instruction(avail)}"
            elif i == num_days - 1:
                avail = _available_hours(departure_dt, is_arrival=False)
                note = f"Day {i+1} ({date_str}) [departure {departure_dt.strftime('%H:%M')}]: {_hours_to_instruction(avail)}"
            else:
                note = f"Day {i+1} ({date_str}): full day, minimum 10 attractions"
            day_notes.append(note)

        day_availability_block = "\n".join(f"  - {n}" for n in day_notes)

        system_prompt = self._build_system_prompt()

        total_budget = user_input.budget * user_input.guests
        attractions_budget = total_budget * 0.30
        interests = constraints.get("interest_tags", [])
        pace = constraints.get("pace", "moderate")
        accessibility = constraints.get("accessibility", "none")
        attractions_hints = constraints.get("attractions_hints", "")

        constraints_block = (
            f"Interests: {', '.join(interests) if interests else 'general sightseeing'}\n"
            f"Pace: {pace}\n"
            f"Accessibility: {accessibility}\n"
        )
        if attractions_hints:
            constraints_block += f"IMPORTANT user preferences: {attractions_hints}\n"

        user_prompt = (
            f"Destination: {user_input.destination}\n"
            f"Arrival: {user_input.arrival}  |  Departure: {user_input.departure}\n"
            f"Total trip budget: {total_budget} PLN (for {user_input.guests} guests, {user_input.budget} per person).\n"
            f"CRITICAL BUDGET CONSTRAINT: The TOTAL cost of ALL attractions and entrance fees for the ENTIRE trip MUST NOT exceed {attractions_budget:.0f} PLN. "
            f"Food and transport are handled separately. Focus on FREE attractions (parks, squares, street art, free museums, walking tours) "
            f"and only add paid attractions if they fit within the {attractions_budget:.0f} PLN attractions budget.\n"
            f"{constraints_block}\n"
            f"Per-day availability (MUST be respected):\n{day_availability_block}\n\n"
            f"Generate a {num_days}-day itinerary following the above constraints. Return ONLY the JSON array."
        )

        parsed_days, usage = await self.call_llm(
            system_prompt,
            user_prompt,
            json_response=True,
            response_schema=TRIP_DAY_SCHEMA,
        )

        async with world.lock:
             world.token_usage[self.name] = usage

        trip_days = self._parse_days(parsed_days)

        async with world.lock:
            world.days = trip_days

        await bus.emit("days_planned")
        await bus.emit("cost_updated")

    def _build_system_prompt(self):
        return (
            "You are an expert Travel Agent specializing in creating personalized daily itineraries. "
            "CRITICAL RULE: You MUST respect the available hours constraint for EACH day listed below. "
            "On travel days (arrival or departure), you MUST plan ONLY as many attractions as fit in the available time window. "
            "Do NOT plan attractions outside of realistic sightseeing hours (09:00–21:00). "
            "For full days, plan STRICTLY minimum 10 attractions. "
            "You MUST distribute the attractions logically: "
            "1. Maintain historical and thematic coherence where possible. "
            "2. Minimize distances between attractions within the same day (group them geographically). "
            "3. Arrange attractions in a realistic order based on the available time window. "
            "Focus strictly on sightseeing and attractions, NOT food/restaurants (another agent handles that). "
            "For 'duration': use minutes for times under 1 hour (e.g. '20 min', '45 min'). Use hours for 1 hour or more (e.g. '1h', '1.5h'). "
            "You MUST return the valid JSON array of objects, where each object represents a day. "
            "The JSON schema for each day is: "
            "{\n"
            "  \"day\": integer,\n"
            "  \"date\": \"YYYY-MM-DD\",\n"
            "  \"theme\": \"string (short theme of the day)\",\n"
            "  \"summary\": \"string (short summary of the day)\",\n"
            "  \"activities\": [\n"
            "    {\"name\": \"Attraction Name\", \"description\": \"One sentence on why it's important.\", \"duration\": \"string (e.g. '1.5h' or '45 min')\"},\n"
            "    ...\n"
            "  ],\n"
            "  \"estimated_cost\": \"string (estimated cost range)\"\n"
            "}\n"
            "Do NOT include any markdown formatting (like ```json), just the raw JSON string."
        )

    def _parse_days(self, parsed_days) -> List[TripDay]:
        trip_days = []
        if parsed_days:
            try:
                for d in parsed_days:
                    trip_days.append(TripDay(**d))
            except Exception as e:
                 self.logger.error(f"Parsing Error: {e}")
                 trip_days = self._fallback_response()
        else:
            trip_days = self._fallback_response()
        return trip_days

    def _fallback_response(self) -> List[TripDay]:
        self.logger.warning("Using fallback response.")
        return []
