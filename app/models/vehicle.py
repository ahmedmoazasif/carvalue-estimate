from typing import Optional

from sqlalchemy import Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    vin: Mapped[str] = mapped_column(String, primary_key=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    make: Mapped[str] = mapped_column(String, nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False)
    trim: Mapped[Optional[str]] = mapped_column(String)
    style: Mapped[Optional[str]] = mapped_column(String)
    driven_wheels: Mapped[Optional[str]] = mapped_column(String)
    engine: Mapped[Optional[str]] = mapped_column(String)
    fuel_type: Mapped[Optional[str]] = mapped_column(String)
    exterior_color: Mapped[Optional[str]] = mapped_column(String)
    interior_color: Mapped[Optional[str]] = mapped_column(String)


Index("ix_vehicles_year_make_model", Vehicle.year, Vehicle.make, Vehicle.model)
