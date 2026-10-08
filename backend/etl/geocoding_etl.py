"""
Agri-Connect — ETL: Nominatim Reverse Geocoding
Uses OpenStreetMap Nominatim (free, no key required)
RULE: Always use a descriptive User-Agent (required by Nominatim ToS)
"""

import requests
from datetime import datetime, timezone
import time

NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
USER_AGENT = "AgriConnect-FarmAdvisory/1.0 (contact: agriconnect@example.com)"

# Rate limit: Nominatim allows 1 req/sec
_last_call_time = 0


def reverse_geocode(lat: float, lon: float) -> dict:
    """
    Convert GPS coordinates to human-readable location using Nominatim.
    Returns village, taluk, district, state, pincode.
    """
    global _last_call_time

    # Rate limiting: 1 req/sec
    elapsed = time.time() - _last_call_time
    if elapsed < 1.1:
        time.sleep(1.1 - elapsed)
    _last_call_time = time.time()

    source_url = f"{NOMINATIM_URL}?lat={lat}&lon={lon}&format=json&addressdetails=1&zoom=14"

    try:
        resp = requests.get(
            NOMINATIM_URL,
            params={"lat": lat, "lon": lon, "format": "json", "addressdetails": 1, "zoom": 14},
            headers={"User-Agent": USER_AGENT},
            timeout=12
        )

        if resp.status_code != 200:
            return _fallback_geocode(lat, lon, source_url, f"HTTP {resp.status_code}")

        data = resp.json()
        addr = data.get("address", {})

        # Extract location fields with fallbacks
        village = (
            addr.get("village") or
            addr.get("hamlet") or
            addr.get("town") or
            addr.get("suburb") or
            addr.get("neighbourhood") or
            ""
        )
        taluk = addr.get("county") or addr.get("subdistrict") or ""
        district = (
            addr.get("district") or
            addr.get("county") or
            addr.get("city") or
            ""
        )
        state = addr.get("state") or ""
        country = addr.get("country") or "India"
        pincode = addr.get("postcode") or ""
        display_name = data.get("display_name", "")

        return {
            "ok": True,
            "village": village,
            "taluk": taluk,
            "district": district,
            "state": state,
            "country": country,
            "pincode": pincode,
            "display_name": display_name,
            "latitude": lat,
            "longitude": lon,
            "source_url": source_url,
            "fetch_timestamp": datetime.now(timezone.utc).isoformat(),
            "geocode_source": "nominatim_osm",
        }

    except requests.exceptions.Timeout:
        return _fallback_geocode(lat, lon, source_url, "timeout")
    except Exception as e:
        return _fallback_geocode(lat, lon, source_url, str(e))


def _fallback_geocode(lat, lon, source_url, reason):
    """
    Fallback when Nominatim fails: try BigDataCloud free API.
    """
    bdc_url = f"https://api.bigdatacloud.net/data/reverse-geocode-client?latitude={lat}&longitude={lon}&localityLanguage=en"
    try:
        resp = requests.get(bdc_url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "ok": True,
                "village": data.get("locality") or data.get("city") or "",
                "taluk": data.get("localityInfo", {}).get("administrative", [{}])[-1].get("name", ""),
                "district": data.get("city") or data.get("principalSubdivision") or "",
                "state": data.get("principalSubdivision") or "",
                "country": data.get("countryName") or "India",
                "pincode": "",
                "display_name": data.get("city") or f"{lat:.4f}, {lon:.4f}",
                "latitude": lat,
                "longitude": lon,
                "source_url": bdc_url,
                "fetch_timestamp": datetime.now(timezone.utc).isoformat(),
                "geocode_source": "bigdatacloud_fallback",
            }
    except Exception:
        pass

    return {
        "ok": False,
        "village": "",
        "taluk": "",
        "district": "",
        "state": "",
        "country": "India",
        "pincode": "",
        "display_name": f"{lat:.4f}°N, {lon:.4f}°E",
        "latitude": lat,
        "longitude": lon,
        "source_url": source_url,
        "fetch_timestamp": datetime.now(timezone.utc).isoformat(),
        "geocode_source": "none",
        "error_reason": reason,
    }
