# AGENTS.md (Codex Guide) — VinAudit CarValue Trial Project

This repo is a small Flask + PostgreSQL web app that:

1. Loads a pipe-delimited vehicle listings file into Postgres
2. Provides a simple UI to estimate market value for a Year+Make+Model (optional mileage)
3. Shows up to 100 comparable listings used in the estimate

**Primary reference:** `DESIGN.md`

---

## 0) Tech Stack & Constraints

- Python 3.11+
- Flask (server-rendered HTML via Jinja2)
- PostgreSQL
- SQLAlchemy 2.x + Alembic migrations
- Pytest for tests
- Prefer clean, modular code (service/repository pattern)

**Non-goals**

- Auth, roles, fancy UI framework
- Async queues (unless explicitly needed)
- Over-engineering

---

## 1) Repo Layout (Target)

Create/maintain this structure:

```
.
├─ app/
│  ├─ init.py           # create_app()
│  ├─ config.py             # env-based config
│  ├─ db.py                 # SQLAlchemy engine/session
│  ├─ models/
│  │  ├─ init.py
│  │  ├─ vehicle.py
│  │  ├─ dealer.py
│  │  ├─ listing.py
│  ├─ repositories/
│  │  ├─ listing_repo.py
│  │  ├─ dealer_repo.py
│  │  ├─ vehicle_repo.py
│  ├─ services/
│  │  ├─ valuation_service.py
│  ├─ routes/
│  │  ├─ web.py             # GET /, POST /estimate
│  ├─ templates/
│  │  ├─ search.html
│  │  ├─ results.html
│  ├─ static/
│  │  └─ styles.css
│
├─ migrations/              # Alembic
├─ tests/
│  ├─ test_valuation.py
│  ├─ test_web.py
│  └─ conftest.py
│
├─ DESIGN.md
├─ AGENTS.md
├─ requirements.txt
└─ docker-compose.yml
```

---

## 2) Environment Variables

Codex: implement config reading these:

- `DATABASE_URL` (e.g. `postgresql+psycopg3://user:pass@localhost:5432/carvalue`)
- `FLASK_ENV` (`development` / `production`)
- `SECRET_KEY` (for Flask session/CSRF if added)
- `OUTLIER_TRIM_PCT` (default `0.05`)
- `DEPRECIATION_PER_10K` (default `300`) # $300 per 10,000 miles

---

## 3) Data Model (Must Match DESIGN.md)

### Tables

- `vehicles` (vin PK, year/make/model/trim/etc)
- `dealers` (id PK, name/address/website)
- `listings` (id PK, vin FK, dealer_id FK, price, mileage, used, certified, dates, listing_status)

### Indexes

- vehicles: `(year, make, model)`
- listings: `(price)`, `(mileage)`, `(listing_status)`, `(last_seen_date)`
- optional: `(year, make, model)` via join path

---

## 4) Data Loading

Load the pipe-delimited file into `market_listings_raw` using Postgres `\copy`, then populate
`vehicles`, `dealers`, and `listings` via the SQL

---

## 5) Valuation Algorithm (Deterministic)

Codex: implement in `ValuationService`:

### Inputs

- year (int), make (str), model (str)
- mileage (optional int)

### Steps

1. Query comparable listings:
   - same year/make/model
   - price IS NOT NULL and mileage IS NOT NULL
   - optionally only “active” statuses if defined (otherwise include all)
2. If zero comps: return “no results” response (UI should show this cleanly)
3. Sort comps by price
4. Trim outliers:
   - remove top and bottom `OUTLIER_TRIM_PCT` fraction
   - ensure at least a minimum sample size remains (fallback to no trimming if too few rows)
5. Base estimate = mean(price)
6. If user mileage provided:
   - median_mileage = median(mileage) of the trimmed set
   - delta = user_mileage - median_mileage
   - adjustment = (delta / 10000) \* DEPRECIATION_PER_10K
   - adjusted_estimate = base_estimate - adjustment
7. Round final estimate to nearest `$100`
8. Return:
   - estimate
   - the 100 sample comps used (vehicle label, price, mileage, location)

**Important:** Keep it explainable and stable. No ML required.

---

## 6) Web UI Requirements

### Pages

- `GET /` renders `search.html` with:
  - Year (required)
  - Make (required)
  - Model (required)
  - Mileage (optional)

- `POST /estimate`:
  - validates inputs (server-side)
  - renders `results.html` with:
    - highlighted estimate
    - table of up to 100 comps:
      - Vehicle: `"{year} {make} {model} {trim}"`
      - Price: formatted currency
      - Mileage: formatted with commas
      - Location: `"City, State"`

UI should be simple, aligned, readable. No fancy styling needed.

---

## 7) Testing Requirements (Pytest)

Codex: implement integration tests (DB required). Use a test DB container or SQLite only if you can keep parity with Postgres features.

### Test cases

1. Valuation
   - base average correct
   - outlier trimming works
   - mileage adjustment decreases estimate when mileage increases
   - rounding to nearest 100

2. Web
   - `/` returns 200
   - `/estimate` returns 200 for valid inputs
   - shows “no results” for unknown Y/M/M

---

## 8) Coding Standards (What Codex Should Follow)

- Keep functions small and testable
- Prefer pure functions for valuation math
- Isolate DB queries in repositories
- Avoid leaking SQLAlchemy session usage into templates
- Centralize input validation
- Add docstrings for services and key functions

---

## 9) “Stop Points” (When Codex Should Ask for Clarification)

If any of these are unknown, Codex should leave TODOs instead of guessing:

- What counts as valid `listing_status` (active/sold/etc.)
- Whether to exclude certain statuses from comps
- Whether to dedupe listings per VIN or keep all rows

---

## 10) Implementation Order (Codex Task Plan)

1. Add Flask app factory + config + DB wiring
2. Create SQLAlchemy models + Alembic migrations
3. Add repo + valuation service
4. Build web routes + templates
5. Add tests (valuation, web)
6. Add docker-compose for Postgres + local run instructions

---

## 11) Definition of Done

- App runs locally with Postgres
- Loads the full dataset successfully
- UI returns estimate and up to 100 comps
- Tests pass
- Code is clean, modular, and matches `DESIGN.md`
