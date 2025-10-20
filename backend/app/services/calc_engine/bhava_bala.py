"""Bhava Bala (house strength) calculations."""

from typing import Dict, List
from app.services.calc_engine.dignities import dignity_service
from app.services.calc_engine.aspects import aspect_service
from app.utils.errors import CalculationError


class BhavaBalaService:
    """Service for Bhava Bala (house strength) calculations."""
    
    def __init__(self):
        """Initialize Bhava Bala service."""
        self.malefic_planets = ["Mars", "Saturn", "Rahu", "Ketu"]
        self.benefic_planets = ["Jupiter", "Venus"]
    
    def calculate_bhava_bala(self, houses: Dict, planet_positions: Dict, 
                           planet_houses: Dict, aspects: List[Dict]) -> Dict:
        """Calculate Bhava Bala for all houses."""
        try:
            bhava_bala = {}
            
            for house_num in range(1, 13):
                strength = self._calculate_house_strength(
                    house_num, houses, planet_positions, planet_houses, aspects
                )
                bhava_bala[house_num] = strength
            
            return bhava_bala
            
        except Exception as e:
            raise CalculationError(f"Error calculating Bhava Bala: {str(e)}")
    
    def _calculate_house_strength(self, house_num: int, houses: Dict, 
                                planet_positions: Dict, planet_houses: Dict, 
                                aspects: List[Dict]) -> float:
        """Calculate strength for a specific house."""
        try:
            # Start with base strength
            strength = 0.50
            
            # Get house lord
            house_lord = self._get_house_lord(house_num, houses)
            if not house_lord:
                return strength
            
            # Get house lord's dignity
            if house_lord in planet_positions:
                lord_dignity = dignity_service.get_dignity(
                    house_lord, planet_positions[house_lord]["sign"]
                )
                
                # +0.15 if house lord dignity ≥ Friend AND NOT combust
                dignity_tier = dignity_service.get_dignity_tier(lord_dignity)
                is_combust = self._is_planet_combust(house_lord, planet_positions)
                
                if dignity_tier >= 2 and not is_combust:  # Friend tier = 2
                    strength += 0.15
                
                # -0.10 if house lord dignity ≤ Enemy OR combust
                if dignity_tier <= 0 or is_combust:  # Enemy tier = 0
                    strength -= 0.10
            
            # Check aspects to house lord
            lord_aspects = self._get_aspects_to_planet(house_lord, aspects)
            jupiter_or_venus_aspect = False
            
            for aspect in lord_aspects:
                if aspect["from"] in ["Jupiter", "Venus"]:
                    jupiter_or_venus_aspect = True
                    break
            
            # +0.10 if house lord aspected by Jupiter OR Venus
            if jupiter_or_venus_aspect:
                strength += 0.10
            
            # Count malefics in the house
            malefics_in_house = 0
            for planet_name, house_num_planet in planet_houses.items():
                if house_num_planet == house_num and planet_name in self.malefic_planets:
                    malefics_in_house += 1
            
            # -0.10 if ≥3 malefics occupy the house
            if malefics_in_house >= 3:
                strength -= 0.10
            
            # Clamp to [0.00, 1.00]
            strength = max(0.00, min(1.00, strength))
            
            return strength
            
        except Exception as e:
            raise CalculationError(f"Error calculating house {house_num} strength: {str(e)}")
    
    def _get_house_lord(self, house_num: int, houses: Dict) -> str:
        """Get lord of a specific house."""
        if house_num not in houses:
            return None
        
        house_sign = houses[house_num]["sign"]
        
        # House lords mapping
        house_lords = {
            0: "Mars",      # Aries
            1: "Venus",     # Taurus
            2: "Mercury",   # Gemini
            3: "Moon",      # Cancer
            4: "Sun",       # Leo
            5: "Mercury",   # Virgo
            6: "Venus",     # Libra
            7: "Mars",      # Scorpio
            8: "Jupiter",   # Sagittarius
            9: "Saturn",    # Capricorn
            10: "Saturn",   # Aquarius
            11: "Jupiter"   # Pisces
        }
        
        return house_lords.get(house_sign)
    
    def _is_planet_combust(self, planet_name: str, planet_positions: Dict) -> bool:
        """Check if a planet is combust."""
        if planet_name not in planet_positions or "Sun" not in planet_positions:
            return False
        
        planet_longitude = planet_positions[planet_name]["longitude"]
        sun_longitude = planet_positions["Sun"]["longitude"]
        
        return dignity_service.is_combust(planet_name, planet_longitude, sun_longitude)
    
    def _get_aspects_to_planet(self, planet_name: str, aspects: List[Dict]) -> List[Dict]:
        """Get all aspects to a specific planet."""
        planet_aspects = []
        
        for aspect in aspects:
            if aspect["to"] == planet_name:
                planet_aspects.append(aspect)
        
        return planet_aspects
    
    def get_house_strength_summary(self, bhava_bala: Dict) -> Dict:
        """Get summary of house strengths."""
        strengths = list(bhava_bala.values())
        
        return {
            "strongest_house": max(bhava_bala.items(), key=lambda x: x[1]),
            "weakest_house": min(bhava_bala.items(), key=lambda x: x[1]),
            "average_strength": sum(strengths) / len(strengths),
            "strong_houses": [house for house, strength in bhava_bala.items() if strength >= 0.7],
            "weak_houses": [house for house, strength in bhava_bala.items() if strength <= 0.3]
        }
    
    def get_career_house_strength(self, bhava_bala: Dict) -> Dict:
        """Get strength of career-related houses."""
        career_houses = {
            "2nd_house": 2,   # Wealth
            "6th_house": 6,   # Service/work
            "10th_house": 10, # Career/profession
            "11th_house": 11  # Gains/income
        }
        
        career_strength = {}
        for house_name, house_num in career_houses.items():
            career_strength[house_name] = {
                "strength": bhava_bala.get(house_num, 0.0),
                "status": "strong" if bhava_bala.get(house_num, 0.0) >= 0.7 else 
                         "moderate" if bhava_bala.get(house_num, 0.0) >= 0.5 else "weak"
            }
        
        return career_strength
    
    def get_marriage_house_strength(self, bhava_bala: Dict) -> Dict:
        """Get strength of marriage-related houses."""
        marriage_houses = {
            "7th_house": 7,   # Marriage/partnership
            "8th_house": 8,   # Longevity/marital happiness
            "12th_house": 12  # Bed pleasures
        }
        
        marriage_strength = {}
        for house_name, house_num in marriage_houses.items():
            marriage_strength[house_name] = {
                "strength": bhava_bala.get(house_num, 0.0),
                "status": "strong" if bhava_bala.get(house_num, 0.0) >= 0.7 else 
                         "moderate" if bhava_bala.get(house_num, 0.0) >= 0.5 else "weak"
            }
        
        return marriage_strength


# Global Bhava Bala service instance
bhavabala_service = BhavaBalaService()

