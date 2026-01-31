import os


class Config:
    """Application configuration loaded from environment variables."""

    DATABASE_URL = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/carvalue",
    )
    FLASK_ENV = os.environ.get("FLASK_ENV", "development")
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")
    OUTLIER_TRIM_PCT = float(os.environ.get("OUTLIER_TRIM_PCT", "0.05"))
    DEPRECIATION_PER_10K = int(os.environ.get("DEPRECIATION_PER_10K", "300"))
