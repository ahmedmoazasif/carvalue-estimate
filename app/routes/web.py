from flask import Blueprint, current_app, redirect, render_template, request, url_for

from app.db import get_session
from app.services.valuation_service import ValuationService

web_bp = Blueprint("web", __name__)


@web_bp.get("/")
def search():
    return render_template("search.html")


@web_bp.post("/estimate")
def estimate():
    form = request.form
    year_raw = form.get("year", "").strip()
    make_raw = form.get("make", "").strip()
    model_raw = form.get("model", "").strip()
    mileage_raw = form.get("mileage", "").strip()

    errors = []
    year = None
    mileage = None

    try:
        year = int(year_raw)
    except ValueError:
        errors.append("Year is required and must be a number.")

    if not make_raw:
        errors.append("Make is required.")
    if not model_raw:
        errors.append("Model is required.")

    if mileage_raw:
        try:
            mileage = int(mileage_raw.replace(",", ""))
        except ValueError:
            errors.append("Mileage must be a number.")

    if errors:
        return render_template("search.html", errors=errors, form=form), 400

    with get_session(current_app) as session:
        service = ValuationService(
            session=session,
            outlier_trim_pct=current_app.config["OUTLIER_TRIM_PCT"],
            depreciation_per_10k=current_app.config["DEPRECIATION_PER_10K"],
        )
        result = service.estimate_value(
            year=year,
            make=make_raw.strip().upper(),
            model=model_raw.strip().upper(),
            mileage=mileage,
        )

    if result.estimate is None:
        return render_template(
            "results.html",
            estimate=None,
            comparables=[],
            year=year,
            make=make_raw,
            model=model_raw,
        )

    return render_template(
        "results.html",
        estimate=result.estimate,
        comparables=result.comparables,
        year=year,
        make=make_raw,
        model=model_raw,
    )
