"""Panchanga calculations (tithi, nakshatra, pada, yoga, karana)."""

from datetime import datetime
from typing import Dict, Tuple
import pytz
from app.services.calc_engine.ephemeris import ephemeris_service
from app.utils.errors import CalculationError


class PanchangaService:
    """Service for Panchanga calculations."""
    
    def __init__(self):
        """Initialize Panchanga service."""
        self.tithi_names = [
            "Purnima", "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
            "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami", "Ekadashi",
            "Dwadashi", "Trayodashi", "Chaturdashi", "Amavasya"
        ]
        
        self.paksha_names = ["Krishna Paksha", "Shukla Paksha"]
        
        self.weekday_names = [
            "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"
        ]
        
        self.yoga_names = [
            "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda",
            "Sukarma", "Dhriti", "Shula", "Ganda", "Vriddhi", "Dhruva",
            "Vyaghata", "Harshana", "Vajra", "Siddhi", "Vyatipata", "Variyan",
            "Parigha", "Shiva", "Siddha", "Sadhya", "Shubha", "Shukla",
            "Brahma", "Indra", "Vaidhriti"
        ]
        
        self.karana_names = [
            "Bava", "Balava", "Kaulava", "Taitila", "Garija", "Vanija",
            "Vishti", "Shakuni", "Chatushpada", "Naga", "Kimstughna"
        ]
    
    def get_weekday(self, jd: float) -> str:
        """Get weekday from Julian day."""
        weekday_num = int(jd + 1.5) % 7
        return self.weekday_names[weekday_num]
    
    def get_tithi(self, jd: float) -> Tuple[str, str]:
        """Get tithi (lunar day) and paksha."""
        try:
            # Get Sun and Moon positions
            sun_pos = ephemeris_service.get_planet_positions(jd, ["Sun"])["Sun"]
            moon_pos = ephemeris_service.get_planet_positions(jd, ["Moon"])["Moon"]
            
            # Calculate angular difference
            sun_long = sun_pos["longitude"]
            moon_long = moon_pos["longitude"]
            
            # Normalize difference
            diff = moon_long - sun_long
            if diff < 0:
                diff += 360
            
            # Tithi calculation (12° per tithi)
            tithi_degrees = 12.0
            tithi_num = int(diff / tithi_degrees)
            
            # Determine paksha
            paksha = "Shukla Paksha" if diff < 180 else "Krishna Paksha"
            
            # Adjust tithi number for paksha
            if paksha == "Krishna Paksha":
                tithi_num = 15 - tithi_num
            else:
                tithi_num += 1
            
            tithi_name = self.tithi_names[tithi_num]
            
            return f"{paksha} {tithi_num}", paksha
            
        except Exception as e:
            raise CalculationError(f"Error calculating tithi: {str(e)}")
    
    def get_nakshatra_and_pada(self, jd: float) -> Tuple[str, int]:
        """Get nakshatra and pada from Moon position."""
        try:
            moon_pos = ephemeris_service.get_planet_positions(jd, ["Moon"])["Moon"]
            return ephemeris_service.get_nakshatra_and_pada(moon_pos["longitude"])
            
        except Exception as e:
            raise CalculationError(f"Error calculating nakshatra: {str(e)}")
    
    def get_yoga(self, jd: float) -> str:
        """Get yoga from Sun and Moon positions."""
        try:
            sun_pos = ephemeris_service.get_planet_positions(jd, ["Sun"])["Sun"]
            moon_pos = ephemeris_service.get_planet_positions(jd, ["Moon"])["Moon"]
            
            sun_long = sun_pos["longitude"]
            moon_long = moon_pos["longitude"]
            
            # Yoga calculation (sum of Sun and Moon longitudes)
            yoga_sum = sun_long + moon_long
            
            # Normalize
            while yoga_sum >= 360:
                yoga_sum -= 360
            
            # 27 yogas, each 13°20'
            yoga_degrees = 13.333333333333334
            yoga_num = int(yoga_sum / yoga_degrees)
            
            return self.yoga_names[yoga_num]
            
        except Exception as e:
            raise CalculationError(f"Error calculating yoga: {str(e)}")
    
    def get_karana(self, jd: float) -> str:
        """Get karana from tithi."""
        try:
            tithi_info, _ = self.get_tithi(jd)
            tithi_num = int(tithi_info.split()[-1])
            
            # Karana calculation
            if tithi_num == 1:
                karana_num = 0  # Bava
            elif tithi_num == 2:
                karana_num = 1  # Balava
            elif tithi_num == 3:
                karana_num = 2  # Kaulava
            elif tithi_num == 4:
                karana_num = 3  # Taitila
            elif tithi_num == 5:
                karana_num = 4  # Garija
            elif tithi_num == 6:
                karana_num = 5  # Vanija
            elif tithi_num == 7:
                karana_num = 6  # Vishti
            elif tithi_num == 8:
                karana_num = 7  # Shakuni
            elif tithi_num == 9:
                karana_num = 8  # Chatushpada
            elif tithi_num == 10:
                karana_num = 9  # Naga
            elif tithi_num == 11:
                karana_num = 10  # Kimstughna
            else:
                # For other tithis, cycle through karanas
                karana_num = (tithi_num - 1) % 11
            
            return self.karana_names[karana_num]
            
        except Exception as e:
            raise CalculationError(f"Error calculating karana: {str(e)}")
    
    def get_sunrise_sunset(self, jd: float, lat: float, lon: float) -> Tuple[str, str]:
        """Get sunrise and sunset times."""
        try:
            import swisseph as swe
            
            # Calculate sunrise and sunset
            # geopos = [longitude, latitude, altitude]
            geopos = [lon, lat, 0.0]  # altitude = 0 for sea level
            
            res, tret = swe.rise_trans(jd, swe.SUN, swe.CALC_RISE, geopos)
            if res < 0:
                raise CalculationError("Sunrise calculation failed")
            sunrise_jd = tret[0]
            
            res, tret = swe.rise_trans(jd, swe.SUN, swe.CALC_SET, geopos)
            if res < 0:
                raise CalculationError("Sunset calculation failed")
            sunset_jd = tret[0]
            
            sunrise_dt = ephemeris_service._julian_to_datetime(sunrise_jd)
            sunset_dt = ephemeris_service._julian_to_datetime(sunset_jd)
            
            return sunrise_dt.strftime("%H:%M"), sunset_dt.strftime("%H:%M")
            
        except Exception as e:
            raise CalculationError(f"Error calculating sunrise/sunset: {str(e)}")
    
    def get_full_panchanga(self, jd: float, lat: float, lon: float) -> Dict:
        """Get complete panchanga for a given time and location."""
        try:
            weekday = self.get_weekday(jd)
            tithi_info, paksha = self.get_tithi(jd)
            nakshatra, pada = self.get_nakshatra_and_pada(jd)
            yoga = self.get_yoga(jd)
            karana = self.get_karana(jd)
            sunrise, sunset = self.get_sunrise_sunset(jd, lat, lon)
            
            return {
                "weekday": weekday,
                "tithi": tithi_info,
                "paksha": paksha,
                "nakshatra": nakshatra,
                "pada": pada,
                "yoga": yoga,
                "karana": karana,
                "sunrise": sunrise,
                "sunset": sunset
            }
            
        except Exception as e:
            raise CalculationError(f"Error calculating panchanga: {str(e)}")


# Global panchanga service instance
panchanga_service = PanchangaService()
