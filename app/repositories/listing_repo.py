from typing import Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.dealer import Dealer
from app.models.listing import Listing
from app.models.vehicle import Vehicle


class ListingRepository:
    """Repository for listing queries and persistence."""

    def __init__(self, session: Session):
        self.session = session

    def add_listing(self, listing: Listing) -> None:
        self.session.add(listing)

    def add_listings(self, listings: list[Listing]) -> None:
        self.session.add_all(listings)

    def get_comparables(
        self,
        year: int,
        make: str,
        model: str,
        limit: Optional[int] = None,
        listing_statuses: Optional[list[str]] = None,
    ) -> list[Tuple[Listing, Vehicle, Optional[Dealer]]]:
        stmt = (
            select(Listing, Vehicle, Dealer)
            .join(Vehicle, Listing.vin == Vehicle.vin)
            .join(Dealer, Listing.dealer_id == Dealer.id, isouter=True)
            .where(
                Vehicle.year == year,
                Vehicle.make == make,
                Vehicle.model == model,
                Listing.price.is_not(None),
                Listing.mileage.is_not(None),
            )
        )

        if listing_statuses is not None:
            # TODO: confirm which listing_status values are considered active
            stmt = stmt.where(Listing.listing_status.in_(listing_statuses))

        if limit is not None:
            stmt = stmt.limit(limit)

        return list(self.session.execute(stmt).all())
