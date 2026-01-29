from decimal import Decimal

from app.models.dealer import Dealer
from app.models.listing import Listing
from app.models.vehicle import Vehicle


def seed_one_listing(session):
    dealer = Dealer(name="Dealer", street=None, city="Austin", state="TX", zip=None, website=None)
    session.add(dealer)
    session.flush()

    vehicle = Vehicle(
        vin="VIN123",
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
            vin="VIN123",
            dealer_id=dealer.id,
            price=Decimal("15000"),
            mileage=40000,
            used=True,
            certified=False,
            listing_status="active",
        )
    )
    session.commit()


def test_search_page(client):
    resp = client.get("/")
    assert resp.status_code == 200


def test_estimate_page_returns_results(client, session):
    seed_one_listing(session)
    resp = client.post(
        "/estimate",
        data={"year": "2018", "make": "Toyota", "model": "Camry"},
    )
    assert resp.status_code == 200
    assert b"Estimated Market Value" in resp.data


def test_estimate_page_no_results(client):
    resp = client.post(
        "/estimate",
        data={"year": "2019", "make": "Toyota", "model": "Camry"},
    )
    assert resp.status_code == 200
    assert b"No comparable listings" in resp.data
