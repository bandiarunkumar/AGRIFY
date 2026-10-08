"""
Agri-Connect — PostgreSQL Database Models
Based on core_tables_schema from agri_real_data_collection_pack.xlsx
All records preserve: source_url, fetch_timestamp, data_quality label
"""

import os
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def utcnow():
    return datetime.now(timezone.utc)


# ============================================================
# TABLE: farm_profiles
# GPS-captured farm with reverse-geocoded location metadata
# ============================================================
class FarmProfile(db.Model):
    __tablename__ = 'farm_profiles'

    id             = db.Column(db.Integer, primary_key=True)
    farm_uid       = db.Column(db.String(64), unique=True, nullable=False)  # hash of lat+lon+farmer
    farmer_name    = db.Column(db.String(128))
    latitude       = db.Column(db.Float, nullable=False)
    longitude      = db.Column(db.Float, nullable=False)
    area_acres     = db.Column(db.Float)

    # Reverse-geocoded fields (Nominatim / BigDataCloud)
    village        = db.Column(db.String(128))
    taluk          = db.Column(db.String(128))
    district       = db.Column(db.String(128))
    state          = db.Column(db.String(128))
    country        = db.Column(db.String(64), default='India')
    pincode        = db.Column(db.String(16))

    # Source metadata
    geocode_source = db.Column(db.String(64), default='nominatim')
    geocode_url    = db.Column(db.Text)
    created_at     = db.Column(db.DateTime(timezone=True), default=utcnow)
    updated_at     = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Relationships
    weather_snapshots   = db.relationship('WeatherSnapshot', backref='farm', lazy=True)
    soil_summaries      = db.relationship('SoilSummary', backref='farm', lazy=True)
    crop_recommendations = db.relationship('CropRecommendation', backref='farm', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'farm_uid': self.farm_uid,
            'farmer_name': self.farmer_name,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'area_acres': self.area_acres,
            'village': self.village,
            'district': self.district,
            'state': self.state,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


# ============================================================
# TABLE: weather_snapshots
# Live OpenWeather One Call data by coordinates (not city name)
# ============================================================
class WeatherSnapshot(db.Model):
    __tablename__ = 'weather_snapshots'

    id               = db.Column(db.Integer, primary_key=True)
    farm_id          = db.Column(db.Integer, db.ForeignKey('farm_profiles.id'), nullable=True)
    latitude         = db.Column(db.Float, nullable=False)
    longitude        = db.Column(db.Float, nullable=False)

    # Current conditions
    temperature_c    = db.Column(db.Float)
    feels_like_c     = db.Column(db.Float)
    temp_min_c       = db.Column(db.Float)
    temp_max_c       = db.Column(db.Float)
    humidity_pct     = db.Column(db.Float)
    pressure_hpa     = db.Column(db.Float)
    rainfall_1h_mm   = db.Column(db.Float, default=0)
    wind_speed_ms    = db.Column(db.Float)
    wind_deg         = db.Column(db.Integer)
    cloud_pct        = db.Column(db.Float)
    uvi              = db.Column(db.Float)
    visibility_m     = db.Column(db.Integer)
    weather_main     = db.Column(db.String(64))
    weather_desc     = db.Column(db.String(128))
    weather_icon     = db.Column(db.String(16))

    # Source metadata (REQUIRED on every row)
    source_url       = db.Column(db.Text)
    fetch_timestamp  = db.Column(db.DateTime(timezone=True), default=utcnow)
    data_quality     = db.Column(db.String(16), default='live')  # live | estimated | cached

    def to_dict(self):
        return {
            'temperature': self.temperature_c,
            'feels_like': self.feels_like_c,
            'temp_min': self.temp_min_c,
            'temp_max': self.temp_max_c,
            'humidity': self.humidity_pct,
            'pressure': self.pressure_hpa,
            'rainfall': self.rainfall_1h_mm,
            'wind_speed': self.wind_speed_ms,
            'wind_deg': self.wind_deg,
            'clouds': self.cloud_pct,
            'uvi': self.uvi,
            'description': self.weather_desc,
            'icon': self.weather_icon,
            'source': self.source_url,
            'fetched_at': self.fetch_timestamp.isoformat() if self.fetch_timestamp else None,
            'data_quality': self.data_quality,
        }


# ============================================================
# TABLE: weather_forecasts
# 5-day / 3-hour forecast aggregated to daily
# ============================================================
class WeatherForecast(db.Model):
    __tablename__ = 'weather_forecasts'

    id               = db.Column(db.Integer, primary_key=True)
    farm_id          = db.Column(db.Integer, db.ForeignKey('farm_profiles.id'), nullable=True)
    latitude         = db.Column(db.Float, nullable=False)
    longitude        = db.Column(db.Float, nullable=False)
    forecast_date    = db.Column(db.Date, nullable=False)
    temp_min_c       = db.Column(db.Float)
    temp_max_c       = db.Column(db.Float)
    temp_avg_c       = db.Column(db.Float)
    humidity_avg_pct = db.Column(db.Float)
    rainfall_mm      = db.Column(db.Float, default=0)
    wind_avg_ms      = db.Column(db.Float)
    cloud_avg_pct    = db.Column(db.Float)
    weather_desc     = db.Column(db.String(128))
    weather_icon     = db.Column(db.String(16))
    source_url       = db.Column(db.Text)
    fetch_timestamp  = db.Column(db.DateTime(timezone=True), default=utcnow)
    data_quality     = db.Column(db.String(16), default='live')


# ============================================================
# TABLE: soil_summaries
# SoilGrids / ISRIC free API (or SoilHive if key provided)
# Labeled as 'estimated' unless farmer uploads lab test
# ============================================================
class SoilSummary(db.Model):
    __tablename__ = 'soil_summaries'

    id                    = db.Column(db.Integer, primary_key=True)
    farm_id               = db.Column(db.Integer, db.ForeignKey('farm_profiles.id'), nullable=True)
    latitude              = db.Column(db.Float, nullable=False)
    longitude             = db.Column(db.Float, nullable=False)

    # Core nutrients
    nitrogen_mg_kg        = db.Column(db.Float)   # N (0–10000 converted)
    phosphorus_mg_kg      = db.Column(db.Float)   # P
    potassium_cmolkg      = db.Column(db.Float)   # K (exchangeable)
    soil_ph               = db.Column(db.Float)   # pH * 10 from SoilGrids
    organic_carbon_dg_kg  = db.Column(db.Float)   # OC
    clay_pct              = db.Column(db.Float)
    sand_pct              = db.Column(db.Float)
    silt_pct              = db.Column(db.Float)
    bulk_density          = db.Column(db.Float)
    cec_cmolkg            = db.Column(db.Float)
    soil_type             = db.Column(db.String(64))  # derived
    moisture_pct          = db.Column(db.Float)   # estimated from texture

    # Source metadata
    source_name           = db.Column(db.String(64), default='soilgrids_isric')
    source_url            = db.Column(db.Text)
    fetch_timestamp       = db.Column(db.DateTime(timezone=True), default=utcnow)
    data_quality          = db.Column(db.String(16), default='estimated')  # estimated | lab_tested
    lab_test_date         = db.Column(db.Date)  # if farmer uploads lab report

    def to_dict(self):
        return {
            'nitrogen': self.nitrogen_mg_kg,
            'phosphorus': self.phosphorus_mg_kg,
            'potassium': self.potassium_cmolkg,
            'ph': self.soil_ph,
            'organic_carbon': self.organic_carbon_dg_kg,
            'clay_pct': self.clay_pct,
            'sand_pct': self.sand_pct,
            'soil_type': self.soil_type,
            'moisture_pct': self.moisture_pct,
            'source': self.source_name,
            'source_url': self.source_url,
            'fetched_at': self.fetch_timestamp.isoformat() if self.fetch_timestamp else None,
            'data_quality': self.data_quality,
        }


# ============================================================
# TABLE: crop_recommendations
# AI-generated crop recommendations with suitability scores
# ============================================================
class CropRecommendation(db.Model):
    __tablename__ = 'crop_recommendations'

    id               = db.Column(db.Integer, primary_key=True)
    farm_id          = db.Column(db.Integer, db.ForeignKey('farm_profiles.id'), nullable=True)
    latitude         = db.Column(db.Float)
    longitude        = db.Column(db.Float)
    season           = db.Column(db.String(32))   # Kharif / Rabi / Zaid
    district         = db.Column(db.String(128))

    # Top 3 recommended crops (stored as JSON array)
    top_crops_json   = db.Column(db.Text)         # JSON list of crop dicts
    all_feasible_json = db.Column(db.Text)        # JSON list of all feasible crops

    # Model inputs snapshot
    temperature_c    = db.Column(db.Float)
    humidity_pct     = db.Column(db.Float)
    soil_n           = db.Column(db.Float)
    soil_p           = db.Column(db.Float)
    soil_k           = db.Column(db.Float)
    soil_ph          = db.Column(db.Float)
    rainfall_mm      = db.Column(db.Float)
    soil_moisture    = db.Column(db.Float)

    model_version    = db.Column(db.String(32))
    created_at       = db.Column(db.DateTime(timezone=True), default=utcnow)
    data_quality     = db.Column(db.String(16), default='live')


# ============================================================
# TABLE: district_crop_history
# Real ICRISAT/NHB/APEDA district production data
# ============================================================
class DistrictCropHistory(db.Model):
    __tablename__ = 'district_crop_history'

    id               = db.Column(db.Integer, primary_key=True)
    state            = db.Column(db.String(128), nullable=False)
    district         = db.Column(db.String(128), nullable=False)
    crop             = db.Column(db.String(128), nullable=False)
    year             = db.Column(db.Integer, nullable=False)
    season           = db.Column(db.String(32))
    area_ha          = db.Column(db.Float)
    production_tonnes = db.Column(db.Float)
    yield_kg_ha      = db.Column(db.Float)

    source_name      = db.Column(db.String(64))
    source_url       = db.Column(db.Text)
    fetch_timestamp  = db.Column(db.DateTime(timezone=True), default=utcnow)
    data_quality     = db.Column(db.String(16), default='official')

    __table_args__ = (
        db.UniqueConstraint('state', 'district', 'crop', 'year', 'season', name='uq_district_crop_year'),
    )


# ============================================================
# TABLE: satellite_summaries (Earth Engine)
# ============================================================
class SatelliteSummary(db.Model):
    __tablename__ = 'satellite_summaries'

    id               = db.Column(db.Integer, primary_key=True)
    farm_id          = db.Column(db.Integer, db.ForeignKey('farm_profiles.id'), nullable=True)
    latitude         = db.Column(db.Float, nullable=False)
    longitude        = db.Column(db.Float, nullable=False)

    image_date       = db.Column(db.Date)
    ndvi             = db.Column(db.Float)   # -1 to 1 vegetation index
    ndwi             = db.Column(db.Float)   # water index
    evi              = db.Column(db.Float)   # enhanced vegetation index
    cloud_cover_pct  = db.Column(db.Float)
    cloud_quality    = db.Column(db.String(32))  # clear / partial / cloudy / unavailable

    satellite_name   = db.Column(db.String(32))  # Sentinel-2 / Landsat-8
    collection_id    = db.Column(db.String(128))
    source_url       = db.Column(db.Text)
    fetch_timestamp  = db.Column(db.DateTime(timezone=True), default=utcnow)
    data_quality     = db.Column(db.String(16), default='estimated')  # live | estimated | unavailable


# ============================================================
# TABLE: agriculture_news
# Ingested + tagged news articles (from NewsAPI)
# ============================================================
class AgricultureNews(db.Model):
    __tablename__ = 'agriculture_news'

    id               = db.Column(db.Integer, primary_key=True)
    article_hash     = db.Column(db.String(64), unique=True)  # SHA256 of URL to deduplicate

    title            = db.Column(db.Text, nullable=False)
    description      = db.Column(db.Text)
    content          = db.Column(db.Text)
    url              = db.Column(db.Text)
    source_name      = db.Column(db.String(128))
    published_at     = db.Column(db.DateTime(timezone=True))

    # Tagging
    crop_tags        = db.Column(db.Text)    # comma-separated crop names
    state_tags       = db.Column(db.Text)    # comma-separated Indian states
    category         = db.Column(db.String(64))  # weather | price | disease | policy | general
    sentiment        = db.Column(db.String(16))  # positive | neutral | negative | alert
    alert_level      = db.Column(db.String(16))  # none | info | warning | danger

    fetch_timestamp  = db.Column(db.DateTime(timezone=True), default=utcnow)
    data_quality     = db.Column(db.String(16), default='live')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'url': self.url,
            'source': self.source_name,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'crop_tags': self.crop_tags,
            'category': self.category,
            'sentiment': self.sentiment,
            'alert_level': self.alert_level,
        }


# ============================================================
# TABLE: disease_detections
# Records from image upload disease detection
# ============================================================
class DiseaseDetection(db.Model):
    __tablename__ = 'disease_detections'

    id               = db.Column(db.Integer, primary_key=True)
    farm_id          = db.Column(db.Integer, db.ForeignKey('farm_profiles.id'), nullable=True)
    crop_name        = db.Column(db.String(64))
    disease_name     = db.Column(db.String(128))
    confidence_pct   = db.Column(db.Float)
    is_healthy       = db.Column(db.Boolean, default=False)
    treatment        = db.Column(db.Text)
    model_name       = db.Column(db.String(64))
    detected_at      = db.Column(db.DateTime(timezone=True), default=utcnow)
    data_quality     = db.Column(db.String(16), default='live')


# ============================================================
# TABLE: farm_alerts
# Generated alerts from weather + satellite + news + crop context
# ============================================================
class FarmAlert(db.Model):
    __tablename__ = 'farm_alerts'

    id               = db.Column(db.Integer, primary_key=True)
    farm_id          = db.Column(db.Integer, db.ForeignKey('farm_profiles.id'), nullable=True)
    alert_type       = db.Column(db.String(32))   # weather | satellite | news | disease | soil
    severity         = db.Column(db.String(16))   # info | warning | danger
    title            = db.Column(db.String(256))
    message          = db.Column(db.Text)
    source_module    = db.Column(db.String(64))
    resolved         = db.Column(db.Boolean, default=False)
    created_at       = db.Column(db.DateTime(timezone=True), default=utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.alert_type,
            'severity': self.severity,
            'title': self.title,
            'message': self.message,
            'source': self.source_module,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
