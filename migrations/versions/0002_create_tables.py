"""create tables

Revision ID: 0002_create_tables
Revises: 0001_initial
Create Date: 2026-01-27
"""
from alembic import op
import sqlalchemy as sa


revision = "0002_create_tables"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vehicles",
        sa.Column("vin", sa.String(), primary_key=True),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("make", sa.String()),
        sa.Column("model", sa.String()),
        sa.Column("trim", sa.String()),
        sa.Column("style", sa.String()),
        sa.Column("driven_wheels", sa.String()),
        sa.Column("engine", sa.String()),
        sa.Column("fuel_type", sa.String()),
        sa.Column("exterior_color", sa.String()),
        sa.Column("interior_color", sa.String()),
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
        sa.Column("vin", sa.String(), sa.ForeignKey(
            "vehicles.vin"), nullable=False),
        sa.Column("dealer_id", sa.Integer(), sa.ForeignKey("dealers.id")),
        sa.Column("price", sa.Numeric()),
        sa.Column("mileage", sa.Integer()),
        sa.Column("used", sa.Boolean()),
        sa.Column("certified", sa.Boolean()),
        sa.Column("first_seen_date", sa.Date()),
        sa.Column("last_seen_date", sa.Date()),
        sa.Column("listing_status", sa.String()),
    )

    op.execute(
        """
        INSERT INTO vehicles (
            vin,
            year,
            make,
            model,
            trim,
            style,
            driven_wheels,
            engine,
            fuel_type,
            exterior_color,
            interior_color
        )
        SELECT DISTINCT ON (UPPER(TRIM(vin)))
            UPPER(TRIM(vin)) AS vin,
            year,
            UPPER(TRIM(make)) AS make,
            UPPER(TRIM(model)) AS model,
            NULLIF(TRIM(trim), '') AS trim,
            NULLIF(TRIM(style), '') AS style,
            NULLIF(TRIM(driven_wheels), '') AS driven_wheels,
            NULLIF(TRIM(engine), '') AS engine,
            NULLIF(TRIM(fuel_type), '') AS fuel_type,
            NULLIF(TRIM(exterior_color), '') AS exterior_color,
            NULLIF(TRIM(interior_color), '') AS interior_color
        FROM market_listings_raw
        WHERE vin IS NOT NULL AND TRIM(vin) <> ''
        """
    )

    op.execute(
        """
        INSERT INTO dealers (name, street, city, state, zip, website)
        SELECT DISTINCT
            NULLIF(TRIM(dealer_name), '') AS name,
            NULLIF(TRIM(dealer_street), '') AS street,
            NULLIF(TRIM(dealer_city), '') AS city,
            NULLIF(TRIM(dealer_state), '') AS state,
            NULLIF(TRIM(dealer_zip), '') AS zip,
            NULLIF(TRIM(seller_website), '') AS website
        FROM market_listings_raw
        WHERE dealer_name IS NOT NULL AND TRIM(dealer_name) <> ''
        """
    )

    op.execute(
        """
        INSERT INTO listings (
            vin,
            dealer_id,
            price,
            mileage,
            used,
            certified,
            first_seen_date,
            last_seen_date,
            listing_status
        )
        SELECT
            UPPER(TRIM(r.vin)) AS vin,
            d.id AS dealer_id,
            r.listing_price,
            r.listing_mileage,
            r.used,
            r.certified,
            r.first_seen_date,
            r.last_seen_date,
            NULLIF(TRIM(r.listing_status), '') AS listing_status
        FROM market_listings_raw r
        LEFT JOIN dealers d ON
            d.name = NULLIF(TRIM(r.dealer_name), '')
            AND d.street IS NOT DISTINCT FROM NULLIF(TRIM(r.dealer_street), '')
            AND d.city IS NOT DISTINCT FROM NULLIF(TRIM(r.dealer_city), '')
            AND d.state IS NOT DISTINCT FROM NULLIF(TRIM(r.dealer_state), '')
            AND d.zip IS NOT DISTINCT FROM NULLIF(TRIM(r.dealer_zip), '')
            AND d.website IS NOT DISTINCT FROM NULLIF(TRIM(r.seller_website), '')
        WHERE r.vin IS NOT NULL AND TRIM(r.vin) <> ''
        """
    )

    op.create_index(
        "ix_vehicles_year_make_model",
        "vehicles",
        ["year", "make", "model"],
    )
    op.create_index("ix_listings_price", "listings", ["price"])
    op.create_index("ix_listings_mileage", "listings", ["mileage"])
    op.create_index("ix_listings_listing_status",
                    "listings", ["listing_status"])
    op.create_index("ix_listings_last_seen_date",
                    "listings", ["last_seen_date"])


def downgrade() -> None:
    op.drop_index("ix_listings_last_seen_date", table_name="listings")
    op.drop_index("ix_listings_listing_status", table_name="listings")
    op.drop_index("ix_listings_mileage", table_name="listings")
    op.drop_index("ix_listings_price", table_name="listings")
    op.drop_table("listings")
    op.drop_table("dealers")
    op.drop_index("ix_vehicles_year_make_model", table_name="vehicles")
    op.drop_table("vehicles")
