"""initial

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
        "vehicles",
        sa.Column("vin", sa.String(), primary_key=True),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("make", sa.String(), nullable=False),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("trim", sa.String()),
        sa.Column("style", sa.String()),
        sa.Column("driven_wheels", sa.String()),
        sa.Column("engine", sa.String()),
        sa.Column("fuel_type", sa.String()),
        sa.Column("exterior_color", sa.String()),
        sa.Column("interior_color", sa.String()),
    )
    op.create_index(
        "ix_vehicles_year_make_model",
        "vehicles",
        ["year", "make", "model"],
    )

    op.create_table(
        "dealers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("street", sa.String()),
        sa.Column("city", sa.String()),
        sa.Column("state", sa.String()),
        sa.Column("zip", sa.String()),
        sa.Column("website", sa.String()),
    )

    op.create_table(
        "listings",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("vin", sa.String(), sa.ForeignKey("vehicles.vin"), nullable=False),
        sa.Column("dealer_id", sa.Integer(), sa.ForeignKey("dealers.id")),
        sa.Column("price", sa.Numeric()),
        sa.Column("mileage", sa.Integer()),
        sa.Column("used", sa.Boolean()),
        sa.Column("certified", sa.Boolean()),
        sa.Column("first_seen_date", sa.Date()),
        sa.Column("last_seen_date", sa.Date()),
        sa.Column("listing_status", sa.String()),
    )
    op.create_index("ix_listings_price", "listings", ["price"])
    op.create_index("ix_listings_mileage", "listings", ["mileage"])
    op.create_index("ix_listings_listing_status", "listings", ["listing_status"])
    op.create_index("ix_listings_last_seen_date", "listings", ["last_seen_date"])


def downgrade() -> None:
    op.drop_index("ix_listings_last_seen_date", table_name="listings")
    op.drop_index("ix_listings_listing_status", table_name="listings")
    op.drop_index("ix_listings_mileage", table_name="listings")
    op.drop_index("ix_listings_price", table_name="listings")
    op.drop_table("listings")
    op.drop_table("dealers")
    op.drop_index("ix_vehicles_year_make_model", table_name="vehicles")
    op.drop_table("vehicles")
