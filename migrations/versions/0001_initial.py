"""raw listings table

Revision ID: 0001_initial
Revises: None
Create Date: 2026-01-27
"""
from alembic import op
import sqlalchemy as sa


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "market_listings_raw",
        sa.Column("vin", sa.Text()),
        sa.Column("year", sa.SmallInteger()),
        sa.Column("make", sa.Text()),
        sa.Column("model", sa.Text()),
        sa.Column("trim", sa.Text()),
        sa.Column("dealer_name", sa.Text()),
        sa.Column("dealer_street", sa.Text()),
        sa.Column("dealer_city", sa.Text()),
        sa.Column("dealer_state", sa.Text()),
        sa.Column("dealer_zip", sa.Text()),
        sa.Column("listing_price", sa.Numeric()),
        sa.Column("listing_mileage", sa.Integer()),
        sa.Column("used", sa.Boolean()),
        sa.Column("certified", sa.Boolean()),
        sa.Column("style", sa.Text()),
        sa.Column("driven_wheels", sa.Text()),
        sa.Column("engine", sa.Text()),
        sa.Column("fuel_type", sa.Text()),
        sa.Column("exterior_color", sa.Text()),
        sa.Column("interior_color", sa.Text()),
        sa.Column("seller_website", sa.Text()),
        sa.Column("first_seen_date", sa.Date()),
        sa.Column("last_seen_date", sa.Date()),
        sa.Column("dealer_vdp_last_seen_date", sa.Date()),
        sa.Column("listing_status", sa.Text()),
    )


def downgrade() -> None:
    op.drop_table("market_listings_raw")
