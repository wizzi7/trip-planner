import asyncio
from typing import Dict, Any, List
from backend.models import UserInput, TripDay

class WorldState:
    def __init__(self, user_input: UserInput):
        self.user_input = user_input
        self.constraints: Dict[str, Any] = {}
        self.days: List[TripDay] = []
        self.total_cost: float = 0.0

        self.lock = asyncio.Lock()

    async def get_snapshot(self) -> Dict[str, Any]:
        async with self.lock:
            return {
                "constraints": self.constraints.copy(),
                "days": [d.model_copy() for d in self.days],
                "total_cost": self.total_cost
            }
