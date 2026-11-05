"""Forecast ingestion, caching, and freshness verification service for FLOOD-X Phase 2.3.

Manages high-resolution Numerical Weather Prediction (NWP) forecast feeds from Open-Meteo,
validating issue times, retrieval timestamps, valid forecast horizons, and data freshness.
Enforces strict safeguards: STALE or EXPIRED classifications prevent silent usage of aged NWP batches.
"""

import os
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
import httpx

from app.schemas.prospective import ForecastHourlyPoint, ProspectiveForecastResponse

logger = logging.getLogger("floodx.prospective.forecast")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
RAW_FORECAST_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "weather", "open_meteo_forecast_pune.json")
PUNE_LAT = 18.5204
PUNE_LON = 73.8567


class ForecastService:
    """Provides validated numerical weather forecast data for the Pune / Mula-Mutha river basin.
    
    Enforces strict temporal provenance and freshness safeguards:
    - Tracks API retrieval timestamp, NWP model generation/issue timestamp, and cache timestamp.
    - Classifies freshness: LIVE_FRESH, CACHED_VALID, STALE, EXPIRED, or DATA_INSUFFICIENT.
    - Prevents silent presentation of stale or expired forecast records as live prediction.
    """

    MAX_CACHE_AGE_HOURS: float = 3.0
    MAX_FORECAST_AGE_HOURS: float = 6.0
    MAX_EXPIRED_AGE_HOURS: float = 24.0

    def __init__(self):
        self.cached_forecast: Optional[Dict[str, Any]] = None
        self.last_retrieval_utc: Optional[datetime] = None
        self.is_live_feed: bool = False
        self._freshness_override: Optional[str] = None

    def load_local_forecast_batch(self) -> Dict[str, Any]:
        """Loads verified raw forecast batch from disk."""
        if not os.path.exists(RAW_FORECAST_PATH):
            raise FileNotFoundError(f"Raw forecast file not found at {RAW_FORECAST_PATH}")

        with open(RAW_FORECAST_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data

    def fetch_live_forecast(self, timeout_sec: float = 4.0) -> Optional[Dict[str, Any]]:
        """Attempts to fetch latest live NWP forecast from Open-Meteo API.
        
        Falls back to verified local raw forecast on timeout, rate limiting, or offline mode.
        """
        api_url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": PUNE_LAT,
            "longitude": PUNE_LON,
            "hourly": (
                "temperature_2m,relative_humidity_2m,precipitation,"
                "precipitation_probability,rain,weather_code,pressure_msl,"
                "wind_speed_10m,wind_direction_10m,soil_temperature_0_to_7cm,"
                "soil_moisture_0_to_7cm,soil_moisture_7_to_28cm"
            ),
            "timezone": "Asia/Kolkata",
            "forecast_days": 7
        }

        try:
            with httpx.Client(timeout=timeout_sec) as client:
                resp = client.get(api_url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    logger.info("Successfully fetched live forecast from Open-Meteo API")
                    self.is_live_feed = True
                    return data
                else:
                    logger.warning("Open-Meteo API returned status %d. Using local verified batch.", resp.status_code)
        except Exception as e:
            logger.info("Live Open-Meteo API fetch skipped or failed (%s). Using verified local batch.", e)

        self.is_live_feed = False
        return None

    def get_forecast_data(self, force_reload: bool = False, force_local: bool = False) -> Dict[str, Any]:
        """Returns the active forecast payload, prioritizing live if available, else local batch."""
        if self.cached_forecast is not None and not force_reload and not force_local:
            return self.cached_forecast

        if not force_local:
            live_data = self.fetch_live_forecast()
            if live_data is not None:
                self.cached_forecast = live_data
                self.last_retrieval_utc = datetime.now(timezone.utc)
                self.is_live_feed = True
                return live_data

        local_data = self.load_local_forecast_batch()
        self.cached_forecast = local_data
        self.last_retrieval_utc = datetime.now(timezone.utc)
        self.is_live_feed = False
        return local_data

    def extract_issue_time_utc(self, data: Dict[str, Any]) -> datetime:
        """Extracts the model issue / generation time in UTC from forecast data payload."""
        utc_offset_sec = data.get("utc_offset_seconds", 19800)
        current = data.get("current", {})
        if "time" in current:
            # e.g. "2026-11-04T14:45"
            dt_local = datetime.fromisoformat(current["time"])
            return (dt_local - timedelta(seconds=utc_offset_sec)).replace(tzinfo=timezone.utc)

        # Fallback to first hourly time
        hourly_times = data.get("hourly", {}).get("time", [])
        if hourly_times:
            dt_local = datetime.fromisoformat(hourly_times[0])
            return (dt_local - timedelta(seconds=utc_offset_sec)).replace(tzinfo=timezone.utc)

        return datetime.now(timezone.utc)

    def evaluate_freshness(self, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Audits forecast freshness, returning status, timestamps, and warning metadata."""
        if self._freshness_override is not None:
            return {
                "data_freshness_status": self._freshness_override,
                "is_live_feed": self.is_live_feed,
                "last_retrieval_utc": (self.last_retrieval_utc or datetime.now(timezone.utc)).isoformat(),
                "forecast_issue_time_utc": datetime.now(timezone.utc).isoformat(),
                "cache_age_hours": 0.1,
                "forecast_age_hours": 0.1,
                "max_cache_age_hours": self.MAX_CACHE_AGE_HOURS,
                "max_forecast_age_hours": self.MAX_FORECAST_AGE_HOURS,
                "freshness_warning": f"Override active: {self._freshness_override}"
            }

        if data is None:
            try:
                data = self.get_forecast_data()
            except Exception as e:
                return {
                    "data_freshness_status": "DATA_INSUFFICIENT",
                    "is_live_feed": False,
                    "last_retrieval_utc": None,
                    "forecast_issue_time_utc": None,
                    "cache_age_hours": None,
                    "forecast_age_hours": None,
                    "max_cache_age_hours": self.MAX_CACHE_AGE_HOURS,
                    "max_forecast_age_hours": self.MAX_FORECAST_AGE_HOURS,
                    "freshness_warning": f"Unable to retrieve forecast data: {str(e)}"
                }

        now_utc = datetime.now(timezone.utc)
        retrieval_utc = self.last_retrieval_utc or now_utc
        cache_age_hours = round(max(0.0, (now_utc - retrieval_utc).total_seconds() / 3600.0), 2)

        issue_utc = self.extract_issue_time_utc(data)
        forecast_age_hours = round(max(0.0, (now_utc - issue_utc).total_seconds() / 3600.0), 2)

        # Freshness determination logic
        if self.is_live_feed:
            if cache_age_hours <= self.MAX_CACHE_AGE_HOURS:
                status = "LIVE_FRESH"
                warning = None
            else:
                status = "STALE"
                warning = f"Live forecast cache age ({cache_age_hours}h) exceeds maximum allowed ({self.MAX_CACHE_AGE_HOURS}h)."
        else:
            if forecast_age_hours <= self.MAX_FORECAST_AGE_HOURS and cache_age_hours <= self.MAX_CACHE_AGE_HOURS:
                status = "CACHED_VALID"
                warning = None
            elif forecast_age_hours <= self.MAX_EXPIRED_AGE_HOURS:
                status = "STALE"
                warning = (
                    f"Forecast batch is STALE (model run is {forecast_age_hours}h old; threshold is {self.MAX_FORECAST_AGE_HOURS}h). "
                    "Live Open-Meteo connection unavailable; results reflect previous model cycle."
                )
            else:
                status = "EXPIRED"
                warning = (
                    f"Forecast batch is EXPIRED (model run is {forecast_age_hours}h old; exceeds 24h limit). "
                    "Must NOT be used for current flood alert decision-making."
                )

        return {
            "data_freshness_status": status,
            "is_live_feed": self.is_live_feed,
            "last_retrieval_utc": retrieval_utc.isoformat(),
            "forecast_issue_time_utc": issue_utc.isoformat(),
            "cache_age_hours": cache_age_hours,
            "forecast_age_hours": forecast_age_hours,
            "max_cache_age_hours": self.MAX_CACHE_AGE_HOURS,
            "max_forecast_age_hours": self.MAX_FORECAST_AGE_HOURS,
            "freshness_warning": warning
        }

    def set_freshness_override(self, status: Optional[str]) -> None:
        """Sets an explicit freshness override (useful for testing and scenario simulation)."""
        self._freshness_override = status

    def parse_forecast_points(self, max_hours: int = 48) -> List[ForecastHourlyPoint]:
        """Parses raw hourly forecast arrays into strongly typed ForecastHourlyPoint records."""
        data = self.get_forecast_data()
        hourly = data.get("hourly", {})
        times = hourly.get("time", [])

        if not times:
            return []

        precip = hourly.get("precipitation", [0.0] * len(times))
        precip_prob = hourly.get("precipitation_probability", [0] * len(times))
        rain = hourly.get("rain", [0.0] * len(times))
        temp = hourly.get("temperature_2m", [25.0] * len(times))
        rh = hourly.get("relative_humidity_2m", [70.0] * len(times))
        pressure = hourly.get("pressure_msl", [948.0] * len(times))
        wind_spd = hourly.get("wind_speed_10m", [10.0] * len(times))
        wind_dir = hourly.get("wind_direction_10m", [180.0] * len(times))
        soil_m = hourly.get("soil_moisture_0_to_7cm", [0.35] * len(times))

        points = []
        utc_offset_sec = data.get("utc_offset_seconds", 19800)

        for idx, t_str in enumerate(times[:max_hours]):
            # Local time string e.g. "2026-11-04T00:00"
            dt_local = datetime.fromisoformat(t_str)
            dt_utc = dt_local - timedelta(seconds=utc_offset_sec)
            dt_utc = dt_utc.replace(tzinfo=timezone.utc)

            pt = ForecastHourlyPoint(
                valid_time_iso=t_str,
                valid_time_utc=dt_utc.isoformat(),
                lead_hours=idx + 1,
                precipitation_mm=round(float(precip[idx] if idx < len(precip) and precip[idx] is not None else 0.0), 2),
                precipitation_probability_pct=int(precip_prob[idx] if idx < len(precip_prob) and precip_prob[idx] is not None else 0),
                rain_mm=round(float(rain[idx] if idx < len(rain) and rain[idx] is not None else 0.0), 2),
                temperature_2m_c=round(float(temp[idx] if idx < len(temp) and temp[idx] is not None else 25.0), 1),
                relative_humidity_pct=round(float(rh[idx] if idx < len(rh) and rh[idx] is not None else 70.0), 1),
                surface_pressure_hpa=round(float(pressure[idx] if idx < len(pressure) and pressure[idx] is not None else 948.0), 1),
                wind_speed_10m_kmh=round(float(wind_spd[idx] if idx < len(wind_spd) and wind_spd[idx] is not None else 10.0), 1),
                wind_direction_10m_deg=round(float(wind_dir[idx] if idx < len(wind_dir) and wind_dir[idx] is not None else 180.0), 1),
                soil_moisture_0_7cm=round(float(soil_m[idx] if idx < len(soil_m) and soil_m[idx] is not None else 0.35), 4)
            )
            points.append(pt)

        return points

    def get_forecast_summary(self, max_hours: int = 48) -> ProspectiveForecastResponse:
        """Returns structured forecast summary response with explicit freshness audit metadata."""
        data = self.get_forecast_data()
        points = self.parse_forecast_points(max_hours=max_hours)
        freshness = self.evaluate_freshness(data)

        issue_time = freshness["forecast_issue_time_utc"]

        return ProspectiveForecastResponse(
            pilot_region="Pune / Mula-Mutha River Basin (18.5204°N, 73.8567°E)",
            issue_time_utc=issue_time,
            timezone=data.get("timezone", "Asia/Kolkata"),
            forecast_horizon_hours=len(points),
            record_count=len(points),
            forecast_points=points,
            data_freshness_status=freshness["data_freshness_status"],
            source_metadata={
                "provider": "Open-Meteo High-Resolution NWP (ECMWF / DWD / GFS)",
                "elevation_m": data.get("elevation", 561.0),
                "latitude": data.get("latitude", PUNE_LAT),
                "longitude": data.get("longitude", PUNE_LON),
                "is_live_feed": freshness["is_live_feed"],
                "last_retrieval_utc": freshness["last_retrieval_utc"],
                "cache_age_hours": freshness["cache_age_hours"],
                "forecast_age_hours": freshness["forecast_age_hours"],
                "freshness_warning": freshness["freshness_warning"]
            }
        )


# Singleton instance
forecast_service = ForecastService()
