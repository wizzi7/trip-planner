from backend.models import UserInput, TripPlan
from backend.world_state import WorldState
from backend.event_bus import InMemoryEventBus
import asyncio
from backend.agents.base import BaseAgent
from backend.agents.city_overview import CityOverviewAgent
from backend.agents.preferences import PreferencesAgent
from backend.agents.attractions import AttractionsAgent
from backend.agents.transport import TransportationAgent
from backend.agents.budget import BudgetAgent
from backend.agents.gastronomy import GastronomyAgent
from backend.llm.factory import LLMFactory

class OrchestratorAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Orchestrator")

    async def run(self, user_input: UserInput) -> TripPlan:
        self.logger.info(f"Starting MAS planning for {user_input.destination}")

        model_name = "gemini-2.5-flash"
        if user_input.llm_settings and user_input.llm_settings.model:
             model_name = user_input.llm_settings.model

        if model_name.startswith("gpt") or model_name.startswith("o1"):
            provider_name = "openai"
        else:
            provider_name = "gemini"
        
        self.logger.info(f"Using LLM Provider: {provider_name}, Model: {model_name}")
        llm_provider = LLMFactory.create_provider(provider=provider_name)
        world = WorldState(user_input)
        bus = InMemoryEventBus()

        agent_classes = [
            PreferencesAgent,
            AttractionsAgent,
            GastronomyAgent,
            TransportationAgent,
            BudgetAgent,
            CityOverviewAgent
        ]

        all_possible_agents = [cls(llm_provider=llm_provider, model_name=model_name) for cls in agent_classes]
        
        tasks = [asyncio.create_task(agent.run(world, bus)) for agent in all_possible_agents]
        
        self.logger.info("Agents started. Waiting for completion...")
        try:
            await asyncio.wait_for(asyncio.gather(*tasks), timeout=60.0)
        except asyncio.TimeoutError:
            self.logger.error("Timed out waiting for agents. Dependency missing or LLM slow.")
        except Exception as e:
            self.logger.error(f"Error during agent execution: {e}")
        
        self.logger.info("Plan stable (or timed out). Stopping agents.")

        for t in tasks:
            if not t.done():
                t.cancel()

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for i, res in enumerate(results):
            if isinstance(res, Exception):
                self.logger.error(f"Agent task {i} failed with: {res}")

        self.logger.info("Generating final TripPlan.")
        
        final_snapshot = await world.get_snapshot()
        culinary = final_snapshot.get("culinary_section")
        mobility = final_snapshot.get("mobility_section")
        
        plan = TripPlan(
            destination=user_input.destination,
            total_cost=final_snapshot["total_cost"],
            days=final_snapshot["days"] or [],
            usage_stats=final_snapshot["token_usage"],
            metadata={"constraints": final_snapshot["constraints"]},
            culinary_section=culinary,
            mobility_section=mobility,
            city_overview=final_snapshot.get("city_overview")
        )
        plan.days = final_snapshot["days"] or []
        
        return plan
