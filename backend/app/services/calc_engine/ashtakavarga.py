"""Ashtakavarga (SAV) calculations."""

from typing import Dict, List
from app.services.calc_engine.ephemeris import ephemeris_service
from app.utils.errors import CalculationError


class AshtakavargaService:
    """Service for Ashtakavarga (SAV) calculations."""
    
    def __init__(self):
        """Initialize Ashtakavarga service."""
        # SAV bindus for each planet in each sign
        # Format: planet -> [sign0, sign1, ..., sign11]
        self.sav_bindus = {
            "Sun": [6, 5, 5, 6, 5, 5, 6, 5, 5, 6, 5, 5],
            "Moon": [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            "Mars": [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            "Mercury": [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            "Jupiter": [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            "Venus": [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            "Saturn": [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5]
        }
        
        # Sign names for reference
        self.sign_names = [
            "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
        ]
    
    def calculate_sav(self, planet_positions: Dict) -> Dict:
        """Calculate Sarvashtakavarga (SAV) for all signs."""
        try:
            # Initialize SAV array (12 signs)
            sav = [0] * 12
            
            # Calculate SAV for each planet
            for planet_name, planet_data in planet_positions.items():
                if planet_name not in self.sav_bindus:
                    continue  # Skip Rahu, Ketu
                
                planet_sign = planet_data["sign"]
                planet_bindus = self.sav_bindus[planet_name]
                
                # Add bindus for each sign
                for sign_num in range(12):
                    # Calculate relative position from planet's sign
                    relative_sign = (sign_num - planet_sign) % 12
                    bindu_value = planet_bindus[relative_sign]
                    sav[sign_num] += bindu_value
            
            # Create detailed SAV data
            sav_data = {
                "sav_values": sav,
                "sav_good_threshold": 30,
                "good_signs": [i for i, value in enumerate(sav) if value >= 30],
                "poor_signs": [i for i, value in enumerate(sav) if value < 30],
                "sign_details": []
            }
            
            # Add sign-wise details
            for sign_num, value in enumerate(sav):
                sav_data["sign_details"].append({
                    "sign": self.sign_names[sign_num],
                    "sign_num": sign_num,
                    "sav_value": value,
                    "status": "good" if value >= 30 else "poor"
                })
            
            return sav_data
            
        except Exception as e:
            raise CalculationError(f"Error calculating SAV: {str(e)}")
    
    def get_house_sav_strength(self, house_num: int, sav_data: Dict) -> int:
        """Get SAV strength for a specific house."""
        if house_num < 1 or house_num > 12:
            return 0
        
        sign_num = house_num - 1  # Houses 1-12 map to signs 0-11
        return sav_data["sav_values"][sign_num]
    
    def is_house_sav_good(self, house_num: int, sav_data: Dict, threshold: int = 30) -> bool:
        """Check if a house has good SAV strength."""
        sav_value = self.get_house_sav_strength(house_num, sav_data)
        return sav_value >= threshold
    
    def get_sav_summary(self, sav_data: Dict) -> Dict:
        """Get SAV summary statistics."""
        sav_values = sav_data["sav_values"]
        
        return {
            "total_sav": sum(sav_values),
            "average_sav": sum(sav_values) / len(sav_values),
            "max_sav": max(sav_values),
            "min_sav": min(sav_values),
            "good_signs_count": len(sav_data["good_signs"]),
            "poor_signs_count": len(sav_data["poor_signs"]),
            "strongest_sign": sav_data["sign_details"][sav_values.index(max(sav_values))]["sign"],
            "weakest_sign": sav_data["sign_details"][sav_values.index(min(sav_values))]["sign"]
        }
    
    def get_career_sav_strength(self, sav_data: Dict) -> Dict:
        """Get SAV strength for career-related houses."""
        career_houses = {
            "2nd_house": 2,   # Wealth
            "6th_house": 6,   # Service/work
            "10th_house": 10, # Career/profession
            "11th_house": 11  # Gains/income
        }
        
        career_sav = {}
        for house_name, house_num in career_houses.items():
            career_sav[house_name] = {
                "sav_value": self.get_house_sav_strength(house_num, sav_data),
                "is_good": self.is_house_sav_good(house_num, sav_data)
            }
        
        return career_sav
    
    def get_marriage_sav_strength(self, sav_data: Dict) -> Dict:
        """Get SAV strength for marriage-related houses."""
        marriage_houses = {
            "7th_house": 7,   # Marriage/partnership
            "8th_house": 8,   # Longevity/marital happiness
            "12th_house": 12  # Bed pleasures
        }
        
        marriage_sav = {}
        for house_name, house_num in marriage_houses.items():
            marriage_sav[house_name] = {
                "sav_value": self.get_house_sav_strength(house_num, sav_data),
                "is_good": self.is_house_sav_good(house_num, sav_data)
            }
        
        return marriage_sav


# Global Ashtakavarga service instance
ashtakavarga_service = AshtakavargaService()

