from datetime import date
from typing import Optional

from sqlalchemy import BigInteger, Boolean, Date, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    vin: Mapped[str] = mapped_column(String, ForeignKey("vehicles.vin"), nullable=False)
    dealer_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("dealers.id"))
    price: Mapped[Optional[float]] = mapped_column(Numeric)
    mileage: Mapped[Optional[int]] = mapped_column(Integer)
    used: Mapped[Optional[bool]] = mapped_column(Boolean)
    certified: Mapped[Optional[bool]] = mapped_column(Boolean)
    first_seen_date: Mapped[Optional[date]] = mapped_column(Date)
    last_seen_date: Mapped[Optional[date]] = mapped_column(Date)
    listing_status: Mapped[Optional[str]] = mapped_column(String)

    vehicle = relationship("Vehicle")
    dealer = relationship("Dealer")


Index("ix_listings_price", Listing.price)
Index("ix_listings_mileage", Listing.mileage)
Index("ix_listings_listing_status", Listing.listing_status)
Index("ix_listings_last_seen_date", Listing.last_seen_date)
