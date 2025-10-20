"""Yoga and Dosha detection."""

from typing import Dict, List, Tuple
from app.services.calc_engine.dignities import dignity_service
from app.services.calc_engine.aspects import aspect_service
from app.utils.errors import CalculationError


class YogaService:
    """Service for detecting yogas and doshas."""
    
    def __init__(self):
        """Initialize Yoga service."""
        self.kendra_houses = [1, 4, 7, 10]  # Angular houses
        self.trikona_houses = [1, 5, 9]     # Trine houses
        self.upachaya_houses = [3, 6, 10, 11]  # Upachaya houses
        self.dusthana_houses = [6, 8, 12]   # Dusthana houses
    
    def detect_all_yogas(self, planet_positions: Dict, planet_houses: Dict, 
                        houses: Dict, aspects: List[Dict]) -> List[Dict]:
        """Detect all yogas and doshas."""
        try:
            yogas = []
            
            # Benefic yogas
            yogas.extend(self._detect_gaja_kesari(planet_positions, planet_houses))
            yogas.extend(self._detect_pancha_mahapurusha(planet_positions, planet_houses))
            yogas.extend(self._detect_raj_yoga(planet_positions, planet_houses, aspects))
            yogas.extend(self._detect_dhana_yoga(planet_positions, planet_houses, aspects))
            yogas.extend(self._detect_viparita_raja(planet_positions, planet_houses))
            yogas.extend(self._detect_neecha_bhanga(planet_positions, planet_houses, aspects))
            
            # Doshas
            yogas.extend(self._detect_manglik_strict(planet_positions, planet_houses))
            yogas.extend(self._detect_manglik_lenient(planet_positions, planet_houses))
            yogas.extend(self._detect_kal_sarpa_strict(planet_positions))
            yogas.extend(self._detect_kal_sarpa_loose(planet_positions))
            yogas.extend(self._detect_kemadruma(planet_positions, planet_houses))
            
            return yogas
            
        except Exception as e:
            raise CalculationError(f"Error detecting yogas: {str(e)}")
    
    def _detect_gaja_kesari(self, planet_positions: Dict, planet_houses: Dict) -> List[Dict]:
        """Detect Gaja-Kesari Yoga (Jupiter-Moon aspect)."""
        yogas = []
        
        if "Jupiter" not in planet_positions or "Moon" not in planet_positions:
            return yogas
        
        # Check if Jupiter aspects Moon (5th, 7th, 9th aspects)
        jupiter_longitude = planet_positions["Jupiter"]["longitude"]
        moon_longitude = planet_positions["Moon"]["longitude"]
        
        # Calculate angular distance
        diff = abs(jupiter_longitude - moon_longitude)
        if diff > 180:
            diff = 360 - diff
        
        # Check for 5th, 7th, or 9th aspect (120°, 180°, 240°)
        if diff in [120, 180, 240] or abs(diff - 120) <= 8 or abs(diff - 180) <= 8 or abs(diff - 240) <= 8:
            yogas.append({
                "name": "Gaja-Kesari",
                "present": True,
                "reason": "Jupiter aspects Moon"
            })
        else:
            yogas.append({
                "name": "Gaja-Kesari",
                "present": False,
                "reason": "Jupiter does not aspect Moon"
            })
        
        return yogas
    
    def _detect_pancha_mahapurusha(self, planet_positions: Dict, planet_houses: Dict) -> List[Dict]:
        """Detect Pancha-Mahapurusha Yogas."""
        yogas = []
        
        mahapurusha_planets = ["Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
        
        for planet in mahapurusha_planets:
            if planet not in planet_positions:
                continue
            
            planet_sign = planet_positions[planet]["sign"]
            planet_house = planet_houses.get(planet, 1)
            
            # Check if planet is in own/exalt sign and in angular house
            dignity = dignity_service.get_dignity(planet, planet_sign)
            is_angular = planet_house in self.kendra_houses
            
            if dignity in ["Own", "Exalted"] and is_angular:
                yogas.append({
                    "name": f"Pancha-Mahapurusha ({planet})",
                    "present": True,
                    "reason": f"{planet} in {dignity} sign in angular house {planet_house}"
                })
            else:
                yogas.append({
                    "name": f"Pancha-Mahapurusha ({planet})",
                    "present": False,
                    "reason": f"{planet} not in own/exalt sign in angular house"
                })
        
        return yogas
    
    def _detect_raj_yoga(self, planet_positions: Dict, planet_houses: Dict, aspects: List[Dict]) -> List[Dict]:
        """Detect Raj Yoga (9th lord + 10th lord conjunction/aspect)."""
        yogas = []
        
        # Get 9th and 10th house lords
        ninth_lord = self._get_house_lord(9, planet_houses, planet_positions)
        tenth_lord = self._get_house_lord(10, planet_houses, planet_positions)
        
        if not ninth_lord or not tenth_lord:
            yogas.append({
                "name": "Raj-Yoga",
                "present": False,
                "reason": "Cannot determine 9th/10th lords"
            })
            return yogas
        
        # Check if lords are same planet
        if ninth_lord == tenth_lord:
            yogas.append({
                "name": "Raj-Yoga",
                "present": True,
                "reason": f"9th and 10th lords are same planet ({ninth_lord})"
            })
            return yogas
        
        # Check for conjunction or aspect
        conjunction = self._check_conjunction(ninth_lord, tenth_lord, planet_positions)
        aspect = self._check_aspect(ninth_lord, tenth_lord, aspects)
        
        if conjunction or aspect:
            reason = "conjunction" if conjunction else "aspect"
            yogas.append({
                "name": "Raj-Yoga",
                "present": True,
                "reason": f"9th lord ({ninth_lord}) and 10th lord ({tenth_lord}) in {reason}"
            })
        else:
            yogas.append({
                "name": "Raj-Yoga",
                "present": False,
                "reason": f"9th lord ({ninth_lord}) and 10th lord ({tenth_lord}) not in conjunction/aspect"
            })
        
        return yogas
    
    def _detect_dhana_yoga(self, planet_positions: Dict, planet_houses: Dict, aspects: List[Dict]) -> List[Dict]:
        """Detect Dhana Yoga (2nd lord + 11th lord conjunction/aspect)."""
        yogas = []
        
        # Get 2nd and 11th house lords
        second_lord = self._get_house_lord(2, planet_houses, planet_positions)
        eleventh_lord = self._get_house_lord(11, planet_houses, planet_positions)
        
        if not second_lord or not eleventh_lord:
            yogas.append({
                "name": "Dhana-Yoga",
                "present": False,
                "reason": "Cannot determine 2nd/11th lords"
            })
            return yogas
        
        # Check if lords are same planet
        if second_lord == eleventh_lord:
            yogas.append({
                "name": "Dhana-Yoga",
                "present": True,
                "reason": f"2nd and 11th lords are same planet ({second_lord})"
            })
            return yogas
        
        # Check for conjunction or aspect
        conjunction = self._check_conjunction(second_lord, eleventh_lord, planet_positions)
        aspect = self._check_aspect(second_lord, eleventh_lord, aspects)
        
        if conjunction or aspect:
            reason = "conjunction" if conjunction else "aspect"
            yogas.append({
                "name": "Dhana-Yoga",
                "present": True,
                "reason": f"2nd lord ({second_lord}) and 11th lord ({eleventh_lord}) in {reason}"
            })
        else:
            yogas.append({
                "name": "Dhana-Yoga",
                "present": False,
                "reason": f"2nd lord ({second_lord}) and 11th lord ({eleventh_lord}) not in conjunction/aspect"
            })
        
        return yogas
    
    def _detect_viparita_raja(self, planet_positions: Dict, planet_houses: Dict) -> List[Dict]:
        """Detect Viparita Raja Yoga (6/8/12 lords in 6/8/12)."""
        yogas = []
        
        dusthana_lords = []
        for house in self.dusthana_houses:
            lord = self._get_house_lord(house, planet_houses, planet_positions)
            if lord:
                dusthana_lords.append((house, lord))
        
        viparita_present = False
        reasons = []
        
        for house, lord in dusthana_lords:
            lord_house = planet_houses.get(lord, 1)
            if lord_house in self.dusthana_houses:
                viparita_present = True
                reasons.append(f"{lord} (lord of {house}th) in dusthana house {lord_house}")
        
        yogas.append({
            "name": "Viparita-Raja",
            "present": viparita_present,
            "reason": "; ".join(reasons) if viparita_present else "No dusthana lords in dusthana houses"
        })
        
        return yogas
    
    def _detect_neecha_bhanga(self, planet_positions: Dict, planet_houses: Dict, aspects: List[Dict]) -> List[Dict]:
        """Detect Neecha Bhanga (cancellation of debilitation)."""
        yogas = []
        
        debilitated_planets = []
        for planet, pos_data in planet_positions.items():
            dignity = dignity_service.get_dignity(planet, pos_data["sign"])
            if dignity == "Debilitated":
                debilitated_planets.append(planet)
        
        if not debilitated_planets:
            yogas.append({
                "name": "Neecha-bhanga",
                "present": False,
                "reason": "No debilitated planets"
            })
            return yogas
        
        neecha_bhanga_present = False
        reasons = []
        
        for planet in debilitated_planets:
            # Check if debilitated planet is aspected by its own lord
            planet_sign = planet_positions[planet]["sign"]
            own_lord = self._get_sign_lord(planet_sign)
            
            if own_lord and self._check_aspect(own_lord, planet, aspects):
                neecha_bhanga_present = True
                reasons.append(f"{planet} aspected by its own lord {own_lord}")
        
        yogas.append({
            "name": "Neecha-bhanga",
            "present": neecha_bhanga_present,
            "reason": "; ".join(reasons) if neecha_bhanga_present else "No debilitated planets have neecha bhanga"
        })
        
        return yogas
    
    def _detect_manglik_strict(self, planet_positions: Dict, planet_houses: Dict) -> List[Dict]:
        """Detect Manglik Dosha (strict - from Lagna)."""
        yogas = []
        
        if "Mars" not in planet_positions:
            yogas.append({
                "name": "Manglik (Strict)",
                "present": False,
                "reason": "Mars not found"
            })
            return yogas
        
        mars_house = planet_houses.get("Mars", 1)
        manglik_houses = [1, 2, 4, 7, 8, 12]
        
        is_manglik = mars_house in manglik_houses
        
        yogas.append({
            "name": "Manglik (Strict)",
            "present": is_manglik,
            "reason": f"Mars in house {mars_house}" + (" (manglik)" if is_manglik else " (not manglik)")
        })
        
        return yogas
    
    def _detect_manglik_lenient(self, planet_positions: Dict, planet_houses: Dict) -> List[Dict]:
        """Detect Manglik Dosha (lenient - from Moon)."""
        yogas = []
        
        if "Mars" not in planet_positions or "Moon" not in planet_positions:
            yogas.append({
                "name": "Manglik (Lenient)",
                "present": False,
                "reason": "Mars or Moon not found"
            })
            return yogas
        
        mars_sign = planet_positions["Mars"]["sign"]
        moon_sign = planet_positions["Moon"]["sign"]
        
        # Calculate Mars house from Moon
        mars_house_from_moon = (mars_sign - moon_sign) % 12 + 1
        manglik_houses = [1, 2, 4, 7, 8, 12]
        
        is_manglik = mars_house_from_moon in manglik_houses
        
        yogas.append({
            "name": "Manglik (Lenient)",
            "present": is_manglik,
            "reason": f"Mars in house {mars_house_from_moon} from Moon" + (" (manglik)" if is_manglik else " (not manglik)")
        })
        
        return yogas
    
    def _detect_kal_sarpa_strict(self, planet_positions: Dict) -> List[Dict]:
        """Detect Kal Sarpa Dosha (strict - all planets between Rahu and Ketu)."""
        yogas = []
        
        if "Rahu" not in planet_positions or "Ketu" not in planet_positions:
            yogas.append({
                "name": "Kal-Sarpa (Strict)",
                "present": False,
                "reason": "Rahu or Ketu not found"
            })
            return yogas
        
        rahu_longitude = planet_positions["Rahu"]["longitude"]
        ketu_longitude = planet_positions["Ketu"]["longitude"]
        
        # Ensure Rahu is before Ketu
        if ketu_longitude < rahu_longitude:
            rahu_longitude, ketu_longitude = ketu_longitude, rahu_longitude
        
        planets_between = 0
        total_planets = 0
        
        for planet, pos_data in planet_positions.items():
            if planet in ["Rahu", "Ketu"]:
                continue
            
            planet_longitude = pos_data["longitude"]
            total_planets += 1
            
            if rahu_longitude <= planet_longitude <= ketu_longitude:
                planets_between += 1
        
        is_kal_sarpa = planets_between == total_planets
        
        yogas.append({
            "name": "Kal-Sarpa (Strict)",
            "present": is_kal_sarpa,
            "reason": f"{planets_between}/{total_planets} planets between Rahu and Ketu"
        })
        
        return yogas
    
    def _detect_kal_sarpa_loose(self, planet_positions: Dict) -> List[Dict]:
        """Detect Kal Sarpa Dosha (loose - all planets within 180° arc)."""
        yogas = []
        
        if "Rahu" not in planet_positions or "Ketu" not in planet_positions:
            yogas.append({
                "name": "Kal-Sarpa (Loose)",
                "present": False,
                "reason": "Rahu or Ketu not found"
            })
            return yogas
        
        rahu_longitude = planet_positions["Rahu"]["longitude"]
        ketu_longitude = planet_positions["Ketu"]["longitude"]
        
        # Calculate arc between Rahu and Ketu
        arc = abs(rahu_longitude - ketu_longitude)
        if arc > 180:
            arc = 360 - arc
        
        is_kal_sarpa = arc <= 180
        
        yogas.append({
            "name": "Kal-Sarpa (Loose)",
            "present": is_kal_sarpa,
            "reason": f"Rahu-Ketu arc is {arc}°"
        })
        
        return yogas
    
    def _detect_kemadruma(self, planet_positions: Dict, planet_houses: Dict) -> List[Dict]:
        """Detect Kemadruma Dosha (Moon isolated)."""
        yogas = []
        
        if "Moon" not in planet_positions:
            yogas.append({
                "name": "Kemadruma",
                "present": False,
                "reason": "Moon not found"
            })
            return yogas
        
        moon_house = planet_houses.get("Moon", 1)
        
        # Check 2nd and 12th houses from Moon
        second_from_moon = (moon_house + 1) % 12 + 1
        twelfth_from_moon = (moon_house + 11) % 12 + 1
        
        planets_in_2nd_12th = 0
        for planet, house in planet_houses.items():
            if planet == "Moon":
                continue
            if house in [second_from_moon, twelfth_from_moon]:
                planets_in_2nd_12th += 1
        
        is_kemadruma = planets_in_2nd_12th == 0
        
        yogas.append({
            "name": "Kemadruma",
            "present": is_kemadruma,
            "reason": f"Moon isolated (no planets in 2nd/12th from Moon)"
        })
        
        return yogas
    
    def _get_house_lord(self, house_num: int, planet_houses: Dict, planet_positions: Dict) -> str:
        """Get lord of a house based on sign."""
        # This is a simplified version - in practice, you'd need the house signs
        # For now, we'll use a basic mapping
        house_lords = {
            1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon",
            5: "Sun", 6: "Mercury", 7: "Venus", 8: "Mars",
            9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter"
        }
        return house_lords.get(house_num)
    
    def _get_sign_lord(self, sign_num: int) -> str:
        """Get lord of a sign."""
        sign_lords = [
            "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
            "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"
        ]
        return sign_lords[sign_num]
    
    def _check_conjunction(self, planet1: str, planet2: str, planet_positions: Dict) -> bool:
        """Check if two planets are in conjunction."""
        if planet1 not in planet_positions or planet2 not in planet_positions:
            return False
        
        pos1 = planet_positions[planet1]["longitude"]
        pos2 = planet_positions[planet2]["longitude"]
        
        diff = abs(pos1 - pos2)
        if diff > 180:
            diff = 360 - diff
        
        return diff <= 8  # 8° orb for conjunction
    
    def _check_aspect(self, planet1: str, planet2: str, aspects: List[Dict]) -> bool:
        """Check if planet1 aspects planet2."""
        for aspect in aspects:
            if aspect["from"] == planet1 and aspect["to"] == planet2:
                return True
        return False


# Global Yoga service instance
yoga_service = YogaService()

