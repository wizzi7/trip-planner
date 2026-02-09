import asyncio
from typing import Dict, Any, List, Optional
from backend.models import UserInput, TripDay, CulinarySection, MobilitySection

class WorldState:
    def __init__(self, user_input: UserInput):
        self.user_input = user_input
        self.constraints: Dict[str, Any] = {}
        self.days: Optional[List[TripDay]] = None
        self.total_cost: float = 0.0
        self.culinary_section: Optional[CulinarySection] = None
        self.mobility_section: Optional[MobilitySection] = None
        self.token_usage: Dict[str, Any] = {}
        self.city_overview: Optional[Any] = None
        
        self.lock = asyncio.Lock()

    async def get_snapshot(self) -> Dict[str, Any]:
        async with self.lock:
            return {
                "constraints": self.constraints.copy(),
                "days": [d.model_copy() for d in self.days] if self.days is not None else [],
                "total_cost": self.total_cost,
                "culinary_section": self.culinary_section.model_copy() if self.culinary_section else None,
                "mobility_section": self.mobility_section.model_copy() if self.mobility_section else None,
                "city_overview": self.city_overview.model_copy() if self.city_overview else None,
                "token_usage": self.token_usage.copy()
            }
