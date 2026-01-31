from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from statistics import mean
from typing import Optional

import numpy as np
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
    ):
        self.session = session
        self.repo = ListingRepository(session)

    @staticmethod
    def _trim_outliers(
        rows: list[tuple], stddevs: float = 3.0
    ) -> list[tuple]:
        if not rows:
            return []
        prices = [float(row[0].price)
                  for row in rows if row[0].price is not None]
        if not prices:
            return rows
        mean_price = float(np.mean(prices))
        std_price = float(np.std(prices))
        if std_price == 0:
            return rows
        lower = mean_price - (stddevs * std_price)
        upper = mean_price + (stddevs * std_price)
        filtered = [row for row in rows if lower <=
                    float(row[0].price) <= upper]
        return filtered or rows

    @staticmethod
    def _round_to_nearest_100(value: Decimal) -> Decimal:
        return (value / Decimal("100")).quantize(Decimal("1")) * Decimal("100")

    @staticmethod
    def _linear_regression(
        mileages: list[int], prices: list[Decimal]
    ) -> tuple[Decimal, Decimal]:
        if not mileages or not prices or len(mileages) != len(prices):
            raise ValueError(
                "Mileage and price lists must be the same length.")
        x = np.array(mileages, dtype=float)
        y = np.array([float(price) for price in prices], dtype=float)
        slope, intercept = np.polyfit(x, y, deg=1)
        return Decimal(str(slope)), Decimal(str(intercept))

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
        trimmed_rows = self._trim_outliers(sorted_rows, 1.0)
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

        slope, intercept = self._linear_regression(
            trimmed_mileages, trimmed_prices)
        target_mileage = (
            Decimal(mileage)
            if mileage is not None
            else Decimal(str(mean(trimmed_mileages)))
        )
        estimate_value = intercept + (slope * target_mileage)

        estimate = self._round_to_nearest_100(estimate_value)

        closest_rows = sorted(
            trimmed_rows,
            key=lambda row: abs(row[0].price - estimate),
        )[:100]
        comparables = []
        for listing, vehicle, dealer in closest_rows:
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
