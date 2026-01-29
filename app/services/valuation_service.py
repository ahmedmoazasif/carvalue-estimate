from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from statistics import mean, median
from typing import Optional

from sqlalchemy.orm import Session

from app.repositories.listing_repo import ListingRepository


@dataclass
class ComparableListing:
    vehicle: str
    price: Decimal
    mileage: int
    location: str


@dataclass
class ValuationResult:
    estimate: Optional[Decimal]
    comparables: list[ComparableListing]


class ValuationService:
    """Compute market valuation for a vehicle using comparable listings."""

    def __init__(
        self,
        session: Session,
        outlier_trim_pct: float = 0.05,
        depreciation_per_10k: int = 300,
    ):
        self.session = session
        self.outlier_trim_pct = outlier_trim_pct
        self.depreciation_per_10k = depreciation_per_10k
        self.repo = ListingRepository(session)

    @staticmethod
    def _trim_outliers(
        sorted_rows: list[tuple], trim_pct: float
    ) -> list[tuple]:
        if not sorted_rows:
            return []
        trim_count = int(len(sorted_rows) * trim_pct)
        if trim_count == 0 or len(sorted_rows) - (trim_count * 2) < 3:
            return sorted_rows
        return sorted_rows[trim_count:-trim_count]

    @staticmethod
    def _round_to_nearest_100(value: Decimal) -> Decimal:
        return (value / Decimal("100")).quantize(Decimal("1")) * Decimal("100")

    def estimate_value(
        self,
        year: int,
        make: str,
        model: str,
        mileage: Optional[int] = None,
        listing_statuses: Optional[list[str]] = None,
    ) -> ValuationResult:
        rows = self.repo.get_comparables(
            year=year,
            make=make,
            model=model,
            listing_statuses=listing_statuses,
        )
        if not rows:
            return ValuationResult(estimate=None, comparables=[])

        sorted_rows = sorted(rows, key=lambda row: row[0].price)
        trimmed_rows = self._trim_outliers(sorted_rows, self.outlier_trim_pct)
        if not trimmed_rows:
            return ValuationResult(estimate=None, comparables=[])

        trimmed_prices = [row[0].price for row in trimmed_rows if row[0].price is not None]
        base_estimate = Decimal(str(mean(trimmed_prices)))
        adjusted_estimate = base_estimate

        if mileage is not None:
            mileages = sorted(
                row[0].mileage for row in trimmed_rows if row[0].mileage is not None
            )
            if mileages:
                median_mileage = median(mileages)
                delta = mileage - int(median_mileage)
                adjustment = (Decimal(delta) / Decimal("10000")) * Decimal(
                    self.depreciation_per_10k
                )
                adjusted_estimate = base_estimate - adjustment

        estimate = self._round_to_nearest_100(adjusted_estimate)

        comparables = []
        for listing, vehicle, dealer in trimmed_rows[:100]:
            label = f"{vehicle.year} {vehicle.make} {vehicle.model}"
            if vehicle.trim:
                label = f"{label} {vehicle.trim}"
            location = ""
            if dealer:
                city = dealer.city or ""
                state = dealer.state or ""
                if city and state:
                    location = f"{city}, {state}"
                else:
                    location = city or state
            comparables.append(
                ComparableListing(
                    vehicle=label,
                    price=listing.price,
                    mileage=listing.mileage or 0,
                    location=location,
                )
            )

        return ValuationResult(estimate=estimate, comparables=comparables)
