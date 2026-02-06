from backend.agents.base import BaseAgent
from backend.models import CulinarySection
import os

class GastronomyAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="GastronomyAgent")
        custom_key = os.environ.get("GASTRONOMY_OPENROUTER_API_KEY")
        if custom_key:
            self.api_key = custom_key

    async def run(self, world: "WorldState", bus: "EventBus"):
        self.logger.info("Waiting for itinerary...")
        await bus.subscribe("days_planned")
        
        if os.environ.get("ENABLE_GASTRONOMY", "true").lower() == "false":
            self.logger.info("Gastronomy Agent disabled by ENABLE_GASTRONOMY flag.")
            async with world.lock:
                world.culinary_section = CulinarySection()
            await bus.emit("cost_updated")
            return

        async with world.lock:
            user_input = world.user_input

        self.logger.info("Finding culinary experiences...")

        system_prompt = (
            "You are an expert Culinary Guide and Food Critic. "
            "Your goal is to provide a single, comprehensive culinary guide for the entire trip destination. "
            "This guide is inspirational and NOT tied to specific days. "
            "Respect the user's budget. "
            "CRITICAL: For 'price_range', strictly use a numeric range with the LOCAL CURRENCY of the destination (e.g., '15-25 EUR', '30-50 PLN', '1500-2500 JPY'). Do NOT use terms like 'Low', 'Medium', 'High'. "
            "CRITICAL: You MUST provide at least SIX (6) distinct items for 'main_dishes'. Main dishes cannot be soups. These are hard requirements. "
            "For 'soups', 'desserts', and 'drinks', provide at 2 distinct items each. "
            "CRITICAL: For 'drinks', strictly use GENERAL CATEGORIES (e.g., 'Vodka', 'Local Beer', 'Fruit Compote') rather than specific brand names. "
            "CRITICAL: For every venue category (traditional, cafes, bars), you MUST provide at least FOUR (4) distinct venues. "
            "DO NOT BE LAZY. You will be penalized for providing fewer than 4 venues per category. "
            "Return a JSON object matching the following structure: "
            "{ "
            "  \"main_dishes\": [{\"name\": \"Dish Name\", \"description\": \"Description...\", \"price_range\": \"20-40 PLN\"}, ... (at least 6 items)], "
            "  \"soups\": [{\"name\": \"Soup Name\", \"description\": \"Description...\", \"price_range\": \"10-20 PLN\"}, ...], "
            "  \"desserts\": [{\"name\": \"Dessert Name\", \"description\": \"Description...\", \"price_range\": \"15-25 PLN\"}, ...], "
            "  \"drinks\": [{\"name\": \"Drink Category\", \"description\": \"Description...\", \"price_range\": \"15-30 PLN\"}, ...], "
            "  \"venues_traditional\": [{\"name\": \"Restaurant Name\", \"district\": \"Old Town\", \"type\": \"Traditional Polish\", \"price_range\": \"40-80 PLN\", \"signature_items\": \"Pierogi, Bigos\"}, ... (min 4 venues)], "
            "  \"venues_cafes\": [{\"name\": \"Cafe Name\", \"district\": \"City Center\", \"type\": \"Cafe\", \"price_range\": \"20-40 PLN\", \"signature_items\": \"Coffee, Cheesecake\"}, ... (min 4 venues)], "
            "  \"venues_bars\": [{\"name\": \"Bar Name\", \"district\": \"Praga\", \"type\": \"Craft Beer\", \"price_range\": \"20-30 PLN\", \"signature_items\": \"Local IPA, Stout\"}, ... (min 4 venues)] "
            "}"
        )

        user_prompt = (
            f"Destination: {user_input.destination}\n"
            f"Budget Per Person: {user_input.budget}\n"
            f"Dietary/Extra Requirements: {user_input.extra_req}\n"
            "Please provide a global culinary guide for this destination."
        )

        response_data, usage = self.call_openrouter(system_prompt, user_prompt, json_response=True, max_tokens=2600)
        
        async with world.lock:
             world.token_usage[self.name] = usage

        if response_data:
            self.logger.info(f"Raw Culinary Response: {response_data}")
            mapped_data = {}
            
            def normalize_list(raw_list):
                 if not isinstance(raw_list, list):
                     return raw_list
                 
                 normalized = []
                 for item in raw_list:
                    if isinstance(item, str):
                        normalized.append({"name": item, "description": "Local specialty", "price_range": "Ask locally"})
                    elif isinstance(item, dict):
                        if "specialty" in item and "signature_items" not in item:
                            item["signature_items"] = item["specialty"]

                        if "price_range" not in item:
                            if "price" in item:
                                item["price_range"] = item["price"]
                            elif "cost" in item:
                                item["price_range"] = item["cost"]
                            elif "estimated_cost" in item:
                                item["price_range"] = item["estimated_cost"]
                            elif "approx_price" in item:
                                item["price_range"] = item["approx_price"]
                            elif "average_price" in item:
                                item["price_range"] = item["average_price"]

                        if "signatures" in item and "signature_items" not in item:
                            item["signature_items"] = item["signatures"]
                        
                        normalized.append(item)
                    else:
                        normalized.append(item)
                 return normalized

            direct_keys = ["main_dishes", "soups", "desserts", "drinks", "venues_traditional", "venues_cafes", "venues_bars"]
            for k in direct_keys:
                if k in response_data:
                    mapped_data[k] = normalize_list(response_data[k])

            if "regional_items" in response_data:
                ri = response_data["regional_items"]
                if "Main Dishes" in ri: mapped_data["main_dishes"] = normalize_list(ri["Main Dishes"])
                if "Soups" in ri: mapped_data["soups"] = normalize_list(ri["Soups"])
                if "Desserts" in ri: mapped_data["desserts"] = normalize_list(ri["Desserts"])
                if "Drinks" in ri: mapped_data["drinks"] = normalize_list(ri["Drinks"])

            if "venues" in response_data:
                v = response_data["venues"]
                if "Traditional Cuisine" in v: mapped_data["venues_traditional"] = normalize_list(v["Traditional Cuisine"])
                if "Cafés & Desserts" in v: mapped_data["venues_cafes"] = normalize_list(v["Cafés & Desserts"])
                if "Wine & Bars" in v: mapped_data["venues_bars"] = normalize_list(v["Wine & Bars"])

            try:
                data_to_use = mapped_data if mapped_data else response_data
                self.logger.info(f"Using data for validation: {data_to_use.keys()}")
                
                culinary_section = CulinarySection(**data_to_use)
                async with world.lock:
                    world.culinary_section = culinary_section
                self.logger.info("Culinary section generated successfully.")
            except Exception as e:
                self.logger.error(f"Failed to parse culinary section: {e}")
                self.logger.error(f"Problematic data: {response_data}")
                async with world.lock:
                    world.culinary_section = CulinarySection()
        else:
             self.logger.warning("Failed to generate culinary section.")
             async with world.lock:
                world.culinary_section = CulinarySection()

        
        await bus.emit("cost_updated")
