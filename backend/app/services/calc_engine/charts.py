"""Chart calculations for D1 and D9."""

from typing import Dict, List
from app.services.calc_engine.ephemeris import ephemeris_service
from app.utils.errors import CalculationError


class ChartService:
    """Service for chart calculations (D1, D9)."""
    
    def __init__(self):
        """Initialize chart service."""
        self.sign_names = [
            "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
        ]
    
    def get_sign_name(self, sign_num: int) -> str:
        """Get sign name from sign number."""
        return self.sign_names[sign_num]
    
    def get_d1_chart(self, jd: float, lat: float, lon: float, ayanamsa: str = "Lahiri") -> Dict:
        """Get D1 (Rashi) chart data."""
        try:
            # Get ascendant
            ascendant = ephemeris_service.get_ascendant(jd, lat, lon, ayanamsa)
            
            # Get planet positions
            planet_positions = ephemeris_service.get_planet_positions(jd)
            
            # Get houses
            houses = ephemeris_service.get_houses(jd, lat, lon, "WholeSign")
            
            # Get planet-house mapping
            planet_houses = ephemeris_service.get_planet_house_positions(planet_positions, houses)
            
            # Format ascendant data
            ascendant_data = {
                "sign": self.get_sign_name(ascendant["sign"]),
                "degree": ascendant["degree_in_sign"],
                "longitude": ascendant["longitude"],
                "nakshatra": ephemeris_service.get_nakshatra_and_pada(ascendant["longitude"])[0],
                "pada": ephemeris_service.get_nakshatra_and_pada(ascendant["longitude"])[1]
            }
            
            # Format planet data
            planets_data = []
            for planet_name, planet_data in planet_positions.items():
                nakshatra, pada = ephemeris_service.get_nakshatra_and_pada(planet_data["longitude"])
                
                planets_data.append({
                    "name": planet_name,
                    "sign": self.get_sign_name(planet_data["sign"]),
                    "degree": planet_data["degree_in_sign"],
                    "longitude": planet_data["longitude"],
                    "nakshatra": nakshatra,
                    "pada": pada,
                    "retrograde": planet_data["retrograde"],
                    "house": planet_houses.get(planet_name, 1)
                })
            
            # Format house data
            houses_data = []
            for house_num, house_data in houses.items():
                houses_data.append({
                    "num": house_num,
                    "sign": self.get_sign_name(house_data["sign"]),
                    "cusp_degree": house_data.get("cusp_degree", 0.0)
                })
            
            return {
                "ascendant": ascendant_data,
                "planets": planets_data,
                "houses": houses_data
            }
            
        except Exception as e:
            raise CalculationError(f"Error calculating D1 chart: {str(e)}")
    
    def get_d9_chart(self, jd: float, lat: float, lon: float, ayanamsa: str = "Lahiri") -> Dict:
        """Get D9 (Navamsha) chart - signs only."""
        try:
            # Get D1 planet positions
            planet_positions = ephemeris_service.get_planet_positions(jd)
            
            # Calculate D9 positions (divide by 3°20' = 3.333...°)
            d9_division = 3.3333333333333335
            
            d9_planet_signs = {}
            d9_ascendant_sign = None
            
            for planet_name, planet_data in planet_positions.items():
                longitude = planet_data["longitude"]
                
                # Calculate D9 sign
                d9_longitude = longitude / d9_division
                d9_sign_num = int(d9_longitude) % 12
                
                d9_planet_signs[planet_name] = {
                    "sign": self.get_sign_name(d9_sign_num),
                    "sign_num": d9_sign_num
                }
            
            # Calculate D9 ascendant
            ascendant = ephemeris_service.get_ascendant(jd, lat, lon, ayanamsa)
            d9_asc_longitude = ascendant["longitude"] / d9_division
            d9_asc_sign_num = int(d9_asc_longitude) % 12
            
            d9_ascendant_sign = {
                "sign": self.get_sign_name(d9_asc_sign_num),
                "sign_num": d9_asc_sign_num
            }
            
            return {
                "ascendant": d9_ascendant_sign,
                "planet_signs": d9_planet_signs
            }
            
        except Exception as e:
            raise CalculationError(f"Error calculating D9 chart: {str(e)}")
    
    def get_house_lords(self, houses: Dict) -> Dict[int, str]:
        """Get lords of each house."""
        house_lords = {
            1: "Mars",      # Aries
            2: "Venus",     # Taurus
            3: "Mercury",   # Gemini
            4: "Moon",      # Cancer
            5: "Sun",       # Leo
            6: "Mercury",   # Virgo
            7: "Venus",     # Libra
            8: "Mars",      # Scorpio
            9: "Jupiter",   # Sagittarius
            10: "Saturn",   # Capricorn
            11: "Saturn",   # Aquarius
            12: "Jupiter"   # Pisces
        }
        
        lords = {}
        for house_num, house_data in houses.items():
            sign_num = house_data["sign"]
            lords[house_num] = house_lords[sign_num]
        
        return lords
    
    def get_planet_signs_dict(self, planet_positions: Dict) -> Dict[str, str]:
        """Get dictionary of planet names to sign names."""
        planet_signs = {}
        for planet_name, planet_data in planet_positions.items():
            planet_signs[planet_name] = self.get_sign_name(planet_data["sign"])
        
        return planet_signs


# Global chart service instance
chart_service = ChartService()

