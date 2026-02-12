from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class LLMSettings(BaseModel):
    provider: str = "gemini"
    model: str = "gemini-2.5-flash"
    temperature: float = 0.7
    max_tokens: int = 2000

class UserInput(BaseModel):
    destination: str
    arrival: str
    departure: str
    guests: int
    budget: float
    pace: str
    transport: List[str]
    accommodation: Optional[str] = None
    interests: List[str] = Field(default_factory=list)
    extra_req: Optional[str] = None
    llm_settings: Optional[LLMSettings] = None
    active_agents: List[str] = Field(default_factory=lambda: ["PreferencesAgent", "AttractionsAgent", "GastronomyAgent", "TransportationAgent", "BudgetAgent", "CityOverviewAgent"])

class Activity(BaseModel):
    time: Optional[str] = Field(None, description="Estimated visiting time (optional)")
    name: str = Field(..., description="Name of the attraction")
    description: str = Field(..., description="Brief one-sentence explanation")
    duration: str = Field(..., description="Duration string, e.g. '1.5h'")

class TripDay(BaseModel):
    day: int
    date: str
    theme: str
    summary: str
    activities: List[Activity]
    estimated_cost: str

class CulinaryDish(BaseModel):
    name: str = "Unknown Dish"
    description: str = "No description available."
    price_range: str = "N/A"

class CulinaryVenue(BaseModel):
    name: str = "Unknown Venue"
    price_range: str = "N/A"
    type: Optional[str] = "Local"
    signature_items: Optional[str] = "Various options"
    district: str = "City Center"

class CulinarySection(BaseModel):
    main_dishes: List[CulinaryDish] = Field(default_factory=list)
    soups: List[CulinaryDish] = Field(default_factory=list)
    desserts: List[CulinaryDish] = Field(default_factory=list)
    drinks: List[CulinaryDish] = Field(default_factory=list)
    venues_traditional: List[CulinaryVenue] = Field(default_factory=list)
    venues_cafes: List[CulinaryVenue] = Field(default_factory=list)
    venues_bars: List[CulinaryVenue] = Field(default_factory=list)

class MobilityOption(BaseModel):
    name: str
    description: str
    price_level: str
    typical_price: Optional[str] = "N/A"
    convenience: Optional[str] = "Moderate"

class MobilitySystem(BaseModel):
    available_options: List[str]
    ticket_types: str
    approximate_prices: str
    coverage_quality: str
    useful_apps: List[str]
    best_use_cases: str
    price_level: str
    website_url: Optional[str] = None

class RideHailing(BaseModel):
    available_apps: List[str]
    typical_pricing_level: str
    safety_notes: str
    when_to_use: str

class WalkingGuide(BaseModel):
    is_walkable: bool
    best_areas: List[str]

class BikeScooter(BaseModel):
    available: bool
    providers: List[str]
    price_range: str
    convenience: str
    cautions: List[str]

class FerryBoat(BaseModel):
    is_relevant: bool
    routes: str = ""
    cost_level: str = ""
    tourist_vs_commuter: str = ""

class CarRental(BaseModel):
    recommended: bool
    parking_difficulty: str
    notes: str

class QuickRecommendations(BaseModel):
    best_overall: str
    cheapest: str
    most_convenient: str
    avoid: List[str]

class MobilitySection(BaseModel):
    public_transport: Optional[MobilitySystem] = None
    taxis: Optional[RideHailing] = None
    walking: Optional[WalkingGuide] = None
    bikes: Optional[BikeScooter] = None
    ferries: Optional[FerryBoat] = None
    car_rental: Optional[CarRental] = None
    quick_recommendations: Optional[QuickRecommendations] = None

class UsageStats(BaseModel):
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost: float
    model: str

class CityOverview(BaseModel):
    city_name: str
    short_description: str
    history_summary: str
    cultural_identity: str

class TripPlan(BaseModel):
    destination: str
    total_cost: float
    days: List[TripDay]
    usage_stats: Dict[str, UsageStats] = Field(default_factory=dict)
    culinary_section: Optional[CulinarySection] = None
    mobility_section: Optional[MobilitySection] = None
    city_overview: Optional[CityOverview] = None
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata from agents (e.g. constraints)")

class UpdateRequest(BaseModel):
    current_plan: TripPlan
    feedback: str
    user_input: UserInput
