"""Transit calculations for major planets."""

from datetime import datetime
from typing import Dict, List
from app.services.calc_engine.ephemeris import ephemeris_service
from app.utils.errors import CalculationError


class TransitService:
    """Service for transit calculations."""
    
    def __init__(self):
        """Initialize transit service."""
        self.sign_names = [
            "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
        ]
    
    def get_current_transits(self, current_jd: float, natal_ascendant: int, 
                           natal_moon_sign: int) -> Dict:
        """Get current transits of major planets."""
        try:
            # Get current positions of Saturn, Jupiter, Rahu, Ketu
            current_positions = ephemeris_service.get_planet_positions(
                current_jd, ["Saturn", "Jupiter", "Rahu", "Ketu"]
            )
            
            transits = {}
            
            # Saturn transit
            saturn_sign = current_positions["Saturn"]["sign"]
            saturn_house_from_lagna = (saturn_sign - natal_ascendant) % 12 + 1
            saturn_house_from_moon = (saturn_sign - natal_moon_sign) % 12 + 1
            
            transits["saturn"] = {
                "sign": self.sign_names[saturn_sign],
                "sign_num": saturn_sign,
                "house_from_lagna": saturn_house_from_lagna,
                "house_from_moon": saturn_house_from_moon
            }
            
            # Jupiter transit
            jupiter_sign = current_positions["Jupiter"]["sign"]
            jupiter_house_from_lagna = (jupiter_sign - natal_ascendant) % 12 + 1
            jupiter_house_from_moon = (jupiter_sign - natal_moon_sign) % 12 + 1
            
            transits["jupiter"] = {
                "sign": self.sign_names[jupiter_sign],
                "sign_num": jupiter_sign,
                "house_from_lagna": jupiter_house_from_lagna,
                "house_from_moon": jupiter_house_from_moon
            }
            
            # Rahu-Ketu axis
            rahu_sign = current_positions["Rahu"]["sign"]
            ketu_sign = (rahu_sign + 6) % 12  # Ketu is 180° from Rahu
            
            rahu_house_from_lagna = (rahu_sign - natal_ascendant) % 12 + 1
            ketu_house_from_lagna = (ketu_sign - natal_ascendant) % 12 + 1
            
            transits["rahu_ketu"] = {
                "rahu_sign": self.sign_names[rahu_sign],
                "rahu_sign_num": rahu_sign,
                "ketu_sign": self.sign_names[ketu_sign],
                "ketu_sign_num": ketu_sign,
                "rahu_house_from_lagna": rahu_house_from_lagna,
                "ketu_house_from_lagna": ketu_house_from_lagna,
                "axis_houses_from_lagna": [rahu_house_from_lagna, ketu_house_from_lagna]
            }
            
            return transits
            
        except Exception as e:
            raise CalculationError(f"Error calculating transits: {str(e)}")
    
    def get_sade_sati_phase(self, saturn_house_from_moon: int) -> str:
        """Determine Sade Sati phase based on Saturn's position from Moon."""
        if saturn_house_from_moon in [12, 1, 2]:
            return "active"
        elif saturn_house_from_moon in [11, 3]:
            return "approaching"
        elif saturn_house_from_moon in [9, 4]:
            return "receding"
        else:
            return "none"
    
    def get_transit_summary(self, current_jd: float, natal_ascendant: int, 
                           natal_moon_sign: int) -> Dict:
        """Get comprehensive transit summary."""
        try:
            transits = self.get_current_transits(current_jd, natal_ascendant, natal_moon_sign)
            
            # Add Sade Sati information
            sade_sati_phase = self.get_sade_sati_phase(transits["saturn"]["house_from_moon"])
            
            return {
                "saturn_house_from_lagna": transits["saturn"]["house_from_lagna"],
                "jupiter_house_from_lagna": transits["jupiter"]["house_from_lagna"],
                "rahu_ketu_axis_from_lagna": transits["rahu_ketu"]["axis_houses_from_lagna"],
                "sade_sati_phase": sade_sati_phase,
                "jupiter_house_from_moon": transits["jupiter"]["house_from_moon"],
                "saturn_house_from_moon": transits["saturn"]["house_from_moon"],
                "detailed_transits": transits
            }
            
        except Exception as e:
            raise CalculationError(f"Error calculating transit summary: {str(e)}")


# Global transit service instance
transit_service = TransitService()

