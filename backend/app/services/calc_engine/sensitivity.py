"""Sensitivity analysis for birth time uncertainty."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from app.services.calc_engine.ephemeris import ephemeris_service
from app.services.calc_engine.charts import chart_service
from app.services.calc_engine.dasha import dasha_service
from app.utils.errors import CalculationError


class SensitivityService:
    """Service for sensitivity analysis."""
    
    def __init__(self):
        """Initialize sensitivity service."""
        self.sign_names = [
            "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
        ]
    
    def analyze_sensitivity(self, birth_jd: float, lat: float, lon: float, 
                           uncertainty_minutes: int, ayanamsa: str = "Lahiri") -> Dict:
        """Analyze sensitivity to birth time changes."""
        try:
            if uncertainty_minutes <= 0:
                return {
                    "uncertainty_minutes": 0,
                    "lagna_flips": False,
                    "lagna_original_sign": self._get_ascendant_sign(birth_jd, lat, lon, ayanamsa),
                    "lagna_if_minus": None,
                    "lagna_if_plus": None,
                    "moon_sign_flips": False,
                    "d9_asc_flips": False,
                    "dasha_boundary_risky": False,
                    "dasha_boundary_reason": "",
                    "house_changes": []
                }
            
            # Calculate modified birth times
            uncertainty_days = uncertainty_minutes / (24 * 60)
            birth_jd_minus = birth_jd - uncertainty_days
            birth_jd_plus = birth_jd + uncertainty_days
            
            # Get original values
            original_ascendant = self._get_ascendant_sign(birth_jd, lat, lon, ayanamsa)
            original_moon_sign = self._get_moon_sign(birth_jd)
            original_d9_asc = self._get_d9_ascendant_sign(birth_jd, lat, lon, ayanamsa)
            
            # Get modified values
            ascendant_minus = self._get_ascendant_sign(birth_jd_minus, lat, lon, ayanamsa)
            ascendant_plus = self._get_ascendant_sign(birth_jd_plus, lat, lon, ayanamsa)
            
            moon_sign_minus = self._get_moon_sign(birth_jd_minus)
            moon_sign_plus = self._get_moon_sign(birth_jd_plus)
            
            d9_asc_minus = self._get_d9_ascendant_sign(birth_jd_minus, lat, lon, ayanamsa)
            d9_asc_plus = self._get_d9_ascendant_sign(birth_jd_plus, lat, lon, ayanamsa)
            
            # Check for flips
            lagna_flips = (original_ascendant != ascendant_minus or 
                          original_ascendant != ascendant_plus)
            moon_sign_flips = (original_moon_sign != moon_sign_minus or 
                             original_moon_sign != moon_sign_plus)
            d9_asc_flips = (original_d9_asc != d9_asc_minus or 
                           original_d9_asc != d9_asc_plus)
            
            # Check dasha boundary risk
            dasha_boundary_risky, dasha_reason = self._check_dasha_boundary_risk(
                birth_jd, birth_jd_minus, birth_jd_plus
            )
            
            # Check house changes for planets
            house_changes = self._get_house_changes(
                birth_jd, birth_jd_minus, birth_jd_plus, lat, lon, ayanamsa
            )
            
            return {
                "uncertainty_minutes": uncertainty_minutes,
                "lagna_flips": lagna_flips,
                "lagna_original_sign": original_ascendant,
                "lagna_if_minus": ascendant_minus,
                "lagna_if_plus": ascendant_plus,
                "moon_sign_flips": moon_sign_flips,
                "d9_asc_flips": d9_asc_flips,
                "dasha_boundary_risky": dasha_boundary_risky,
                "dasha_boundary_reason": dasha_reason,
                "house_changes": house_changes
            }
            
        except Exception as e:
            raise CalculationError(f"Error in sensitivity analysis: {str(e)}")
    
    def _get_ascendant_sign(self, jd: float, lat: float, lon: float, ayanamsa: str) -> str:
        """Get ascendant sign."""
        try:
            ascendant = ephemeris_service.get_ascendant(jd, lat, lon, ayanamsa)
            return self.sign_names[ascendant["sign"]]
        except:
            return "Unknown"
    
    def _get_moon_sign(self, jd: float) -> str:
        """Get Moon sign."""
        try:
            moon_pos = ephemeris_service.get_planet_positions(jd, ["Moon"])["Moon"]
            return self.sign_names[moon_pos["sign"]]
        except:
            return "Unknown"
    
    def _get_d9_ascendant_sign(self, jd: float, lat: float, lon: float, ayanamsa: str) -> str:
        """Get D9 ascendant sign."""
        try:
            ascendant = ephemeris_service.get_ascendant(jd, lat, lon, ayanamsa)
            d9_longitude = ascendant["longitude"] / 3.3333333333333335
            d9_sign_num = int(d9_longitude) % 12
            return self.sign_names[d9_sign_num]
        except:
            return "Unknown"
    
    def _check_dasha_boundary_risk(self, original_jd: float, minus_jd: float, plus_jd: float) -> tuple:
        """Check if birth time changes affect dasha boundaries."""
        try:
            # Get current dasha for original time
            current_md, current_ad, _, _ = dasha_service.get_current_dasha(original_jd, original_jd)
            
            # Check if dasha changes with time variations
            minus_md, minus_ad, _, _ = dasha_service.get_current_dasha(minus_jd, minus_jd)
            plus_md, plus_ad, _, _ = dasha_service.get_current_dasha(plus_jd, plus_jd)
            
            # Check for dasha changes
            md_changes = (current_md != minus_md or current_md != plus_md)
            ad_changes = (current_ad != minus_ad or current_ad != plus_ad)
            
            if md_changes or ad_changes:
                reasons = []
                if md_changes:
                    reasons.append("MD changes")
                if ad_changes:
                    reasons.append("AD changes")
                return True, "; ".join(reasons)
            
            return False, ""
            
        except Exception as e:
            return False, f"Error checking dasha boundaries: {str(e)}"
    
    def _get_house_changes(self, original_jd: float, minus_jd: float, plus_jd: float,
                          lat: float, lon: float, ayanamsa: str) -> List[Dict]:
        """Get house changes for planets with time variations."""
        try:
            house_changes = []
            
            # Get planet positions and houses for all three times
            original_positions = ephemeris_service.get_planet_positions(original_jd)
            minus_positions = ephemeris_service.get_planet_positions(minus_jd)
            plus_positions = ephemeris_service.get_planet_positions(plus_jd)
            
            original_houses = ephemeris_service.get_houses(original_jd, lat, lon, "WholeSign")
            minus_houses = ephemeris_service.get_houses(minus_jd, lat, lon, "WholeSign")
            plus_houses = ephemeris_service.get_houses(plus_jd, lat, lon, "WholeSign")
            
            original_planet_houses = ephemeris_service.get_planet_house_positions(original_positions, original_houses)
            minus_planet_houses = ephemeris_service.get_planet_house_positions(minus_positions, minus_houses)
            plus_planet_houses = ephemeris_service.get_planet_house_positions(plus_positions, plus_houses)
            
            # Check for house changes
            for planet in original_positions.keys():
                if planet in ["Rahu", "Ketu"]:
                    continue  # Skip nodes for simplicity
                
                original_house = original_planet_houses.get(planet, 1)
                minus_house = minus_planet_houses.get(planet, 1)
                plus_house = plus_planet_houses.get(planet, 1)
                
                house_changes.append({
                    "planet": planet,
                    "house_original": original_house,
                    "house_if_minus": minus_house,
                    "house_if_plus": plus_house
                })
            
            return house_changes
            
        except Exception as e:
            return [{"planet": "Error", "house_original": 0, "house_if_minus": 0, "house_if_plus": 0}]
    
    def get_sensitivity_summary(self, sensitivity_data: Dict) -> Dict:
        """Get summary of sensitivity analysis."""
        try:
            total_risks = 0
            risk_details = []
            
            if sensitivity_data["lagna_flips"]:
                total_risks += 1
                risk_details.append("Ascendant sign changes")
            
            if sensitivity_data["moon_sign_flips"]:
                total_risks += 1
                risk_details.append("Moon sign changes")
            
            if sensitivity_data["d9_asc_flips"]:
                total_risks += 1
                risk_details.append("D9 ascendant changes")
            
            if sensitivity_data["dasha_boundary_risky"]:
                total_risks += 1
                risk_details.append("Dasha boundary risk")
            
            # Count house changes
            house_changes_count = 0
            for change in sensitivity_data["house_changes"]:
                if (change["house_original"] != change["house_if_minus"] or 
                    change["house_original"] != change["house_if_plus"]):
                    house_changes_count += 1
            
            if house_changes_count > 0:
                total_risks += 1
                risk_details.append(f"{house_changes_count} planets change houses")
            
            return {
                "total_risks": total_risks,
                "risk_level": "High" if total_risks >= 3 else "Medium" if total_risks >= 1 else "Low",
                "risk_details": risk_details,
                "recommendation": self._get_recommendation(total_risks, sensitivity_data["uncertainty_minutes"])
            }
            
        except Exception as e:
            return {
                "total_risks": 0,
                "risk_level": "Unknown",
                "risk_details": ["Error in analysis"],
                "recommendation": "Manual verification recommended"
            }
    
    def _get_recommendation(self, total_risks: int, uncertainty_minutes: int) -> str:
        """Get recommendation based on sensitivity analysis."""
        if uncertainty_minutes == 0:
            return "Birth time is precise, calculations are reliable"
        elif total_risks == 0:
            return "Birth time uncertainty has minimal impact on calculations"
        elif total_risks <= 2:
            return "Some sensitivity detected, consider rectification if possible"
        else:
            return "High sensitivity detected, birth time rectification strongly recommended"


# Global sensitivity service instance
sensitivity_service = SensitivityService()

