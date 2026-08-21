"""SQLAlchemy ORM model for the cities schema.

The Cities context owns its own PostgreSQL schema. It stores normalized
canonical locations: a unique city+country pair with the raw source string and
full address for reference. There are no cross-context FKs — jobs, companies
and candidate profiles reference a city row by a plain ``city_id`` column.
"""

from __future__ import annotations

from datetime import datetime, UTC
import uuid

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.infrastructure.database.sqlalchemy_config import Base


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


uq_city_country = "uq_cities_city_country"


class CityModel(Base):
    __tablename__ = "cities"
    __table_args__ = (
        UniqueConstraint("city", "country", name=uq_city_country),
        {"schema": "city"},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid7()))
    city: Mapped[str] = mapped_column(String, nullable=False, default="")
    country: Mapped[str] = mapped_column(String, nullable=False, default="")
    original_text: Mapped[str] = mapped_column(Text, nullable=True)
    address: Mapped[str] = mapped_column(Text, nullable=True)
    hidden: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[str] = mapped_column(Text, default=_now_iso)
    updated_at: Mapped[str] = mapped_column(Text, default=_now_iso)

    aliases: Mapped[list["CityAliasModel"]] = relationship(
        back_populates="city", cascade="all, delete-orphan"
    )


class CityAliasModel(Base):
    __tablename__ = "city_aliases"
    __table_args__ = {"schema": "city"}

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid7()))
    city_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("city.cities.id"), nullable=False
    )
    alias_name: Mapped[str] = mapped_column(String, nullable=False)
    normalized_name: Mapped[str] = mapped_column(String, nullable=False, default="")
    created_at: Mapped[str] = mapped_column(Text, default=_now_iso)

    city: Mapped["CityModel"] = relationship(back_populates="aliases")


__all__ = ["CityModel", "CityAliasModel"]