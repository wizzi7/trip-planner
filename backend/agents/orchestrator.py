from backend.models import UserInput, TripPlan
from backend.world_state import WorldState
from backend.event_bus import InMemoryEventBus
import asyncio
from backend.agents.base import BaseAgent
from backend.agents.preferences import PreferencesAgent
from backend.agents.attractions import AttractionsAgent
from backend.agents.transport import TransportationAgent
from backend.agents.budget import BudgetAgent
from backend.agents.gastronomy import GastronomyAgent

class OrchestratorAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Orchestrator")
        self.preferences_agent = PreferencesAgent()
        self.attractions_agent = AttractionsAgent()
        self.gastronomy_agent = GastronomyAgent()
        self.transport_agent = TransportationAgent()
        self.budget_agent = BudgetAgent()

    async def run(self, user_input: UserInput) -> TripPlan:
        self.logger.info(f"Starting MAS planning for {user_input.destination}")
        
        world = WorldState(user_input)
        bus = InMemoryEventBus()
        
        agents = [
            self.preferences_agent,
            self.attractions_agent,
            self.gastronomy_agent,
            self.transport_agent,
            self.budget_agent
        ]
        
        tasks = [asyncio.create_task(agent.run(world, bus)) for agent in agents]
        
        self.logger.info("Agents started. Waiting for plan stability...")
        await bus.subscribe("plan_stable")
        
        self.logger.info("Plan stable. Stopping agents.")

        for t in tasks:
            if not t.done():
                t.cancel()

        await asyncio.gather(*tasks, return_exceptions=True)
        
        self.logger.info("Generating final TripPlan.")
        
        final_snapshot = await world.get_snapshot()
        plan = TripPlan(
            destination=user_input.destination,
            total_cost=final_snapshot["total_cost"],
            days=final_snapshot["days"],
            usage_stats=final_snapshot["token_usage"],
            metadata={"constraints": final_snapshot["constraints"]},
            culinary_section=final_snapshot.get("culinary_section", None),
            mobility_section=final_snapshot.get("mobility_section", None)
        )
        plan.days = final_snapshot["days"] 
        
        return plan
