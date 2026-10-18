"""
AGRIFY — Database Configuration & Environment Management
Module: backend/database_config.py

Handles reliable environment-driven database configuration for development,
testing, and production environments.
Normalizes PostgreSQL driver schemes (postgres:// -> postgresql://) and
configures connection pooling, pre-ping, and timeouts.
"""

import os
import re


def normalize_database_url(url: str) -> str:
    """
    Ensure the database URL conforms to modern SQLAlchemy driver specifications.
    Render, Heroku, and Supabase often output 'postgres://' which SQLAlchemy 2.x
    rejects in favor of 'postgresql://' or 'postgresql+psycopg2://'.
    """
    if not url or not isinstance(url, str):
        return ""
    cleaned = url.strip()
    if cleaned.startswith("postgres://"):
        cleaned = re.sub(r"^postgres://", "postgresql://", cleaned, count=1)
    return cleaned


def get_database_uri() -> str:
    """
    Retrieve the normalized database URI from environment variables.
    Defaults to empty string if not configured (stateless operation).
    """
    raw_url = os.getenv("DATABASE_URL", "").strip()
    return normalize_database_url(raw_url)


def get_sqlalchemy_engine_options(database_uri: str) -> dict:
    """
    Build connection pool options suitable for the specific database engine.
    - SQLite: avoids pool_size/max_overflow, supports pool_pre_ping.
    - PostgreSQL: sets pool_pre_ping, connection recycling, and reasonable pool limits.
    """
    options = {
        "pool_pre_ping": True,
    }
    if database_uri.startswith("sqlite"):
        return options

    # PostgreSQL / MySQL connection pool tuning
    options.update({
        "pool_recycle": 1800,  # 30 minutes
        "pool_timeout": 30,    # seconds
    })
    return options


def is_database_enabled() -> bool:
    """Check if a database URI is configured and enabled in environment."""
    return bool(get_database_uri())


def get_persistence_mode(is_testing: bool = False, current_uri: str = "") -> str:
    """
    Determine the active persistence mode:
    - 'persistent': When external durable database URI is configured.
    - 'in_memory_test': When running under test configuration with in-memory SQLite.
    - 'stateless': When no persistent database is configured (DATABASE_URL empty).
    """
    if is_testing and "sqlite:///:memory:" in (current_uri or ""):
        return "in_memory_test"
    uri = get_database_uri()
    if uri:
        return "persistent"
    return "stateless"


def validate_production_configuration(environ=None) -> dict:
    """
    Validate production database and secret configuration.
    Raises ValueError with descriptive actionable error if production mode is active
    but configuration is missing or insecure.
    Returns status dictionary summarizing validated configuration without exposing secret values.
    """
    env = environ if environ is not None else os.environ
    flask_env = env.get("FLASK_ENV", "").strip().lower()
    app_env = env.get("ENVIRONMENT", "").strip().lower()
    is_prod = (flask_env == "production" or app_env == "production")

    if not is_prod:
        return {
            "is_production": False,
            "status": "development_or_testing",
            "database_configured": bool(get_database_uri()),
        }

    # Validate SECRET_KEY in production
    secret_key = env.get("SECRET_KEY", "").strip()
    insecure_keys = {
        "",
        "agrify-default-secret-salt-key",
        "change-me-to-something-long-and-random",
        "secret",
        "changeme",
        "development-key",
        "12345678",
    }
    if not secret_key or secret_key.lower() in insecure_keys or len(secret_key) < 16:
        raise ValueError(
            "CRITICAL SECURITY CONFIGURATION ERROR: Explicit, high-entropy SECRET_KEY "
            "(minimum 16 characters) is required when running in production mode. "
            "Never use default or placeholder keys in production."
        )

    # Validate DATABASE_URL in production if provided
    raw_db = env.get("DATABASE_URL", "").strip()
    if raw_db.startswith("sqlite"):
        raise ValueError(
            "CRITICAL DATABASE CONFIGURATION ERROR: SQLite is not supported for production deployments. "
            "Configure a durable PostgreSQL DATABASE_URL."
        )

    return {
        "is_production": True,
        "status": "production_validated",
        "database_configured": bool(raw_db),
        "persistence_mode": "persistent" if raw_db else "stateless",
    }
