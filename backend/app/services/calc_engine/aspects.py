"""Parashari aspects calculations."""

from typing import Dict, List, Tuple
from app.services.calc_engine.ephemeris import ephemeris_service
from app.utils.errors import CalculationError


class AspectService:
    """Service for Parashari aspects calculations."""
    
    def __init__(self):
        """Initialize aspect service."""
        # Aspect definitions
        self.aspects = {
            "Sun": [7],           # 7th aspect only
            "Moon": [7],          # 7th aspect only
            "Mars": [4, 7, 8],    # 4th, 7th, 8th aspects
            "Mercury": [7],       # 7th aspect only
            "Jupiter": [5, 7, 9], # 5th, 7th, 9th aspects
            "Venus": [7],         # 7th aspect only
            "Saturn": [3, 7, 10], # 3rd, 7th, 10th aspects
            "Rahu": [7],          # 7th aspect only
            "Ketu": [7]           # 7th aspect only
        }
        
        # Orb allowances (degrees)
        self.aspect_orbs = {
            "Sun": 7,      # 7°
            "Moon": 7,     # 7°
            "Mars": 8,     # 8°
            "Mercury": 7,  # 7°
            "Jupiter": 9,  # 9°
            "Venus": 7,    # 7°
            "Saturn": 9,   # 9°
            "Rahu": 7,     # 7°
            "Ketu": 7      # 7°
        }
    
    def calculate_aspect_distance(self, from_longitude: float, to_longitude: float, aspect_type: int) -> float:
        """Calculate distance for a specific aspect."""
        # Calculate angular distance
        diff = to_longitude - from_longitude
        if diff < 0:
            diff += 360
        
        # Calculate expected distance for aspect
        expected_distance = (aspect_type - 1) * 30  # Each aspect is 30° apart
        
        # Calculate actual distance
        actual_distance = abs(diff - expected_distance)
        if actual_distance > 180:
            actual_distance = 360 - actual_distance
        
        return actual_distance
    
    def is_aspect_applicable(self, from_planet: str, aspect_type: int) -> bool:
        """Check if a planet can cast a specific aspect."""
        if from_planet not in self.aspects:
            return False
        
        return aspect_type in self.aspects[from_planet]
    
    def get_aspect_strength(self, orb: float, max_orb: float) -> float:
        """Calculate aspect strength based on orb (0.0 to 1.0)."""
        if orb > max_orb:
            return 0.0
        
        # Linear strength calculation
        strength = 1.0 - (orb / max_orb)
        return max(0.0, min(1.0, strength))
    
    def get_planet_aspects(self, from_planet: str, from_longitude: float, 
                          all_planets: Dict, houses: Dict) -> List[Dict]:
        """Get all aspects cast by a planet."""
        aspects = []
        
        if from_planet not in self.aspects:
            return aspects
        
        max_orb = self.aspect_orbs.get(from_planet, 7)
        
        # Check aspects to other planets
        for to_planet, to_data in all_planets.items():
            if from_planet == to_planet:
                continue
            
            to_longitude = to_data["longitude"]
            
            for aspect_type in self.aspects[from_planet]:
                orb = self.calculate_aspect_distance(from_longitude, to_longitude, aspect_type)
                
                if orb <= max_orb:
                    strength = self.get_aspect_strength(orb, max_orb)
                    
                    aspects.append({
                        "from": from_planet,
                        "to": to_planet,
                        "type": f"{aspect_type}th",
                        "orb_deg": orb,
                        "strength": strength
                    })
        
        # Check aspects to houses
        for house_num, house_data in houses.items():
            house_longitude = house_data["sign"] * 30 + house_data.get("cusp_degree", 0)
            
            for aspect_type in self.aspects[from_planet]:
                orb = self.calculate_aspect_distance(from_longitude, house_longitude, aspect_type)
                
                if orb <= max_orb:
                    strength = self.get_aspect_strength(orb, max_orb)
                    
                    aspects.append({
                        "from": from_planet,
                        "to": f"House {house_num}",
                        "type": f"{aspect_type}th",
                        "orb_deg": orb,
                        "strength": strength
                    })
        
        return aspects
    
    def get_all_aspects(self, planet_positions: Dict, houses: Dict) -> List[Dict]:
        """Get all aspects in the chart."""
        all_aspects = []
        
        for planet_name, planet_data in planet_positions.items():
            planet_longitude = planet_data["longitude"]
            planet_aspects = self.get_planet_aspects(
                planet_name, planet_longitude, planet_positions, houses
            )
            all_aspects.extend(planet_aspects)
        
        return all_aspects
    
    def get_aspects_to_house(self, house_num: int, planet_positions: Dict, houses: Dict) -> List[Dict]:
        """Get all aspects to a specific house."""
        aspects_to_house = []
        
        if house_num not in houses:
            return aspects_to_house
        
        house_data = houses[house_num]
        house_longitude = house_data["sign"] * 30 + house_data.get("cusp_degree", 0)
        
        for planet_name, planet_data in planet_positions.items():
            planet_longitude = planet_data["longitude"]
            
            if planet_name not in self.aspects:
                continue
            
            max_orb = self.aspect_orbs.get(planet_name, 7)
            
            for aspect_type in self.aspects[planet_name]:
                orb = self.calculate_aspect_distance(planet_longitude, house_longitude, aspect_type)
                
                if orb <= max_orb:
                    strength = self.get_aspect_strength(orb, max_orb)
                    
                    aspects_to_house.append({
                        "from": planet_name,
                        "to": f"House {house_num}",
                        "type": f"{aspect_type}th",
                        "orb_deg": orb,
                        "strength": strength
                    })
        
        return aspects_to_house
    
    def get_aspects_between_planets(self, planet1: str, planet2: str, 
                                  planet_positions: Dict) -> List[Dict]:
        """Get aspects between two specific planets."""
        aspects_between = []
        
        if planet1 not in planet_positions or planet2 not in planet_positions:
            return aspects_between
        
        planet1_data = planet_positions[planet1]
        planet2_data = planet_positions[planet2]
        
        planet1_longitude = planet1_data["longitude"]
        planet2_longitude = planet2_data["longitude"]
        
        # Check aspects from planet1 to planet2
        if planet1 in self.aspects:
            max_orb = self.aspect_orbs.get(planet1, 7)
            
            for aspect_type in self.aspects[planet1]:
                orb = self.calculate_aspect_distance(planet1_longitude, planet2_longitude, aspect_type)
                
                if orb <= max_orb:
                    strength = self.get_aspect_strength(orb, max_orb)
                    
                    aspects_between.append({
                        "from": planet1,
                        "to": planet2,
                        "type": f"{aspect_type}th",
                        "orb_deg": orb,
                        "strength": strength
                    })
        
        # Check aspects from planet2 to planet1
        if planet2 in self.aspects:
            max_orb = self.aspect_orbs.get(planet2, 7)
            
            for aspect_type in self.aspects[planet2]:
                orb = self.calculate_aspect_distance(planet2_longitude, planet1_longitude, aspect_type)
                
                if orb <= max_orb:
                    strength = self.get_aspect_strength(orb, max_orb)
                    
                    aspects_between.append({
                        "from": planet2,
                        "to": planet1,
                        "type": f"{aspect_type}th",
                        "orb_deg": orb,
                        "strength": strength
                    })
        
        return aspects_between


# Global aspect service instance
aspect_service = AspectService()

