# src/gis_analysis.py
import os
import requests
from typing import Dict, Any, Optional

# Optional: use geopy if available for robust geocoding
try:
    from geopy.geocoders import Nominatim
    GEOPY_AVAILABLE = True
except Exception:
    GEOPY_AVAILABLE = False

OPEN_ELEVATION_URL = "https://api.open-elevation.com/api/v1/lookup"  # public service (rate limits apply)

def geocode_location(location: str, user_agent: str = "dpr-evaluator") -> Optional[Dict[str, float]]:
    """
    Geocode a location string to lat/lon using geopy (Nominatim) if available,
    otherwise try Nominatim HTTP API.
    """
    try:
        if GEOPY_AVAILABLE:
            geolocator = Nominatim(user_agent=user_agent, timeout=10)
            res = geolocator.geocode(location)
            if res:
                return {"lat": res.latitude, "lon": res.longitude, "display_name": res.address}
        # fallback to http endpoint
        url = "https://nominatim.openstreetmap.org/search"
        resp = requests.get(url, params={"q": location, "format": "json", "limit": 1}, headers={"User-Agent": user_agent}, timeout=10)
        data = resp.json()
        if data:
            return {"lat": float(data[0]["lat"]), "lon": float(data[0]["lon"]), "display_name": data[0].get("display_name", "")}
    except Exception as e:
        print("[WARN] Geocode failed:", e)
    return None

def get_elevation(lat: float, lon: float) -> Optional[float]:
    """
    Fetch elevation in meters using open-elevation public API.
    """
    try:
        resp = requests.get(OPEN_ELEVATION_URL, params={"locations": f"{lat},{lon}"}, timeout=10)
        data = resp.json()
        if "results" in data and data["results"]:
            return float(data["results"][0]["elevation"])
    except Exception as e:
        print("[WARN] Elevation fetch failed:", e)
    return None

def analyze_site(location: str) -> Dict[str, Any]:
    """
    Perform a quick GIS analysis for a given site string:
    - Geocode
    - Elevation
    - Basic flood risk heuristic (low elevation -> flagged)
    - Returns dict with keys: geocode, elevation, flood_risk, notes
    """
    result = {"geocode": None, "elevation_m": None, "flood_risk": "unknown", "notes": []}
    geo = geocode_location(location)
    if not geo:
        result["notes"].append("Geocoding failed")
        return result
    result["geocode"] = geo
    elev = get_elevation(geo["lat"], geo["lon"])
    result["elevation_m"] = elev
    # heuristic flood risk: elevation < 10m -> high risk near coast/rivers
    if elev is None:
        result["flood_risk"] = "unknown"
    elif elev < 5:
        result["flood_risk"] = "very_high"
        result["notes"].append("Very low elevation (likely flood-prone)")
    elif elev < 15:
        result["flood_risk"] = "high"
        result["notes"].append("Low elevation (possible flood risk)")
    elif elev < 50:
        result["flood_risk"] = "moderate"
    else:
        result["flood_risk"] = "low"
    return result
