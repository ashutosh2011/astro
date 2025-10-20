"""Main calculation orchestrator that runs the full pipeline."""

import json
import gzip
from datetime import datetime
from typing import Dict, Any
from app.services.calc_engine.ephemeris import ephemeris_service
from app.services.calc_engine.panchanga import panchanga_service
from app.services.calc_engine.charts import chart_service
from app.services.calc_engine.dignities import dignity_service
from app.services.calc_engine.aspects import aspect_service
from app.services.calc_engine.dasha import dasha_service
from app.services.calc_engine.transits import transit_service
from app.services.calc_engine.ashtakavarga import ashtakavarga_service
from app.services.calc_engine.bhava_bala import bhavabala_service
from app.services.calc_engine.yogas import yoga_service
from app.services.calc_engine.sensitivity import sensitivity_service
from app.utils.errors import CalculationError


class CalcOrchestrator:
    """Main orchestrator for all calculation services."""
    
    def __init__(self):
        """Initialize calculation orchestrator."""
        self.ruleset_version = "1.0.0"
        self.ephemeris_version = "sepl_18"
    
    def run_full_calculation(self, birth_data: Dict) -> Dict:
        """Run complete calculation pipeline."""
        try:
            # Extract birth data
            jd = birth_data["jd"]
            lat = birth_data["lat"]
            lon = birth_data["lon"]
            ayanamsa = birth_data.get("ayanamsa", "Lahiri")
            house_system = birth_data.get("house_system", "WholeSign")
            uncertainty_minutes = birth_data.get("uncertainty_minutes", 0)
            
            # Get current time for transits
            current_jd = birth_data.get("current_jd", jd)
            
            # 1. Meta information
            meta = self._get_meta_info(birth_data)
            
            # 2. Panchanga
            panchanga = panchanga_service.get_full_panchanga(jd, lat, lon)
            
            # 3. D1 Chart
            d1_chart = chart_service.get_d1_chart(jd, lat, lon, ayanamsa)
            
            # 4. D9 Chart
            d9_chart = chart_service.get_d9_chart(jd, lat, lon, ayanamsa)
            
            # 5. Planet positions and houses
            planet_positions = ephemeris_service.get_planet_positions(jd)
            houses = ephemeris_service.get_houses(jd, lat, lon, house_system)
            planet_houses = ephemeris_service.get_planet_house_positions(planet_positions, houses)
            
            # 6. Dignities and combustion
            dignities = dignity_service.get_all_dignities(planet_positions)
            combustion = dignity_service.get_all_combustion(planet_positions)
            
            # 7. Aspects
            aspects = aspect_service.get_all_aspects(planet_positions, houses)
            
            # 8. Dasha
            dasha_info = dasha_service.get_full_dasha_info(jd, current_jd)
            
            # 9. Transits
            natal_ascendant = ephemeris_service.get_ascendant(jd, lat, lon, ayanamsa)["sign"]
            natal_moon_sign = planet_positions["Moon"]["sign"]
            transits = transit_service.get_transit_summary(current_jd, natal_ascendant, natal_moon_sign)
            
            # 10. SAV (Ashtakavarga)
            sav_data = ashtakavarga_service.calculate_sav(planet_positions)
            
            # 11. Yogas and Doshas
            yogas = yoga_service.detect_all_yogas(planet_positions, planet_houses, houses, aspects)
            
            # 12. Bhava Bala
            bhava_bala = bhavabala_service.calculate_bhava_bala(houses, planet_positions, planet_houses, aspects)
            
            # 13. Sensitivity analysis
            sensitivity = None
            if uncertainty_minutes > 0:
                sensitivity = sensitivity_service.analyze_sensitivity(jd, lat, lon, uncertainty_minutes, ayanamsa)
            
            # Assemble final result
            calc_snapshot = {
                "meta": meta,
                "panchanga": panchanga,
                "d1": d1_chart,
                "dignities": dignities,
                "combustion": combustion,
                "aspects": aspects,
                "dasha": dasha_info,
                "transits": transits,
                "d9": d9_chart,
                "sav": sav_data,
                "yogas": yogas,
                "bhava_bala": bhava_bala,
                "sensitivity": sensitivity
            }
            
            return calc_snapshot
            
        except Exception as e:
            raise CalculationError(f"Error in calculation pipeline: {str(e)}")
    
    def _get_meta_info(self, birth_data: Dict) -> Dict:
        """Get meta information for the calculation."""
        return {
            "ayanamsa": birth_data.get("ayanamsa", "Lahiri"),
            "house_system": birth_data.get("house_system", "WholeSign"),
            "timezone": birth_data.get("timezone", "UTC"),
            "dst_used": birth_data.get("dst_used", False),
            "ephemeris": "SwissEph",
            "calc_timestamp": datetime.utcnow().isoformat() + "Z",
            "ruleset_version": self.ruleset_version,
            "ephemeris_version": self.ephemeris_version,
            "uncertainty_minutes": birth_data.get("uncertainty_minutes", 0)
        }
    
    def compress_calc_snapshot(self, calc_snapshot: Dict) -> bytes:
        """Compress calculation snapshot for storage."""
        try:
            json_str = json.dumps(calc_snapshot, default=str)
            compressed = gzip.compress(json_str.encode('utf-8'))
            return compressed
        except Exception as e:
            raise CalculationError(f"Error compressing calc snapshot: {str(e)}")
    
    def decompress_calc_snapshot(self, compressed_data: bytes) -> Dict:
        """Decompress calculation snapshot from storage."""
        try:
            decompressed = gzip.decompress(compressed_data)
            json_str = decompressed.decode('utf-8')
            return json.loads(json_str)
        except Exception as e:
            raise CalculationError(f"Error decompressing calc snapshot: {str(e)}")
    
    def get_calc_summary(self, calc_snapshot: Dict) -> Dict:
        """Get summary of calculation results for LLM payload."""
        try:
            d1 = calc_snapshot["d1"]
            d9 = calc_snapshot["d9"]
            dasha = calc_snapshot["dasha"]
            transits = calc_snapshot["transits"]
            sav = calc_snapshot["sav"]
            yogas = calc_snapshot["yogas"]
            bhava_bala = calc_snapshot["bhava_bala"]
            sensitivity = calc_snapshot.get("sensitivity")
            
            # Format planets for LLM
            planets = []
            for planet in d1["planets"]:
                planets.append({
                    "name": planet["name"],
                    "sign": planet["sign"],
                    "degree": planet["degree"],
                    "dignity": calc_snapshot["dignities"].get(planet["name"], {}).get("dignity", "Neutral"),
                    "retrograde": planet["retrograde"],
                    "combust": calc_snapshot["combustion"].get(planet["name"], False),
                    "house": planet["house"]
                })
            
            # Format houses
            houses = []
            for house in d1["houses"]:
                houses.append({
                    "num": house["num"],
                    "sign": house["sign"]
                })
            
            # Format aspects
            aspects = []
            for aspect in calc_snapshot["aspects"]:
                aspects.append({
                    "from": aspect["from"],
                    "to": aspect["to"],
                    "type": aspect["type"],
                    "strength": aspect["strength"]
                })
            
            # Format yogas
            yoga_list = []
            for yoga in yogas:
                yoga_list.append({
                    "name": yoga["name"],
                    "present": yoga["present"]
                })
            
            # Format D9 better analysis
            d9_better = {}
            for planet_name in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
                if planet_name in calc_snapshot["dignities"] and planet_name in d9["planet_signs"]:
                    d1_dignity = calc_snapshot["dignities"][planet_name]["dignity"]
                    d9_sign = d9["planet_signs"][planet_name]["sign"]
                    d9_dignity = dignity_service.get_dignity(planet_name, d9["planet_signs"][planet_name]["sign_num"])
                    
                    d1_tier = dignity_service.get_dignity_tier(d1_dignity)
                    d9_tier = dignity_service.get_dignity_tier(d9_dignity)
                    
                    d9_better[planet_name] = d9_tier > d1_tier
            
            return {
                "ascendant": {
                    "sign": d1["ascendant"]["sign"],
                    "degree": d1["ascendant"]["degree"],
                    "nakshatra": d1["ascendant"]["nakshatra"],
                    "pada": d1["ascendant"]["pada"]
                },
                "d1": {
                    "planets": planets,
                    "houses": houses,
                    "aspects": aspects
                },
                "d9": {
                    "asc_sign": d9["ascendant"]["sign"],
                    "planet_signs": {k: v["sign"] for k, v in d9["planet_signs"].items()},
                    "d9_better": d9_better
                },
                "yogas": yoga_list,
                "bhava_bala": list(bhava_bala.values()),
                "timing": {
                    "current_md": dasha["current_md"],
                    "current_ad": dasha["current_ad"],
                    "next_12m_ads": dasha["next_12m_ads"]
                },
                "transits_now": {
                    "saturn_house_from_lagna": transits["saturn_house_from_lagna"],
                    "jupiter_house_from_lagna": transits["jupiter_house_from_lagna"],
                    "rahu_ketu_axis_from_lagna": transits["rahu_ketu_axis_from_lagna"],
                    "sade_sati_phase": transits["sade_sati_phase"]
                },
                "sav": sav["sav_values"],
                "sensitivity": {
                    "lagna_flip": sensitivity["lagna_flips"] if sensitivity else False,
                    "moon_flip": sensitivity["moon_sign_flips"] if sensitivity else False,
                    "dasha_boundary_risky": sensitivity["dasha_boundary_risky"] if sensitivity else False
                } if sensitivity else None
            }
            
        except Exception as e:
            raise CalculationError(f"Error creating calc summary: {str(e)}")


# Global calculation orchestrator instance
calc_orchestrator = CalcOrchestrator()

