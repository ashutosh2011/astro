"""Vimshottari dasha calculations."""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from app.services.calc_engine.ephemeris import ephemeris_service
from app.utils.errors import CalculationError


class DashaService:
    """Service for Vimshottari dasha calculations."""
    
    def __init__(self):
        """Initialize dasha service."""
        # Vimshottari dasha periods (in years)
        self.dasha_periods = {
            "Sun": 6,
            "Moon": 10,
            "Mars": 7,
            "Rahu": 18,
            "Jupiter": 16,
            "Saturn": 19,
            "Mercury": 17,
            "Ketu": 7,
            "Venus": 20
        }
        
        # Order of dashas
        self.dasha_order = [
            "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", 
            "Mercury", "Ketu", "Venus"
        ]
        
        # Nakshatra lords
        self.nakshatra_lords = [
            "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
            "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
            "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"
        ]
    
    def get_moon_nakshatra(self, jd: float) -> Tuple[str, float]:
        """Get Moon's nakshatra and position within it."""
        try:
            moon_pos = ephemeris_service.get_planet_positions(jd, ["Moon"])["Moon"]
            moon_longitude = moon_pos["longitude"]
            
            # Calculate nakshatra
            nakshatra_degrees = 13.333333333333334  # 13°20'
            nakshatra_num = int(moon_longitude // nakshatra_degrees)
            degree_in_nakshatra = moon_longitude % nakshatra_degrees
            
            # Get nakshatra lord
            nakshatra_lord = self.nakshatra_lords[nakshatra_num]
            
            return nakshatra_lord, degree_in_nakshatra
            
        except Exception as e:
            raise CalculationError(f"Error calculating Moon nakshatra: {str(e)}")
    
    def get_dasha_start_date(self, birth_jd: float, moon_longitude: float) -> float:
        """Calculate the start date of the dasha cycle."""
        try:
            # Get Moon's nakshatra lord
            nakshatra_lord, degree_in_nakshatra = self.get_moon_nakshatra(birth_jd)
            
            # Calculate remaining period in current nakshatra
            nakshatra_degrees = 13.333333333333334
            remaining_degrees = nakshatra_degrees - degree_in_nakshatra
            
            # Convert to years (each degree = 1 year in Vimshottari)
            remaining_years = remaining_degrees / nakshatra_degrees * self.dasha_periods[nakshatra_lord]
            
            # Calculate start date
            start_jd = birth_jd - (remaining_years * 365.25)
            
            return start_jd
            
        except Exception as e:
            raise CalculationError(f"Error calculating dasha start date: {str(e)}")
    
    def get_current_dasha(self, birth_jd: float, current_jd: float) -> Tuple[str, str, float, float]:
        """Get current Mahadasha and Antardasha."""
        try:
            # Calculate elapsed time since birth
            elapsed_days = current_jd - birth_jd
            elapsed_years = elapsed_days / 365.25
            
            # Get dasha start date
            dasha_start_jd = self.get_dasha_start_date(birth_jd, 
                ephemeris_service.get_planet_positions(birth_jd, ["Moon"])["Moon"]["longitude"])
            
            # Calculate elapsed time since dasha start
            dasha_elapsed_days = current_jd - dasha_start_jd
            dasha_elapsed_years = dasha_elapsed_days / 365.25
            
            # Find current Mahadasha
            current_md = None
            md_start_year = 0
            
            for md_planet in self.dasha_order:
                md_period = self.dasha_periods[md_planet]
                
                if dasha_elapsed_years < md_start_year + md_period:
                    current_md = md_planet
                    break
                
                md_start_year += md_period
            
            if current_md is None:
                # Cycle completed, start over
                current_md = self.dasha_order[0]
                md_start_year = 0
            
            # Calculate Antardasha
            md_elapsed_years = dasha_elapsed_years - md_start_year
            ad_start_year = 0
            
            for ad_planet in self.dasha_order:
                ad_period = self.dasha_periods[ad_planet] * self.dasha_periods[current_md] / 120
                
                if md_elapsed_years < ad_start_year + ad_period:
                    current_ad = ad_planet
                    break
                
                ad_start_year += ad_period
            
            if current_ad is None:
                current_ad = self.dasha_order[0]
            
            # Calculate remaining periods
            md_remaining_years = self.dasha_periods[current_md] - md_elapsed_years
            ad_remaining_years = ad_period - (md_elapsed_years - ad_start_year)
            
            return current_md, current_ad, md_remaining_years, ad_remaining_years
            
        except Exception as e:
            raise CalculationError(f"Error calculating current dasha: {str(e)}")
    
    def get_next_12_months_ads(self, birth_jd: float, current_jd: float) -> List[Dict]:
        """Get Antardashas for the next 12 months."""
        try:
            current_md, current_ad, md_remaining, ad_remaining = self.get_current_dasha(birth_jd, current_jd)
            
            ads = []
            current_date = datetime.fromtimestamp((current_jd - 2440588) * 86400)
            end_date = current_date + timedelta(days=365)  # 12 months
            
            # Start with current AD
            ad_start_date = current_date
            ad_end_date = current_date + timedelta(days=ad_remaining * 365.25)
            
            # Truncate if extends beyond 12 months
            if ad_end_date > end_date:
                ad_end_date = end_date
            
            ads.append({
                "planet": current_ad,
                "start_date": ad_start_date.strftime("%Y-%m-%d"),
                "end_date": ad_end_date.strftime("%Y-%m-%d"),
                "md": current_md,
                "ad": current_ad
            })
            
            # If current AD doesn't cover full 12 months, add next AD
            if ad_end_date < end_date:
                next_ad_start = ad_end_date
                next_ad_index = (self.dasha_order.index(current_ad) + 1) % len(self.dasha_order)
                next_ad = self.dasha_order[next_ad_index]
                
                # Calculate next AD period
                next_ad_period_years = self.dasha_periods[next_ad] * self.dasha_periods[current_md] / 120
                next_ad_end = next_ad_start + timedelta(days=next_ad_period_years * 365.25)
                
                # Truncate if extends beyond 12 months
                if next_ad_end > end_date:
                    next_ad_end = end_date
                
                ads.append({
                    "planet": next_ad,
                    "start_date": next_ad_start.strftime("%Y-%m-%d"),
                    "end_date": next_ad_end.strftime("%Y-%m-%d"),
                    "md": current_md,
                    "ad": next_ad
                })
            
            return ads
            
        except Exception as e:
            raise CalculationError(f"Error calculating next 12 months ADs: {str(e)}")
    
    def get_current_paryantar_dasha(self, birth_jd: float, current_jd: float) -> Tuple[str, float]:
        """Get current Paryantar dasha."""
        try:
            current_md, current_ad, md_remaining, ad_remaining = self.get_current_dasha(birth_jd, current_jd)
            
            # Calculate elapsed time in current AD
            ad_period_years = self.dasha_periods[current_ad] * self.dasha_periods[current_md] / 120
            ad_elapsed_years = ad_period_years - ad_remaining
            
            # Find current Paryantar dasha
            pd_start_year = 0
            
            for pd_planet in self.dasha_order:
                pd_period = self.dasha_periods[pd_planet] * self.dasha_periods[current_ad] * self.dasha_periods[current_md] / (120 * 120)
                
                if ad_elapsed_years < pd_start_year + pd_period:
                    current_pd = pd_planet
                    pd_remaining = pd_period - (ad_elapsed_years - pd_start_year)
                    return current_pd, pd_remaining
                
                pd_start_year += pd_period
            
            # Fallback
            return self.dasha_order[0], 0
            
        except Exception as e:
            raise CalculationError(f"Error calculating current Paryantar dasha: {str(e)}")
    
    def get_complete_dasha_sequence(self, birth_jd: float, current_jd: float) -> Dict:
        """Get complete dasha sequence showing all levels."""
        try:
            current_md, current_ad, md_remaining, ad_remaining = self.get_current_dasha(birth_jd, current_jd)
            current_pd, pd_remaining = self.get_current_paryantar_dasha(birth_jd, current_jd)
            
            # Get dasha start date
            dasha_start_jd = self.get_dasha_start_date(birth_jd, 
                ephemeris_service.get_planet_positions(birth_jd, ["Moon"])["Moon"]["longitude"])
            
            # Calculate elapsed time since dasha start
            dasha_elapsed_days = current_jd - dasha_start_jd
            dasha_elapsed_years = dasha_elapsed_days / 365.25
            
            # Find current Mahadasha start
            md_start_year = 0
            for md_planet in self.dasha_order:
                md_period = self.dasha_periods[md_planet]
                if md_planet == current_md:
                    break
                md_start_year += md_period
            
            # Calculate Mahadasha start date
            md_start_jd = dasha_start_jd + (md_start_year * 365.25)
            md_start_date = datetime.fromtimestamp((md_start_jd - 2440588) * 86400)
            md_end_date = md_start_date + timedelta(days=self.dasha_periods[current_md] * 365.25)
            
            # Calculate Antardasha start
            ad_start_year = 0
            for ad_planet in self.dasha_order:
                ad_period = self.dasha_periods[ad_planet] * self.dasha_periods[current_md] / 120
                if ad_planet == current_ad:
                    break
                ad_start_year += ad_period
            
            ad_start_jd = md_start_jd + (ad_start_year * 365.25)
            ad_start_date = datetime.fromtimestamp((ad_start_jd - 2440588) * 86400)
            ad_end_date = ad_start_date + timedelta(days=self.dasha_periods[current_ad] * self.dasha_periods[current_md] / 120 * 365.25)
            
            # Calculate Paryantar dasha start
            pd_start_year = 0
            for pd_planet in self.dasha_order:
                pd_period = self.dasha_periods[pd_planet] * self.dasha_periods[current_ad] * self.dasha_periods[current_md] / (120 * 120)
                if pd_planet == current_pd:
                    break
                pd_start_year += pd_period
            
            pd_start_jd = ad_start_jd + (pd_start_year * 365.25)
            pd_start_date = datetime.fromtimestamp((pd_start_jd - 2440588) * 86400)
            pd_end_date = pd_start_date + timedelta(days=self.dasha_periods[current_pd] * self.dasha_periods[current_ad] * self.dasha_periods[current_md] / (120 * 120) * 365.25)
            
            return {
                "maha_dasha": {
                    "planet": current_md,
                    "start_date": md_start_date.strftime("%Y-%m-%d"),
                    "end_date": md_end_date.strftime("%Y-%m-%d"),
                    "remaining_years": md_remaining,
                    "total_years": self.dasha_periods[current_md]
                },
                "antar_dasha": {
                    "planet": current_ad,
                    "start_date": ad_start_date.strftime("%Y-%m-%d"),
                    "end_date": ad_end_date.strftime("%Y-%m-%d"),
                    "remaining_years": ad_remaining,
                    "total_years": self.dasha_periods[current_ad] * self.dasha_periods[current_md] / 120
                },
                "paryantar_dasha": {
                    "planet": current_pd,
                    "start_date": pd_start_date.strftime("%Y-%m-%d"),
                    "end_date": pd_end_date.strftime("%Y-%m-%d"),
                    "remaining_years": pd_remaining,
                    "total_years": self.dasha_periods[current_pd] * self.dasha_periods[current_ad] * self.dasha_periods[current_md] / (120 * 120)
                }
            }
            
        except Exception as e:
            raise CalculationError(f"Error calculating complete dasha sequence: {str(e)}")
    
    def get_full_dasha_info(self, birth_jd: float, current_jd: float) -> Dict:
        """Get complete dasha information."""
        try:
            current_md, current_ad, md_remaining, ad_remaining = self.get_current_dasha(birth_jd, current_jd)
            next_12m_ads = self.get_next_12_months_ads(birth_jd, current_jd)
            
            # Try to get complete sequence, but don't fail if it doesn't work
            complete_sequence = None
            try:
                complete_sequence = self.get_complete_dasha_sequence(birth_jd, current_jd)
            except Exception as e:
                print(f"Warning: Could not calculate complete dasha sequence: {str(e)}")
                complete_sequence = None
            
            return {
                "current_md": current_md,
                "current_ad": current_ad,
                "md_remaining_years": md_remaining,
                "ad_remaining_years": ad_remaining,
                "next_12m_ads": next_12m_ads,
                "complete_sequence": complete_sequence
            }
            
        except Exception as e:
            raise CalculationError(f"Error calculating full dasha info: {str(e)}")


# Global dasha service instance
dasha_service = DashaService()

