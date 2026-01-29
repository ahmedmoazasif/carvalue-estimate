from sqlalchemy import select

from app.models.dealer import Dealer
from app.models.listing import Listing
from app.models.vehicle import Vehicle
from app.services.import_service import ImportService


def test_import_skips_invalid_rows(session):
    rows = [
        "VIN1|2018|Toyota|Camry|LE|Best Dealer|123 Main|Austin|TX|78701|15000|45000|Y|N|Sedan|FWD|2.5L|Gasoline|Red|Black|example.com|2020-01-01|2020-02-01|2020-02-01|active",
        "VIN2|2019|Honda|Civic|LX|Another Dealer|456 Elm|Dallas|TX|75001||30000|Y|N|Sedan|FWD|2.0L|Gasoline|Blue|Gray|example.com|2020-01-01|2020-02-01|2020-02-01|active",
        "VIN3|2020|Ford|Focus|SE|Dealer|789 Oak|Houston|TX|77001|12000||Y|N|Sedan|FWD|2.0L|Gasoline|White|Black|example.com|2020-01-01|2020-02-01|2020-02-01|active",
    ]

    service = ImportService(session=session, batch_size=2)
    stats = service.import_rows(rows)

    assert stats.total_rows == 3
    assert stats.inserted_rows == 1
    assert stats.skipped_rows == 2
    assert stats.skipped_reasons["invalid_price"] == 1
    assert stats.skipped_reasons["invalid_mileage"] == 1

    dealers = session.execute(select(Dealer)).scalars().all()
    vehicles = session.execute(select(Vehicle)).scalars().all()
    listings = session.execute(select(Listing)).scalars().all()

    assert len(dealers) == 1
    assert len(vehicles) == 1
    assert len(listings) == 1
