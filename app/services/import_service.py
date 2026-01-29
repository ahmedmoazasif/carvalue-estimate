from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Iterable, Optional

from sqlalchemy.orm import Session

from app.models.listing import Listing
from app.repositories.dealer_repo import DealerRepository
from app.repositories.listing_repo import ListingRepository
from app.repositories.vehicle_repo import VehicleRepository


@dataclass
class ImportStats:
    total_rows: int = 0
    inserted_rows: int = 0
    skipped_rows: int = 0
    skipped_reasons: dict[str, int] = field(default_factory=dict)
    skipped_details: list[tuple[str, str]] = field(default_factory=list)

    def record_skip(self, reason: str, vin: Optional[str] = None) -> None:
        self.skipped_rows += 1
        self.skipped_reasons[reason] = self.skipped_reasons.get(reason, 0) + 1
        if vin:
            self.skipped_details.append((vin, reason))


class ImportService:
    """Import pipe-delimited vehicle listing data into the database."""

    def __init__(self, session: Session, batch_size: int = 5000):
        self.session = session
        self.batch_size = batch_size
        self.dealer_repo = DealerRepository(session)
        self.vehicle_repo = VehicleRepository(session)
        self.listing_repo = ListingRepository(session)

    @staticmethod
    def _parse_bool(value: Optional[str]) -> Optional[bool]:
        if value is None:
            return None
        val = value.strip().lower()
        if val in {"true", "1", "y", "yes"}:
            return True
        if val in {"false", "0", "n", "no"}:
            return False
        return None

    @staticmethod
    def _parse_date(value: Optional[str]):
        if not value:
            return None
        try:
            return datetime.strptime(value.strip(), "%Y-%m-%d").date()
        except ValueError:
            return None

    @staticmethod
    def _parse_price(value: Optional[str]) -> Optional[Decimal]:
        if value is None:
            return None
        try:
            return Decimal(value.strip())
        except (InvalidOperation, ValueError):
            return None

    @staticmethod
    def _parse_int(value: Optional[str]) -> Optional[int]:
        if value is None:
            return None
        try:
            return int(value.strip())
        except ValueError:
            return None

    def import_rows(self, rows: Iterable[str], dry_run: bool = False) -> ImportStats:
        stats = ImportStats()
        batch: list[Listing] = []

        for line in rows:
            stats.total_rows += 1
            parts = line.rstrip("\n").split("|")
            if len(parts) != 25:
                vin_raw = parts[0].strip().upper() if parts else None
                stats.record_skip("invalid_field_count", vin_raw)
                continue

            (
                vin,
                year,
                make,
                model,
                trim,
                dealer_name,
                dealer_street,
                dealer_city,
                dealer_state,
                dealer_zip,
                listing_price,
                listing_mileage,
                used,
                certified,
                style,
                driven_wheels,
                engine,
                fuel_type,
                exterior_color,
                interior_color,
                seller_website,
                first_seen_date,
                last_seen_date,
                _dealer_vdp_last_seen_date,
                listing_status,
            ) = parts

            vin = vin.strip().upper()
            year_val = self._parse_int(year)
            if year_val is None:
                stats.record_skip("invalid_year", vin)
                continue

            make_val = make.strip().upper()
            model_val = model.strip().upper()
            trim_val = trim.strip() or None

            if listing_price.strip() == "":
                price_val = None
            else:
                price_val = self._parse_price(listing_price)
                if price_val is None:
                    stats.record_skip("invalid_price", vin)
                    continue

            if listing_mileage.strip() == "":
                mileage_val = None
            else:
                mileage_val = self._parse_int(listing_mileage)
                if mileage_val is None:
                    stats.record_skip("invalid_mileage", vin)
                    continue

            used_val = self._parse_bool(used)
            certified_val = self._parse_bool(certified)

            if dry_run:
                stats.inserted_rows += 1
                continue

            dealer = self.dealer_repo.find_or_create(
                name=dealer_name.strip(),
                street=dealer_street.strip() or None,
                city=dealer_city.strip() or None,
                state=dealer_state.strip() or None,
                zip_code=dealer_zip.strip() or None,
                website=seller_website.strip() or None,
            )

            vehicle = self.vehicle_repo.get_or_create(
                vin=vin,
                year=year_val,
                make=make_val,
                model=model_val,
                trim=trim_val,
                style=style.strip() or None,
                driven_wheels=driven_wheels.strip() or None,
                engine=engine.strip() or None,
                fuel_type=fuel_type.strip() or None,
                exterior_color=exterior_color.strip() or None,
                interior_color=interior_color.strip() or None,
            )

            listing = Listing(
                vin=vehicle.vin,
                dealer_id=dealer.id,
                price=price_val,
                mileage=mileage_val,
                used=used_val,
                certified=certified_val,
                first_seen_date=self._parse_date(first_seen_date),
                last_seen_date=self._parse_date(last_seen_date),
                listing_status=listing_status.strip() or None,
            )

            batch.append(listing)
            stats.inserted_rows += 1

            if len(batch) >= self.batch_size:
                self.listing_repo.add_listings(batch)
                self.session.commit()
                batch.clear()

        if batch and not dry_run:
            self.listing_repo.add_listings(batch)
            self.session.commit()

        return stats
