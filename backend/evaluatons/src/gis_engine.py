import os
import re
import json
import requests
import numpy as np

from pyproj import Transformer
from shapely.geometry import Point, LineString
from shapely.ops import unary_union
from typing import List, Dict, Optional, Any

 
# 0. Helpers & Cache 

OUTPUT_ROOT = "gis_outputs"
os.makedirs(OUTPUT_ROOT, exist_ok=True)
CACHE_PATH = os.path.join(OUTPUT_ROOT, "gis_cache.json")


def _load_cache() -> Dict[str, Any]:
    if not os.path.exists(CACHE_PATH):
        return {}
    try:
        with open(CACHE_PATH, "r") as f:
            return json.load(f)
    except:
        return {}


def _save_cache(cache: Dict[str, Any]):
    try:
        with open(CACHE_PATH, "w") as f:
            json.dump(cache, f, indent=2)
    except:
        pass

# 1. Robust Geocoding (OSM) 
def geocode_location(location: str):
    url = f"https://nominatim.openstreetmap.org/search?q={location}&format=json&limit=1"
    try:
        r = requests.get(url, headers={"User-Agent": "dpr-gis"}, timeout=15)
        data = r.json()
    except:
        return None, None

    if not data:
        return None, None
    return float(data[0]["lat"]), float(data[0]["lon"])

# 2. Elevation API (Open-Meteo) 
def get_elevation(lat: float, lon: float) -> float:
    try:
        r = requests.get(
            f"https://api.open-meteo.com/v1/elevation?latitude={lat}&longitude={lon}",
            timeout=15
        ).json()
        return float(r["elevation"][0])
    except:
        return 0.0

 
# 3. DEM Grid (coarse) 
def get_dem_grid(lat: float, lon: float, steps: int = 15, delta_deg: float = 0.002):
    lats = [lat + (i - steps // 2) * delta_deg for i in range(steps)]
    lons = [lon + (j - steps // 2) * delta_deg for j in range(steps)]

    grid = np.zeros((steps, steps))
    for i, la in enumerate(lats):
        for j, lo in enumerate(lons):
            grid[i, j] = get_elevation(la, lo)
    return grid

 
# 4. Terrain Calculations (NO PLOTS) 
def estimate_cut_fill(dem):
    if dem is None:
        return None

    return {
        "mean_elevation_m": float(np.mean(dem)),
        "roughness_index": float(np.std(dem)),
        "max_elevation_m": float(np.max(dem)),
        "min_elevation_m": float(np.min(dem)),
        "estimated_cut_fill_volume_m3_per_km": float(np.std(dem) * 1500.0),
    }


def compute_landslide_risk(dem):
    if dem is None:
        return None

    dy, dx = np.gradient(dem)
    slope = np.sqrt(dx**2 + dy**2)
    steep_pixels = np.sum(slope > 25)
    total_pixels = slope.size

    return {
        "steep_area_pixels": int(steep_pixels),
        "total_pixels": int(total_pixels),
        "landslide_risk_percent": float((steep_pixels / max(1, total_pixels)) * 100),
    }


def hydrology_flow_analysis(dem):
    if dem is None:
        return None

    dy, dx = np.gradient(dem)
    flow_acc = np.abs(dx) + np.abs(dy)

    return {
        "mean_flow_direction_rad": float(np.mean(-np.arctan2(dx, dy))),
        "flow_accumulation_index": float(np.mean(flow_acc)),
        "drainage_density_index": float(np.mean(np.abs(flow_acc))),
    }


def estimate_flood_risk(dem, osm):
    if dem is None:
        return None

    mean_elev = np.mean(dem)
    low = dem < mean_elev
    dy, dx = np.gradient(dem)
    flat = np.sqrt(dx**2 + dy**2)
    pond = flat < np.percentile(flat, 40)

    mask = low & pond
    risk_index = float(np.mean(mask) * 100)

    water_bodies = 0
    for el in osm.get("elements", []):
        tags = el.get("tags") or {}
        if "water" in tags or "waterway" in tags:
            water_bodies += 1

    if water_bodies > 0:
        risk_index = min(100, risk_index + 15)

    return {
        "flood_risk_index_0_100": risk_index,
        "low_fraction": float(np.mean(low)),
        "ponding_fraction": float(np.mean(pond)),
        "water_feature_count": water_bodies,
    }
 
# 5. Overpass Query (NO IMAGES) 
def overpass_query(lat: float, lon: float, dist=2000):
    q = f"""
    [out:json];
    (
      way["highway"](around:{dist},{lat},{lon});
      way["waterway"](around:{dist},{lat},{lon});
      relation["water"](around:{dist},{lat},{lon});
    );
    out geom;
    """
    try:
        r = requests.post("http://overpass-api.de/api/interpreter", data=q, timeout=40)
        return r.json()
    except:
        return {"elements": []}


def detect_settlements(lat: float, lon: float, dist=2000):
    q = f"""
    [out:json];
    (
      node["place"](around:{dist},{lat},{lon});
      node["amenity"](around:{dist},{lat},{lon});
      way["landuse"](around:{dist},{lat},{lon});
    );
    out center;
    """
    try:
        r = requests.post("http://overpass-api.de/api/interpreter", data=q, timeout=40).json()
        names = []
        for el in r.get("elements", []):
            n = (el.get("tags") or {}).get("name")
            if n:
                names.append(n)
        return list(sorted(set(names)))
    except:
        return []

 
# 6. Terrain Risk Classification 
def classify_terrain_risk(landslide, flood, hydrology, cutfill):
    ls = (landslide or {}).get("landslide_risk_percent", 0)
    fl = (flood or {}).get("flood_risk_index_0_100", 0)
    dr = (hydrology or {}).get("drainage_density_index", 0) * 10
    rf = (cutfill or {}).get("roughness_index", 0)

    score = ls * 0.3 + fl * 0.3 + dr * 0.2 + min(30, rf * 0.5)

    tier = "Low" if score < 30 else "Moderate" if score < 60 else "High"

    return {
        "terrain_risk_tier": tier,
        "terrain_risk_score_0_100": float(min(100, score)),
        "terrain_risk_explanation": f"Score {score:.1f} from LS={ls:.1f}, FL={fl:.1f}, DR={dr:.1f}, RF={rf:.2f}",
    }

 
# 7. Climate API 
def get_climate_profile(lat: float, lon: float):
    try:
        url = (
            "https://climate-api.open-meteo.com/v1/climate?"
            f"latitude={lat}&longitude={lon}&start_year=1991&end_year=2020&monthly_mean=precipitation_sum"
        )
        data = requests.get(url, timeout=20).json()
        precip = data.get("monthly_mean", {}).get("precipitation_sum", [])
    except:
        return None

    if not precip:
        return None

    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    pairs = list(zip(months, precip))
    pairs_sorted = sorted(pairs, key=lambda x: x[1], reverse=True)

    return {
        "avg_annual_rain_mm": float(sum(precip)),
        "wettest_months": [m for m, _ in pairs_sorted[:3]],
        "construction_window_months": [m for m in months if m not in [x[0] for x in pairs_sorted[:3]]],
    }

 
# 8. MAIN FUNCTION — NO PNG SAVED ANYWHERE 
def advanced_gis_analysis(location: str, project_text: Optional[str] = None) -> Dict[str, Any]:
    cache = _load_cache()
    key = location.lower().strip()

    if key in cache:
        return cache[key]

    lat, lon = geocode_location(location)
    if lat is None:
        return {"error": "Location not found", "location": location}

    dem = get_dem_grid(lat, lon)
    elevation = get_elevation(lat, lon)

    cutfill = estimate_cut_fill(dem)
    landslide = compute_landslide_risk(dem)
    hydrology = hydrology_flow_analysis(dem)

    osm = overpass_query(lat, lon)
    flood = estimate_flood_risk(dem, osm)

    settlements = detect_settlements(lat, lon)
    road_count = sum(
        1 for el in osm.get("elements", [])
        if el.get("type") == "way" and "highway" in (el.get("tags") or {})
    )
    connectivity_score = min(10, road_count / 3)

    climate = get_climate_profile(lat, lon)
    terrain = classify_terrain_risk(landslide, flood, hydrology, cutfill)

    result = {
        "location": location,
        "coordinates": {"lat": lat, "lon": lon},
        "elevation_m": elevation,
        "cut_fill_estimation": cutfill,
        "landslide_risk": landslide,
        "hydrology_analysis": hydrology,
        "flood_risk": flood,
        "terrain_risk_classification": terrain,
        "nearby_settlements": settlements,
        "road_count": road_count,
        "connectivity_score_0_10": connectivity_score,
        "climate_profile": climate,
    }

    cache[key] = result
    _save_cache(cache)

    return result
