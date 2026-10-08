"""
weather.py — Backward-compatible wrapper
Delegates to etl/weather_etl.py which uses coordinate-based fetching.
"""
from etl.weather_etl import (
    get_weather_by_coords,
    get_forecast_by_coords,
    get_weather_by_city as get_weather,
    get_forecast_by_city as get_forecast,
)

__all__ = ["get_weather", "get_forecast", "get_weather_by_coords", "get_forecast_by_coords"]