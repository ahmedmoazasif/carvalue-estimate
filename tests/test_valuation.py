from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.dealer import Dealer
from app.models.listing import Listing
from app.models.vehicle import Vehicle
from app.services.valuation_service import ValuationService


def seed_listings(session: Session):
    dealer = Dealer(name="Dealer", street=None, city="Austin", state="TX", zip=None, website=None)
    session.add(dealer)
    session.flush()

    for idx, price in enumerate([8000, 10000, 11000, 12000, 13000, 14000, 15000, 16000, 17000, 30000]):
        vin = f"VIN{idx}"
        vehicle = Vehicle(
            vin=vin,
            year=2018,
            make="TOYOTA",
            model="CAMRY",
            trim="LE",
            style=None,
            driven_wheels=None,
            engine=None,
            fuel_type=None,
            exterior_color=None,
            interior_color=None,
        )
        session.add(vehicle)
        session.add(
            Listing(
                vin=vin,
                dealer_id=dealer.id,
                price=Decimal(price),
                mileage=40000 + idx * 1000,
                used=True,
                certified=False,
                listing_status="active",
            )
        )
    session.commit()


def test_valuation_outlier_trim_and_rounding(session):
    seed_listings(session)
    service = ValuationService(session=session, outlier_trim_pct=0.1, depreciation_per_10k=300)
    result = service.estimate_value(year=2018, make="TOYOTA", model="CAMRY")

    assert result.estimate is not None
    # After trimming 10% (1 low + 1 high): average of 8 middle prices
    expected_avg = Decimal(sum([10000, 11000, 12000, 13000, 14000, 15000, 16000, 17000])) / Decimal(8)
    assert result.estimate == (expected_avg / Decimal(100)).quantize(Decimal("1")) * Decimal(100)


def test_mileage_adjustment_decreases_with_higher_mileage(session):
    seed_listings(session)
    service = ValuationService(session=session, outlier_trim_pct=0.0, depreciation_per_10k=300)
    base = service.estimate_value(year=2018, make="TOYOTA", model="CAMRY", mileage=40000).estimate
    higher = service.estimate_value(year=2018, make="TOYOTA", model="CAMRY", mileage=80000).estimate

    assert base is not None
    assert higher is not None
    assert higher < base
