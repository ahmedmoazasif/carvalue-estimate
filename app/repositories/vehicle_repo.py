from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.vehicle import Vehicle


class VehicleRepository:
    """Repository for vehicle persistence."""

    def __init__(self, session: Session):
        self.session = session

    def get_or_create(self, vin: str, **fields) -> Vehicle:
        stmt = select(Vehicle).where(Vehicle.vin == vin)
        vehicle = self.session.execute(stmt).scalar_one_or_none()
        if vehicle:
            return vehicle

        vehicle = Vehicle(vin=vin, **fields)
        self.session.add(vehicle)
        return vehicle
