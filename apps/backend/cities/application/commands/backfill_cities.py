"""Backfill existing jobs and companies into the cities table.

Normalizes each non-deleted job's ``location`` and each company's
``city``/``country`` into canonical city rows, then links them by ``city_id``
(and denormalizes city/country onto jobs for display).

Run:
    uv run python -m cities.application.commands.backfill_cities
"""

from __future__ import annotations

import sys

from sqlalchemy import select
from sqlalchemy.orm import Session

from cities.application.services.city_service import CityService
from cities.infrastructure import SQLAlchemyCityRepository
from companies.infrastructure import SQLAlchemyCompanyRepository
from companies.infrastructure.models.company_model import CompanyModel
from jobs.infrastructure import SQLAlchemyJobRepository
from jobs.infrastructure.models.job_model import JobModel
from shared.infrastructure.database.sqlalchemy_config import SessionLocal


def backfill(session: Session, dry_run: bool = False) -> dict[str, int]:
    city_service = CityService(SQLAlchemyCityRepository(session))
    job_repo = SQLAlchemyJobRepository(session)
    company_repo = SQLAlchemyCompanyRepository(session)

    stats = {"jobs": 0, "companies": 0, "cities_created": 0, "linked": 0}

    jobs = session.scalars(
        select(JobModel).where(JobModel.deleted == 0, JobModel.location.isnot(None))
    ).all()
    for job in jobs:
        location = (job.location or "").strip()
        if not location:
            continue
        row = city_service.normalize_and_ensure(location, address=location)
        if row is None:
            continue
        if not dry_run:
            job_repo.update_fields(
                job.id,
                city_id=row["id"],
                city=row["city"],
                country=row["country"],
            )
        stats["jobs"] += 1
        stats["linked"] += 1

    companies = session.scalars(
        select(CompanyModel).where(
            (CompanyModel.city.isnot(None)) | (CompanyModel.country.isnot(None))
        )
    ).all()
    for company in companies:
        city = (company.city or "").strip()
        country = (company.country or "").strip()
        if not city and not country:
            continue
        row = city_service.ensure(
            city,
            country,
            original_text=f"{city}, {country}" if city else country,
            address=company.headquarters_full or "",
        )
        if row is None:
            continue
        if not dry_run:
            company_repo.update_fields(company.id, city_id=row["id"])
        stats["companies"] += 1
        stats["linked"] += 1

    if not dry_run:
        session.commit()
    return stats


def main() -> None:
    from structlog import get_logger

    dry_run = "--dry-run" in sys.argv
    with SessionLocal() as session:
        stats = backfill(session, dry_run=dry_run)
    get_logger("cities.commands.backfill").info("backfill_complete", dry_run=dry_run, **stats)


if __name__ == "__main__":
    main()

__all__ = ["backfill"]