"""Swiss Ephemeris wrapper for astronomical calculations."""

import swisseph as swe
from datetime import datetime, date
from typing import Dict, List, Tuple, Optional
import pytz
from app.config import settings
from app.utils.errors import EphemerisLoadFailedError, CalculationError


class EphemerisService:
    """Swiss Ephemeris service for astronomical calculations."""
    
    def __init__(self):
        """Initialize Swiss Ephemeris."""
        try:
            # Set ephemeris path
            swe.set_ephe_path(settings.ephemeris_path)
            
            # Test ephemeris loading
            swe.calc_ut(2451545.0, swe.SUN, swe.FLG_SWIEPH)
            
        except Exception as e:
            raise EphemerisLoadFailedError(settings.ephemeris_path)
    
    def _datetime_to_julian(self, dt: datetime) -> float:
        """Convert datetime to Julian day number."""
        year = dt.year
        month = dt.month
        day = dt.day
        hour = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
        
        return swe.julday(year, month, day, hour, swe.GREG_CAL)
    
    def _julian_to_datetime(self, jd: float) -> datetime:
        """Convert Julian day number to datetime."""
        year, month, day, hour = swe.revjul(jd, swe.GREG_CAL)
        
        return datetime(
            year=int(year),
            month=int(month),
            day=int(day),
            hour=int(hour),
            minute=int((hour - int(hour)) * 60),
            second=int(((hour - int(hour)) * 60 - int((hour - int(hour)) * 60)) * 60)
        )
    
    def _get_ayanamsa_offset(self, jd: float, ayanamsa: str = "Lahiri") -> float:
        """Get ayanamsa offset for sidereal calculations."""
        ayanamsa_map = {
            "Lahiri": swe.SIDM_LAHIRI,
            "Raman": swe.SIDM_RAMAN,
            "KP": swe.SIDM_KRISHNAMURTI,
            "Fagan-Bradley": swe.SIDM_FAGAN_BRADLEY,
            "Yukteshwar": swe.SIDM_YUKTESHWAR
        }
        
        sid_mode = ayanamsa_map.get(ayanamsa, swe.SIDM_LAHIRI)
        retflags, aya = swe.get_ayanamsa_ex(jd, sid_mode)
        return aya
    
    def get_planet_positions(self, jd: float, planets: List[str] = None) -> Dict[str, Dict]:
        """Get sidereal positions of planets."""
        if planets is None:
            planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
        
        planet_map = {
            "Sun": swe.SUN,
            "Moon": swe.MOON,
            "Mars": swe.MARS,
            "Mercury": swe.MERCURY,
            "Jupiter": swe.JUPITER,
            "Venus": swe.VENUS,
            "Saturn": swe.SATURN,
            "Rahu": swe.MEAN_NODE,
            "Ketu": swe.MEAN_NODE  # Ketu is 180° from Rahu
        }
        
        positions = {}
        ayanamsa_offset = self._get_ayanamsa_offset(jd)
        
        for planet_name in planets:
            try:
                planet_id = planet_map[planet_name]
                xx, ret = swe.calc_ut(jd, planet_id, swe.FLG_SWIEPH)
                
                if ret < 0:
                    raise CalculationError(f"Error calculating {planet_name} position")
                
                # Convert to sidereal longitude
                sidereal_longitude = xx[0] - ayanamsa_offset
                
                # Normalize to 0-360°
                while sidereal_longitude < 0:
                    sidereal_longitude += 360
                while sidereal_longitude >= 360:
                    sidereal_longitude -= 360
                
                # Get sign and degree within sign
                sign_num = int(sidereal_longitude // 30)
                degree_in_sign = sidereal_longitude % 30
                
                # Check if retrograde
                is_retrograde = xx[3] < 0  # Speed is negative for retrograde
                
                positions[planet_name] = {
                    "longitude": sidereal_longitude,
                    "sign": sign_num,
                    "degree_in_sign": degree_in_sign,
                    "retrograde": is_retrograde,
                    "speed": xx[3]
                }
                
                # Special handling for Ketu (180° from Rahu)
                if planet_name == "Ketu":
                    ketu_longitude = sidereal_longitude + 180
                    if ketu_longitude >= 360:
                        ketu_longitude -= 360
                    
                    ketu_sign_num = int(ketu_longitude // 30)
                    ketu_degree_in_sign = ketu_longitude % 30
                    
                    positions["Ketu"] = {
                        "longitude": ketu_longitude,
                        "sign": ketu_sign_num,
                        "degree_in_sign": ketu_degree_in_sign,
                        "retrograde": is_retrograde,
                        "speed": xx[3]
                    }
                
            except Exception as e:
                raise CalculationError(f"Error calculating {planet_name}: {str(e)}")
        
        return positions
    
    def get_ascendant(self, jd: float, lat: float, lon: float, ayanamsa: str = "Lahiri") -> Dict:
        """Get ascendant (rising sign) calculation."""
        try:
            # Calculate ascendant
            cusps, ascmc = swe.houses(jd, lat, lon, b'P')  # Placidus houses
            
            # Get sidereal ascendant
            ayanamsa_offset = self._get_ayanamsa_offset(jd, ayanamsa)
            sidereal_ascendant = ascmc[0] - ayanamsa_offset
            
            # Normalize to 0-360°
            while sidereal_ascendant < 0:
                sidereal_ascendant += 360
            while sidereal_ascendant >= 360:
                sidereal_ascendant -= 360
            
            # Get sign and degree within sign
            sign_num = int(sidereal_ascendant // 30)
            degree_in_sign = sidereal_ascendant % 30
            
            return {
                "longitude": sidereal_ascendant,
                "sign": sign_num,
                "degree_in_sign": degree_in_sign,
                "cusp_degree": ascmc[0]  # Tropical cusp degree
            }
            
        except Exception as e:
            raise CalculationError(f"Error calculating ascendant: {str(e)}")
    
    def get_houses(self, jd: float, lat: float, lon: float, house_system: str = "WholeSign") -> Dict:
        """Get house cusps."""
        try:
            if house_system == "WholeSign":
                # For Whole Sign houses, we only need the ascendant
                ascendant_data = self.get_ascendant(jd, lat, lon)
                ascendant_sign = ascendant_data["sign"]
                
                houses = {}
                for i in range(1, 13):
                    house_sign = (ascendant_sign + i - 1) % 12
                    houses[i] = {
                        "sign": house_sign,
                        "cusp_degree": ascendant_data["degree_in_sign"] if i == 1 else 0.0
                    }
                
                return houses
            
            else:
                # For other house systems, use Swiss Ephemeris
                cusps, ascmc = swe.houses(jd, lat, lon, b'P')  # Placidus
                
                houses = {}
                for i in range(1, 13):
                    cusp_longitude = cusps[i]
                    
                    # Convert to sidereal
                    ayanamsa_offset = self._get_ayanamsa_offset(jd)
                    sidereal_longitude = cusp_longitude - ayanamsa_offset
                    
                    # Normalize
                    while sidereal_longitude < 0:
                        sidereal_longitude += 360
                    while sidereal_longitude >= 360:
                        sidereal_longitude -= 360
                    
                    sign_num = int(sidereal_longitude // 30)
                    degree_in_sign = sidereal_longitude % 30
                    
                    houses[i] = {
                        "sign": sign_num,
                        "cusp_degree": degree_in_sign
                    }
                
                return houses
                
        except Exception as e:
            raise CalculationError(f"Error calculating houses: {str(e)}")
    
    def get_planet_house_positions(self, planet_positions: Dict, houses: Dict) -> Dict[str, int]:
        """Get which house each planet is in."""
        planet_houses = {}
        
        for planet_name, planet_data in planet_positions.items():
            planet_sign = planet_data["sign"]
            
            # Find which house this sign corresponds to
            for house_num, house_data in houses.items():
                if house_data["sign"] == planet_sign:
                    planet_houses[planet_name] = house_num
                    break
            else:
                # Fallback - shouldn't happen
                planet_houses[planet_name] = 1
        
        return planet_houses
    
    def get_nakshatra_and_pada(self, longitude: float) -> Tuple[str, int]:
        """Get nakshatra and pada from longitude."""
        # 27 nakshatras, each 13°20' (13.333...°)
        nakshatra_degrees = 13.333333333333334
        
        nakshatra_num = int(longitude // nakshatra_degrees)
        degree_in_nakshatra = longitude % nakshatra_degrees
        
        # Each nakshatra has 4 padas, each 3°20' (3.333...°)
        pada_num = int(degree_in_nakshatra // 3.3333333333333335) + 1
        
        nakshatra_names = [
            "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
            "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
            "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
            "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishtha",
            "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
        ]
        
        nakshatra_name = nakshatra_names[nakshatra_num]
        
        return nakshatra_name, pada_num


# Global ephemeris service instance
ephemeris_service = EphemerisService()

