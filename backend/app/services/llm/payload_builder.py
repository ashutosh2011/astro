"""Payload builder for LLM requests."""

import logging
from typing import Dict, Any, List
from app.services.calc_engine.orchestrator import calc_orchestrator
from app.services.calc_engine.dignities import dignity_service
from app.services.calc_engine.ashtakavarga import ashtakavarga_service
from app.services.calc_engine.bhava_bala import bhavabala_service

logger = logging.getLogger(__name__)


class PayloadBuilder:
    """Builder for LLM payloads with topic-specific context."""
    
    def __init__(self):
        """Initialize payload builder."""
        pass
    
    def build_payload(self, user_profile: Dict, calc_snapshot: Dict, 
                     question: str, topic: str, conversation_context: List[Dict] = None, 
                     time_horizon_months: int = 12) -> Dict:
        """Build complete payload for LLM."""
        try:
            # Get calc summary with error handling
            try:
                calc_summary = calc_orchestrator.get_calc_summary(calc_snapshot)
            except Exception as e:
                logger.error(f"Failed to get calc summary: {str(e)}", exc_info=True)
                # If calc summary fails, create a minimal summary
                calc_summary = {
                    "ascendant": {"sign": "Unknown", "degree": 0},
                    "d1": {"planets": [], "houses": [], "aspects": []},
                    "d9": {"asc_sign": "Unknown", "planet_signs": {}, "d9_better": {}},
                    "yogas": [],
                    "bhava_bala": [],
                    "timing": {"current_md": "Unknown", "current_ad": "Unknown", "next_12m_ads": []},
                    "transits_now": {"saturn_house_from_lagna": 0, "jupiter_house_from_lagna": 0, "rahu_ketu_axis_from_lagna": [0, 0], "sade_sati_phase": "none"},
                    "sav": {},
                    "sensitivity": None
                }
                logger.warning(f"Using minimal calc summary due to error: {str(e)}")
            
            # Base payload
            payload = {
                "user_profile": {
                    "name": user_profile.get("name", ""),
                    "gender": user_profile.get("gender", ""),
                    "tz": user_profile.get("tz", ""),
                    "place": user_profile.get("place", "")
                },
                "calc_summary": calc_summary,
                "conversation_context": conversation_context or [],
                "question": question,
                "topic": topic,
                "time_horizon": {"months_min": 3, "months_max": time_horizon_months},
                "style_constraints": {
                    "no_remedies": True,
                    "no_fatalism": True,
                    "show_evidence": True,
                    "use_time_windows": True,
                    "brevity_target_tokens": 350
                }
            }
            
            # Add topic-specific clues
            try:
                if topic == "marriage":
                    payload["marriage_indicators"] = self._get_marriage_indicators(calc_snapshot)
                elif topic == "career":
                    payload["career_clues"] = self._get_career_clues(calc_snapshot)
                elif topic == "health":
                    payload["health_clues"] = self._get_health_clues(calc_snapshot)
            except Exception as e:
                logger.warning(f"Could not add topic-specific clues for {topic}: {str(e)}", exc_info=True)
            
            return payload
            
        except Exception as e:
            raise Exception(f"Error building payload: {str(e)}")
    
    def _get_marriage_indicators(self, calc_snapshot: Dict) -> Dict:
        """Get marriage-related indicators."""
        try:
            d1 = calc_snapshot["d1"]
            d9 = calc_snapshot["d9"]
            yogas = calc_snapshot["yogas"]
            transits = calc_snapshot["transits"]
            
            # Get 7th house lord
            seventh_lord = self._get_house_lord(7, d1["houses"])
            seventh_lord_sign = self._get_house_sign(7, d1["houses"])
            seventh_lord_dignity = self._get_planet_dignity(seventh_lord, calc_snapshot["dignities"])
            
            # Get Venus info
            venus_info = self._get_planet_info("Venus", d1["planets"], calc_snapshot["dignities"])
            
            # Get D9 info
            d9_asc_sign = d9["ascendant"]["sign"]
            d9_venus_sign = d9["planet_signs"].get("Venus", "Unknown")
            
            # Check Manglik status
            manglik_strict = any(yoga["name"] == "Manglik (Strict)" and yoga["present"] for yoga in yogas)
            manglik_lenient = any(yoga["name"] == "Manglik (Lenient)" and yoga["present"] for yoga in yogas)
            
            return {
                "seventh_lord": seventh_lord,
                "seventh_lord_sign": seventh_lord_sign,
                "seventh_lord_dignity": seventh_lord_dignity,
                "venus_sign": venus_info["sign"],
                "venus_dignity": venus_info["dignity"],
                "d9_asc_sign": d9_asc_sign,
                "d9_venus_sign": d9_venus_sign,
                "manglik_status_strict": manglik_strict,
                "manglik_status_lenient": manglik_lenient
            }
            
        except Exception as e:
            return {"error": f"Could not get marriage indicators: {str(e)}"}
    
    def _get_career_clues(self, calc_snapshot: Dict) -> Dict:
        """Get career-related clues."""
        try:
            d1 = calc_snapshot["d1"]
            yogas = calc_snapshot["yogas"]
            transits = calc_snapshot["transits"]
            
            # Get house lords
            tenth_lord = self._get_house_lord(10, d1["houses"])
            tenth_lord_sign = self._get_house_sign(10, d1["houses"])
            tenth_lord_dignity = self._get_planet_dignity(tenth_lord, calc_snapshot["dignities"])
            
            second_lord = self._get_house_lord(2, d1["houses"])
            eleventh_lord = self._get_house_lord(11, d1["houses"])
            
            # Get career yogas
            career_yogas = [yoga["name"] for yoga in yogas if yoga["present"] and 
                           any(keyword in yoga["name"].lower() for keyword in ["raj", "pancha", "dhana"])]
            
            # Get transit info
            jupiter_transit_house = transits["jupiter_house_from_lagna"]
            saturn_transit_house = transits["saturn_house_from_lagna"]
            
            return {
                "tenth_lord": tenth_lord,
                "tenth_lord_sign": tenth_lord_sign,
                "tenth_lord_dignity": tenth_lord_dignity,
                "second_lord": second_lord,
                "eleventh_lord": eleventh_lord,
                "career_yogas_present": career_yogas,
                "jupiter_transit_house_from_lagna": jupiter_transit_house,
                "saturn_transit_house_from_lagna": saturn_transit_house
            }
            
        except Exception as e:
            return {"error": f"Could not get career clues: {str(e)}"}
    
    def _get_health_clues(self, calc_snapshot: Dict) -> Dict:
        """Get health-related clues."""
        try:
            d1 = calc_snapshot["d1"]
            transits = calc_snapshot["transits"]
            
            # Get house lords
            sixth_lord = self._get_house_lord(6, d1["houses"])
            sixth_lord_sign = self._get_house_sign(6, d1["houses"])
            sixth_lord_dignity = self._get_planet_dignity(sixth_lord, calc_snapshot["dignities"])
            
            eighth_lord = self._get_house_lord(8, d1["houses"])
            twelfth_lord = self._get_house_lord(12, d1["houses"])
            
            # Get Saturn transit from Moon
            saturn_transit_from_moon = transits["saturn_house_from_moon"]
            
            # Check Mars-Moon relationship
            mars_moon_relation = self._get_mars_moon_relation(d1["planets"])
            
            # Get vitality hint (Sun-Lagna separation)
            sun_lagna_separation = self._get_sun_lagna_separation(d1["planets"], d1["ascendant"])
            
            return {
                "sixth_lord": sixth_lord,
                "sixth_lord_sign": sixth_lord_sign,
                "sixth_lord_dignity": sixth_lord_dignity,
                "eighth_lord": eighth_lord,
                "twelfth_lord": twelfth_lord,
                "saturn_transit_from_moon": saturn_transit_from_moon,
                "mars_moon_relation": mars_moon_relation,
                "vitality_hint": {"sun_lagna_separation_deg": sun_lagna_separation}
            }
            
        except Exception as e:
            return {"error": f"Could not get health clues: {str(e)}"}
    
    def _get_house_lord(self, house_num: int, houses: List[Dict]) -> str:
        """Get lord of a house based on the sign occupying that house."""
        # Sign-to-ruler mapping based on Vedic astrology
        sign_rulers = {
            "Aries": "Mars",
            "Taurus": "Venus",
            "Gemini": "Mercury",
            "Cancer": "Moon",
            "Leo": "Sun",
            "Virgo": "Mercury",
            "Libra": "Venus",
            "Scorpio": "Mars",
            "Sagittarius": "Jupiter",
            "Capricorn": "Saturn",
            "Aquarius": "Saturn",
            "Pisces": "Jupiter"
        }
        
        # Find the house and get its sign
        for house in houses:
            if house.get("num") == house_num:
                sign = house.get("sign", "")
                return sign_rulers.get(sign, "Unknown")
        
        return "Unknown"
    
    def _get_house_sign(self, house_num: int, houses: List[Dict]) -> str:
        """Get sign of a house."""
        for house in houses:
            if house["num"] == house_num:
                return house["sign"]
        return "Unknown"
    
    def _get_planet_dignity(self, planet: str, dignities: Dict) -> str:
        """Get dignity of a planet."""
        return dignities.get(planet, {}).get("dignity", "Neutral")
    
    def _get_planet_info(self, planet: str, planets: List[Dict], dignities: Dict) -> Dict:
        """Get planet information."""
        for p in planets:
            if p["name"] == planet:
                return {
                    "sign": p["sign"],
                    "dignity": dignities.get(planet, {}).get("dignity", "Neutral")
                }
        return {"sign": "Unknown", "dignity": "Neutral"}
    
    def _get_mars_moon_relation(self, planets: List[Dict]) -> str:
        """Get Mars-Moon relationship."""
        mars_house = None
        moon_house = None
        
        for planet in planets:
            if planet["name"] == "Mars":
                mars_house = planet["house"]
            elif planet["name"] == "Moon":
                moon_house = planet["house"]
        
        if mars_house and moon_house:
            if mars_house == moon_house:
                return "conjunction"
            elif abs(mars_house - moon_house) in [1, 11]:
                return "adjacent"
            elif abs(mars_house - moon_house) == 6:
                return "opposition"
            else:
                return "other"
        
        return "unknown"
    
    def _get_sun_lagna_separation(self, planets: List[Dict], ascendant: Dict) -> float:
        """Get Sun-Lagna separation in degrees."""
        sun_longitude = None
        ascendant_longitude = ascendant.get("longitude", 0)
        
        for planet in planets:
            if planet["name"] == "Sun":
                sun_longitude = planet["longitude"]
                break
        
        if sun_longitude is not None:
            diff = abs(sun_longitude - ascendant_longitude)
            if diff > 180:
                diff = 360 - diff
            return diff
        
        return 0.0


# Global payload builder instance
payload_builder = PayloadBuilder()

