"""initial_10_models

Revision ID: 0001_initial_10_models
Revises:
Create Date: 2026-10-18 08:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0001_initial_10_models'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. farm_profiles
    op.create_table(
        'farm_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('farm_uid', sa.String(length=64), nullable=False),
        sa.Column('farmer_name', sa.String(length=128), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('area_acres', sa.Float(), nullable=True),
        sa.Column('village', sa.String(length=128), nullable=True),
        sa.Column('taluk', sa.String(length=128), nullable=True),
        sa.Column('district', sa.String(length=128), nullable=True),
        sa.Column('state', sa.String(length=128), nullable=True),
        sa.Column('country', sa.String(length=64), server_default='India', nullable=True),
        sa.Column('pincode', sa.String(length=16), nullable=True),
        sa.Column('geocode_source', sa.String(length=64), server_default='nominatim', nullable=True),
        sa.Column('geocode_url', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('farm_uid')
    )

    # 2. weather_snapshots
    op.create_table(
        'weather_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('farm_id', sa.Integer(), sa.ForeignKey('farm_profiles.id'), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('temperature_c', sa.Float(), nullable=True),
        sa.Column('feels_like_c', sa.Float(), nullable=True),
        sa.Column('temp_min_c', sa.Float(), nullable=True),
        sa.Column('temp_max_c', sa.Float(), nullable=True),
        sa.Column('humidity_pct', sa.Float(), nullable=True),
        sa.Column('pressure_hpa', sa.Float(), nullable=True),
        sa.Column('rainfall_1h_mm', sa.Float(), server_default='0', nullable=True),
        sa.Column('wind_speed_ms', sa.Float(), nullable=True),
        sa.Column('wind_deg', sa.Integer(), nullable=True),
        sa.Column('cloud_pct', sa.Float(), nullable=True),
        sa.Column('uvi', sa.Float(), nullable=True),
        sa.Column('visibility_m', sa.Integer(), nullable=True),
        sa.Column('weather_main', sa.String(length=64), nullable=True),
        sa.Column('weather_desc', sa.String(length=128), nullable=True),
        sa.Column('weather_icon', sa.String(length=16), nullable=True),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('fetch_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('data_quality', sa.String(length=16), server_default='live', nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 3. weather_forecasts
    op.create_table(
        'weather_forecasts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('farm_id', sa.Integer(), sa.ForeignKey('farm_profiles.id'), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('forecast_date', sa.Date(), nullable=False),
        sa.Column('temp_min_c', sa.Float(), nullable=True),
        sa.Column('temp_max_c', sa.Float(), nullable=True),
        sa.Column('temp_avg_c', sa.Float(), nullable=True),
        sa.Column('humidity_avg_pct', sa.Float(), nullable=True),
        sa.Column('rainfall_mm', sa.Float(), server_default='0', nullable=True),
        sa.Column('wind_avg_ms', sa.Float(), nullable=True),
        sa.Column('cloud_avg_pct', sa.Float(), nullable=True),
        sa.Column('weather_desc', sa.String(length=128), nullable=True),
        sa.Column('weather_icon', sa.String(length=16), nullable=True),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('fetch_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('data_quality', sa.String(length=16), server_default='live', nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 4. soil_summaries
    op.create_table(
        'soil_summaries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('farm_id', sa.Integer(), sa.ForeignKey('farm_profiles.id'), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('nitrogen_mg_kg', sa.Float(), nullable=True),
        sa.Column('phosphorus_mg_kg', sa.Float(), nullable=True),
        sa.Column('potassium_cmolkg', sa.Float(), nullable=True),
        sa.Column('soil_ph', sa.Float(), nullable=True),
        sa.Column('organic_carbon_dg_kg', sa.Float(), nullable=True),
        sa.Column('clay_pct', sa.Float(), nullable=True),
        sa.Column('sand_pct', sa.Float(), nullable=True),
        sa.Column('silt_pct', sa.Float(), nullable=True),
        sa.Column('bulk_density', sa.Float(), nullable=True),
        sa.Column('cec_cmolkg', sa.Float(), nullable=True),
        sa.Column('soil_type', sa.String(length=64), nullable=True),
        sa.Column('moisture_pct', sa.Float(), nullable=True),
        sa.Column('source_name', sa.String(length=64), server_default='soilgrids_isric', nullable=True),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('fetch_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('data_quality', sa.String(length=16), server_default='estimated', nullable=True),
        sa.Column('lab_test_date', sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 5. crop_recommendations
    op.create_table(
        'crop_recommendations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('farm_id', sa.Integer(), sa.ForeignKey('farm_profiles.id'), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('season', sa.String(length=32), nullable=True),
        sa.Column('district', sa.String(length=128), nullable=True),
        sa.Column('top_crops_json', sa.Text(), nullable=True),
        sa.Column('all_feasible_json', sa.Text(), nullable=True),
        sa.Column('temperature_c', sa.Float(), nullable=True),
        sa.Column('humidity_pct', sa.Float(), nullable=True),
        sa.Column('soil_n', sa.Float(), nullable=True),
        sa.Column('soil_p', sa.Float(), nullable=True),
        sa.Column('soil_k', sa.Float(), nullable=True),
        sa.Column('soil_ph', sa.Float(), nullable=True),
        sa.Column('rainfall_mm', sa.Float(), nullable=True),
        sa.Column('soil_moisture', sa.Float(), nullable=True),
        sa.Column('model_version', sa.String(length=32), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('data_quality', sa.String(length=16), server_default='live', nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 6. district_crop_history
    op.create_table(
        'district_crop_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('state', sa.String(length=128), nullable=False),
        sa.Column('district', sa.String(length=128), nullable=False),
        sa.Column('crop', sa.String(length=128), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('season', sa.String(length=32), nullable=True),
        sa.Column('area_ha', sa.Float(), nullable=True),
        sa.Column('production_tonnes', sa.Float(), nullable=True),
        sa.Column('yield_kg_ha', sa.Float(), nullable=True),
        sa.Column('source_name', sa.String(length=64), nullable=True),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('fetch_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('data_quality', sa.String(length=16), server_default='official', nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('state', 'district', 'crop', 'year', 'season', name='uq_district_crop_year')
    )

    # 7. satellite_summaries
    op.create_table(
        'satellite_summaries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('farm_id', sa.Integer(), sa.ForeignKey('farm_profiles.id'), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('image_date', sa.Date(), nullable=True),
        sa.Column('ndvi', sa.Float(), nullable=True),
        sa.Column('ndwi', sa.Float(), nullable=True),
        sa.Column('evi', sa.Float(), nullable=True),
        sa.Column('cloud_cover_pct', sa.Float(), nullable=True),
        sa.Column('cloud_quality', sa.String(length=32), nullable=True),
        sa.Column('satellite_name', sa.String(length=32), nullable=True),
        sa.Column('collection_id', sa.String(length=128), nullable=True),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('fetch_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('data_quality', sa.String(length=16), server_default='estimated', nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 8. agriculture_news
    op.create_table(
        'agriculture_news',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('article_hash', sa.String(length=64), nullable=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('url', sa.Text(), nullable=True),
        sa.Column('source_name', sa.String(length=128), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('crop_tags', sa.Text(), nullable=True),
        sa.Column('state_tags', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=64), nullable=True),
        sa.Column('sentiment', sa.String(length=16), nullable=True),
        sa.Column('alert_level', sa.String(length=16), nullable=True),
        sa.Column('fetch_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('data_quality', sa.String(length=16), server_default='live', nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('article_hash')
    )

    # 9. disease_detections
    op.create_table(
        'disease_detections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('farm_id', sa.Integer(), sa.ForeignKey('farm_profiles.id'), nullable=True),
        sa.Column('crop_name', sa.String(length=64), nullable=True),
        sa.Column('disease_name', sa.String(length=128), nullable=True),
        sa.Column('confidence_pct', sa.Float(), nullable=True),
        sa.Column('is_healthy', sa.Boolean(), server_default='0', nullable=True),
        sa.Column('treatment', sa.Text(), nullable=True),
        sa.Column('model_name', sa.String(length=64), nullable=True),
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('data_quality', sa.String(length=16), server_default='live', nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 10. farm_alerts
    op.create_table(
        'farm_alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('farm_id', sa.Integer(), sa.ForeignKey('farm_profiles.id'), nullable=True),
        sa.Column('alert_type', sa.String(length=32), nullable=True),
        sa.Column('severity', sa.String(length=16), nullable=True),
        sa.Column('title', sa.String(length=256), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('source_module', sa.String(length=64), nullable=True),
        sa.Column('resolved', sa.Boolean(), server_default='0', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('farm_alerts')
    op.drop_table('disease_detections')
    op.drop_table('agriculture_news')
    op.drop_table('satellite_summaries')
    op.drop_table('district_crop_history')
    op.drop_table('crop_recommendations')
    op.drop_table('soil_summaries')
    op.drop_table('weather_forecasts')
    op.drop_table('weather_snapshots')
    op.drop_table('farm_profiles')
