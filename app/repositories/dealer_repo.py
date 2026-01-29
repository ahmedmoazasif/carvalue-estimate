from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.dealer import Dealer


class DealerRepository:
    """Repository for dealer persistence."""

    def __init__(self, session: Session):
        self.session = session

    def find_or_create(
        self,
        name: str,
        street: Optional[str],
        city: Optional[str],
        state: Optional[str],
        zip_code: Optional[str],
        website: Optional[str],
    ) -> Dealer:
        stmt = select(Dealer).where(
            Dealer.name == name,
            Dealer.street == street,
            Dealer.city == city,
            Dealer.state == state,
            Dealer.zip == zip_code,
            Dealer.website == website,
        )
        dealer = self.session.execute(stmt).scalar_one_or_none()
        if dealer:
            return dealer

        dealer = Dealer(
            name=name,
            street=street,
            city=city,
            state=state,
            zip=zip_code,
            website=website,
        )
        self.session.add(dealer)
        self.session.flush()
        return dealer
