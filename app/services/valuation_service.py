from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from statistics import mean
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
    ):
        self.session = session
        self.outlier_trim_pct = outlier_trim_pct
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

    @staticmethod
    def _linear_regression(
        mileages: list[int], prices: list[Decimal]
    ) -> tuple[Decimal, Decimal]:
        if not mileages or not prices or len(mileages) != len(prices):
            raise ValueError("Mileage and price lists must be the same length.")

        n = Decimal(len(mileages))
        sum_x = Decimal(sum(mileages))
        sum_y = sum(prices, Decimal("0"))
        sum_xx = sum(Decimal(mileage) * Decimal(mileage) for mileage in mileages)
        sum_xy = sum(
            Decimal(mileage) * price for mileage, price in zip(mileages, prices)
        )
        denom = (n * sum_xx) - (sum_x * sum_x)
        if denom == 0:
            slope = Decimal("0")
        else:
            slope = ((n * sum_xy) - (sum_x * sum_y)) / denom
        intercept = (sum_y - (slope * sum_x)) / n
        return slope, intercept

    def estimate_value(
        self,
        year: int,
        make: str,
        model: str,
        mileage: Optional[int] = None,
    ) -> ValuationResult:
        rows = self.repo.get_comparables(
            year=year,
            make=make,
            model=model,
        )
        if not rows:
            return ValuationResult(estimate=None, comparables=[])

        sorted_rows = sorted(rows, key=lambda row: row[0].price)
        trimmed_rows = self._trim_outliers(sorted_rows, self.outlier_trim_pct)
        if not trimmed_rows:
            return ValuationResult(estimate=None, comparables=[])

        trimmed_prices = [
            row[0].price for row in trimmed_rows if row[0].price is not None
        ]
        trimmed_mileages = [
            row[0].mileage for row in trimmed_rows if row[0].mileage is not None
        ]

        if not trimmed_prices or not trimmed_mileages:
            return ValuationResult(estimate=None, comparables=[])

        slope, intercept = self._linear_regression(trimmed_mileages, trimmed_prices)
        target_mileage = (
            Decimal(mileage)
            if mileage is not None
            else Decimal(str(mean(trimmed_mileages)))
        )
        estimate_value = intercept + (slope * target_mileage)
        estimate = self._round_to_nearest_100(estimate_value)

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
