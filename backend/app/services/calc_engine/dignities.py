"""Planetary dignities and combustion calculations."""

from typing import Dict, List, Tuple
from app.services.calc_engine.ephemeris import ephemeris_service
from app.utils.errors import CalculationError


class DignityService:
    """Service for planetary dignities and combustion."""
    
    def __init__(self):
        """Initialize dignity service."""
        # Exaltation signs and degrees
        self.exaltation_signs = {
            "Sun": 0,      # Aries
            "Moon": 3,      # Taurus
            "Mars": 9,      # Capricorn
            "Mercury": 5,   # Virgo
            "Jupiter": 3,   # Cancer
            "Venus": 0,     # Pisces
            "Saturn": 6     # Libra
        }
        
        # Debilitation signs
        self.debilitation_signs = {
            "Sun": 6,       # Libra
            "Moon": 8,      # Scorpio
            "Mars": 3,      # Cancer
            "Mercury": 8,   # Pisces
            "Jupiter": 8,   # Capricorn
            "Venus": 0,     # Virgo
            "Saturn": 0     # Aries
        }
        
        # Own signs (Mooltrikona and Swakshetra)
        self.own_signs = {
            "Sun": [4],           # Leo (Mooltrikona)
            "Moon": [3],          # Cancer (Mooltrikona)
            "Mars": [0, 7],       # Aries (Mooltrikona), Scorpio
            "Mercury": [2, 5],    # Gemini (Mooltrikona), Virgo
            "Jupiter": [8, 10],   # Sagittarius (Mooltrikona), Pisces
            "Venus": [1, 6],      # Taurus (Mooltrikona), Libra
            "Saturn": [9, 10]     # Capricorn (Mooltrikona), Aquarius
        }
        
        # Mooltrikona signs
        self.mooltrikona_signs = {
            "Sun": 4,       # Leo
            "Moon": 3,      # Cancer
            "Mars": 0,      # Aries
            "Mercury": 2,   # Gemini
            "Jupiter": 8,   # Sagittarius
            "Venus": 1,     # Taurus
            "Saturn": 9     # Capricorn
        }
        
        # Friendship relationships
        self.friendships = {
            "Sun": {"friends": ["Moon", "Mars", "Jupiter"], "enemies": ["Saturn", "Venus"], "neutral": ["Mercury"]},
            "Moon": {"friends": ["Sun", "Mercury"], "enemies": ["Mars", "Saturn", "Jupiter", "Venus"], "neutral": []},
            "Mars": {"friends": ["Sun", "Moon", "Jupiter"], "enemies": ["Mercury", "Venus", "Saturn"], "neutral": []},
            "Mercury": {"friends": ["Sun", "Venus"], "enemies": ["Moon"], "neutral": ["Mars", "Jupiter", "Saturn"]},
            "Jupiter": {"friends": ["Sun", "Moon", "Mars"], "enemies": ["Mercury", "Venus"], "neutral": ["Saturn"]},
            "Venus": {"friends": ["Mercury", "Saturn"], "enemies": ["Sun", "Moon", "Mars"], "neutral": ["Jupiter"]},
            "Saturn": {"friends": ["Mercury", "Venus"], "enemies": ["Sun", "Moon", "Mars"], "neutral": ["Jupiter"]}
        }
        
        # Combustion orbs (degrees)
        self.combustion_orbs = {
            "Sun": 0,       # Sun doesn't combust
            "Moon": 12,     # 12°
            "Mars": 17,     # 17°
            "Mercury": 12,  # 12°
            "Jupiter": 11,  # 11°
            "Venus": 10,    # 10°
            "Saturn": 15    # 15°
        }
    
    def get_dignity(self, planet_name: str, planet_sign: int) -> str:
        """Get dignity of a planet in a sign."""
        if planet_name not in self.exaltation_signs:
            return "Neutral"  # Rahu, Ketu
        
        # Check exaltation
        if planet_sign == self.exaltation_signs[planet_name]:
            return "Exalted"
        
        # Check debilitation
        if planet_sign == self.debilitation_signs[planet_name]:
            return "Debilitated"
        
        # Check Mooltrikona
        if planet_sign == self.mooltrikona_signs[planet_name]:
            return "Mooltrikona"
        
        # Check own signs
        if planet_sign in self.own_signs[planet_name]:
            return "Own"
        
        return "Neutral"
    
    def get_friendship(self, planet1: str, planet2: str) -> str:
        """Get friendship relationship between two planets."""
        if planet1 not in self.friendships or planet2 not in self.friendships:
            return "Neutral"
        
        relationships = self.friendships[planet1]
        
        if planet2 in relationships["friends"]:
            return "Friend"
        elif planet2 in relationships["enemies"]:
            return "Enemy"
        else:
            return "Neutral"
    
    def is_combust(self, planet_name: str, planet_longitude: float, sun_longitude: float) -> bool:
        """Check if a planet is combust."""
        if planet_name == "Sun":
            return False  # Sun doesn't combust
        
        if planet_name not in self.combustion_orbs:
            return False  # Rahu, Ketu don't combust
        
        # Calculate angular distance
        diff = abs(planet_longitude - sun_longitude)
        if diff > 180:
            diff = 360 - diff
        
        # Check if within combustion orb
        combustion_orb = self.combustion_orbs[planet_name]
        return diff <= combustion_orb
    
    def get_all_dignities(self, planet_positions: Dict) -> Dict[str, Dict]:
        """Get dignities for all planets."""
        dignities = {}
        
        for planet_name, planet_data in planet_positions.items():
            sign_num = planet_data["sign"]
            dignity = self.get_dignity(planet_name, sign_num)
            
            dignities[planet_name] = {
                "dignity": dignity,
                "sign": sign_num,
                "sign_name": self._get_sign_name(sign_num)
            }
        
        return dignities
    
    def get_all_combustion(self, planet_positions: Dict) -> Dict[str, bool]:
        """Get combustion status for all planets."""
        combustion = {}
        
        if "Sun" not in planet_positions:
            return combustion
        
        sun_longitude = planet_positions["Sun"]["longitude"]
        
        for planet_name, planet_data in planet_positions.items():
            planet_longitude = planet_data["longitude"]
            is_combust = self.is_combust(planet_name, planet_longitude, sun_longitude)
            combustion[planet_name] = is_combust
        
        return combustion
    
    def get_dignity_tier(self, dignity: str) -> int:
        """Get dignity tier for D9 comparison."""
        tier_map = {
            "Exalted": 5,
            "Own": 4,
            "Mooltrikona": 3,
            "Friend": 2,
            "Neutral": 1,
            "Enemy": 0,
            "Debilitated": -1
        }
        return tier_map.get(dignity, 1)
    
    def _get_sign_name(self, sign_num: int) -> str:
        """Get sign name from number."""
        sign_names = [
            "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
        ]
        return sign_names[sign_num]


# Global dignity service instance
dignity_service = DignityService()

