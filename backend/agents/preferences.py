from backend.agents.base import BaseAgent
import os

PREFERENCES_SYSTEM_PROMPT = (
    "You are a Travel Preferences Analyst in a multi-agent trip planning system. "
    "Your job is to interpret the user's free-text extra requirements and produce "
    "structured instructions for specialized downstream agents.\n\n"
    "You MUST return a JSON object with exactly these keys:\n"
    "- \"dietary_restrictions\": list of strings (e.g. [\"vegan\", \"gluten-free\"]). Empty list if none mentioned.\n"
    "- \"accessibility\": string describing accessibility needs (e.g. \"wheelchair\", \"child-friendly\"). \"none\" if not applicable.\n"
    "- \"attractions_hints\": string with specific guidance for the sightseeing/attractions planning agent. "
    "Include preferences about types of places, crowd levels, child-friendliness, pace, themes, etc. Empty string if no relevant hints.\n"
    "- \"gastronomy_hints\": string with specific guidance for the culinary/restaurant agent. "
    "Include dietary needs, cuisine preferences, restaurant types, meal preferences, etc. Empty string if no relevant hints.\n"
    "- \"transport_hints\": string with specific guidance for the transportation/mobility agent. "
    "Include preferred transport modes, accessibility needs for transport, bike preferences, etc. Empty string if no relevant hints.\n"
    "- \"general_notes\": string with any other relevant context that doesn't fit the above categories. Empty string if none.\n\n"
    "Be concise but specific. Always write hints in English, even if the user input is in another language."
)

PREFERENCES_RESPONSE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "dietary_restrictions": {
            "type": "array",
            "items": {"type": "string"},
        },
        "accessibility": {"type": "string"},
        "attractions_hints": {"type": "string"},
        "gastronomy_hints": {"type": "string"},
        "transport_hints": {"type": "string"},
        "general_notes": {"type": "string"},
    },
    "required": [
        "dietary_restrictions",
        "accessibility",
        "attractions_hints",
        "gastronomy_hints",
        "transport_hints",
        "general_notes",
    ],
}


class PreferencesAgent(BaseAgent):
    def __init__(self, llm_provider=None, model_name=None):
        super().__init__(name="PreferencesAgent", llm_provider=llm_provider, model_name=model_name)

    async def run(self, world: "WorldState", bus: "EventBus"):
        if os.environ.get("ENABLE_PREFERENCES", "true").lower() == "false":
            self.logger.info("Preferences Agent disabled by ENABLE_PREFERENCES flag.")
            async with world.lock:
                world.constraints = {}
            await bus.emit("constraints_ready")
            return

        self.logger.info(f"Extracting constraints for {world.user_input.destination}")

        ui = world.user_input

        interest_tags = list(ui.interests) if ui.interests else []

        if ui.extra_req and ui.extra_req.strip():
            self.logger.info(f"Extra requirements detected — invoking LLM to interpret: '{ui.extra_req}'")

            user_prompt = (
                f"Destination: {ui.destination}\n"
                f"Trip dates: {ui.arrival} to {ui.departure}\n"
                f"Number of guests: {ui.guests}\n"
                f"Selected interests: {', '.join(interest_tags) if interest_tags else 'none'}\n"
                f"Pace preference: {ui.pace}\n\n"
                f"User's extra requirements (free text):\n\"{ui.extra_req}\"\n\n"
                "Analyze the above and produce the structured JSON."
            )

            llm_result, usage = await self.call_llm(
                PREFERENCES_SYSTEM_PROMPT,
                user_prompt,
                json_response=True,
                response_schema=PREFERENCES_RESPONSE_SCHEMA,
            )

            if llm_result and isinstance(llm_result, dict):
                dietary_restrictions = llm_result.get("dietary_restrictions", [])
                accessibility = llm_result.get("accessibility", "none")
                attractions_hints = llm_result.get("attractions_hints", "")
                gastronomy_hints = llm_result.get("gastronomy_hints", "")
                transport_hints = llm_result.get("transport_hints", "")
                general_notes = llm_result.get("general_notes", "")
                self.logger.info(f"LLM interpretation: dietary={dietary_restrictions}, "
                                 f"accessibility={accessibility}, "
                                 f"attractions_hints='{attractions_hints[:80]}...', "
                                 f"gastronomy_hints='{gastronomy_hints[:80]}...', "
                                 f"transport_hints='{transport_hints[:80]}...'")
            else:
                self.logger.warning("LLM returned empty/invalid result — falling back to rule-based parsing.")
                dietary_restrictions, accessibility, attractions_hints, gastronomy_hints, transport_hints, general_notes = (
                    self._rule_based_parse(ui.extra_req)
                )
                usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "cost": 0.0, "model": "none (fallback)"}
        else:
            self.logger.info("No extra requirements — using rule-based extraction only.")
            dietary_restrictions = []
            accessibility = "none"
            attractions_hints = ""
            gastronomy_hints = ""
            transport_hints = ""
            general_notes = ""
            usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "cost": 0.0, "model": "none (rule-based)"}

        constraints = {
            "interest_tags": interest_tags,
            "dietary_restrictions": dietary_restrictions,
            "accessibility": accessibility,
            "pace": ui.pace,
            "extra_requirements": ui.extra_req or "",
            "attractions_hints": attractions_hints,
            "gastronomy_hints": gastronomy_hints,
            "transport_hints": transport_hints,
            "general_notes": general_notes,
        }

        self.logger.info(f"Final constraints: {constraints}")

        async with world.lock:
            world.constraints = constraints
            world.token_usage[self.name] = usage

        await bus.emit("constraints_ready")

    def _rule_based_parse(self, extra_req: str):
        extra_lower = extra_req.lower()

        dietary_restrictions = []
        diet_keywords = {
            "vegan": "vegan",
            "vegetarian": "vegetarian",
            "gluten": "gluten-free",
            "halal": "halal",
            "kosher": "kosher",
            "lactose": "lactose-free",
        }
        for keyword, tag in diet_keywords.items():
            if keyword in extra_lower and tag not in dietary_restrictions:
                dietary_restrictions.append(tag)

        accessibility = "none"
        access_keywords = ["wheelchair", "disability", "accessible"]
        if any(kw in extra_lower for kw in access_keywords):
            accessibility = "wheelchair_accessible"

        return dietary_restrictions, accessibility, "", "", "", ""
