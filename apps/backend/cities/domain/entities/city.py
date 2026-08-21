"""City domain entity for the Cities bounded context.

A City is a normalized, unique canonical location: a city name plus its
country. Raw source strings (original_text) and full addresses are kept on the
same row so the cities page can show them (truncated) while jobs, companies and
the candidate profile only reference the row by ``city_id`` (a plain logical
column — no cross-context FK, AGENTS.md rule 15).
"""

from __future__ import annotations

import re
from datetime import datetime, UTC
from typing import Any


class City:
    """A single canonical city row."""

    def __init__(
        self,
        id: str | None = None,
        city: str = "",
        country: str = "",
        original_text: str = "",
        address: str = "",
        hidden: bool = False,
        created_at: str | None = None,
        updated_at: str | None = None,
    ):
        self.id = id
        self.city = city
        self.country = country
        self.original_text = original_text
        self.address = address
        self.hidden = hidden
        self.created_at = created_at or datetime.now(UTC).isoformat()
        self.updated_at = updated_at or self.created_at

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "city": self.city,
            "country": self.country,
            "original_text": self.original_text,
            "address": self.address,
            "hidden": self.hidden,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class CityNormalizer:
    """Normalize a raw location string to a unique canonical ``(city, country)``.

    Normalization means extracting a city and a country in a unique form for
    each city: aliases collapse to one canonical name (München → Munich) and
    known cities map to their country (Berlin → Germany). Unrecognized values
    are title-cased and kept as the city with an empty country.
    """

    # alias → canonical city name (lowercase alias keys)
    ALIASES: dict[str, str] = {
        "münchen": "Munich",
        "munich": "Munich",
        "köln": "Cologne",
        "cologne": "Cologne",
        "zürich": "Zurich",
        "zurich": "Zurich",
        "wien": "Vienna",
        "vienna": "Vienna",
        "nürnberg": "Nuremberg",
        "nuremberg": "Nuremberg",
        "düsseldorf": "Duesseldorf",
        "duesseldorf": "Duesseldorf",
        "frankfurt am main": "Frankfurt",
        "frankfurt a. m.": "Frankfurt",
        "den haag": "The Hague",
        "the hague": "The Hague",
    }

    # canonical city → country
    CITY_COUNTRIES: dict[str, str] = {
        "Berlin": "Germany",
        "Munich": "Germany",
        "Hamburg": "Germany",
        "Heidelberg": "Germany",
        "Frankfurt": "Germany",
        "Cologne": "Germany",
        "Stuttgart": "Germany",
        "Leipzig": "Germany",
        "Dortmund": "Germany",
        "Magdeburg": "Germany",
        "Dresden": "Germany",
        "Nuremberg": "Germany",
        "Duesseldorf": "Germany",
        "Bremen": "Germany",
        "Bonn": "Germany",
        "Hannover": "Germany",
        "Mannheim": "Germany",
        "Karlsruhe": "Germany",
        "Bochum": "Germany",
        "Essen": "Germany",
        "Aachen": "Germany",
        "Muenster": "Germany",
        "Freiburg": "Germany",
        "Augsburg": "Germany",
        "Erlangen": "Germany",
        "Regensburg": "Germany",
        "Bielefeld": "Germany",
        "Kiel": "Germany",
        "Rostock": "Germany",
        "Chemnitz": "Germany",
        "Potsdam": "Germany",
        "Darmstadt": "Germany",
        "Ulm": "Germany",
        "Ingolstadt": "Germany",
        "Wuerzburg": "Germany",
        "Saarbruecken": "Germany",
        "Madrid": "Spain",
        "Barcelona": "Spain",
        "Valencia": "Spain",
        "Paris": "France",
        "Lyon": "France",
        "London": "UK",
        "Manchester": "UK",
        "Amsterdam": "Netherlands",
        "Rotterdam": "Netherlands",
        "Eindhoven": "Netherlands",
        "Utrecht": "Netherlands",
        "The Hague": "Netherlands",
        "Vienna": "Austria",
        "Zurich": "Switzerland",
        "Geneva": "Switzerland",
        "Dublin": "Ireland",
        "Lisbon": "Portugal",
        "Prague": "Czechia",
        "Warsaw": "Poland",
        "Krakow": "Poland",
        "Stockholm": "Sweden",
        "Copenhagen": "Denmark",
        "Helsinki": "Finland",
        "Oslo": "Norway",
        "Milan": "Italy",
        "Rome": "Italy",
        "Brussels": "Belgium",
        "Antwerp": "Belgium",
        "Ghent": "Belgium",
        "Luxembourg": "Luxembourg",
    }

    COUNTRY_ONLY: frozenset[str] = frozenset(
        {
            "germany",
            "netherlands",
            "spain",
            "france",
            "uk",
            "united kingdom",
            "austria",
            "switzerland",
            "ireland",
            "portugal",
            "czechia",
            "czech republic",
            "poland",
            "sweden",
            "denmark",
            "finland",
            "norway",
            "italy",
            "belgium",
            "luxembourg",
            "europe",
            "remote germany",
            "remote",
        }
    )

    @classmethod
    def _canonical_city(cls, raw: str) -> str:
        key = raw.strip().lower()
        return cls.ALIASES.get(key, raw.strip().title())

    @classmethod
    def normalize(cls, raw: str | None) -> tuple[str, str]:
        """Return ``(city, country)`` for a raw location string."""
        if not raw:
            return "", ""
        text = raw.strip()
        if not text:
            return "", ""
        lower = text.lower()

        # Remote variants carry no city.
        if lower in {"remote", "remote germany", "work from anywhere", "fully remote"}:
            return "Remote", "Germany" if lower == "remote germany" else ""

        # Country-only tokens.
        if lower in cls.COUNTRY_ONLY and lower != "europe":
            country = lower.title()
            if lower == "uk" or lower == "united kingdom":
                country = "UK"
            elif lower == "czech republic":
                country = "Czechia"
            return "", country

        # "City, Region, Country" / "City, Country" — comma-separated: last is
        # the country, first is the city.
        comma_parts = [p.strip() for p in text.split(",") if p.strip()]
        if len(comma_parts) >= 2:
            city = cls._canonical_city(comma_parts[0])
            return city, cls._canonical_country(comma_parts[-1])

        # "/"- or "|"-separated lists of cities (e.g. "Berlin / Munich"): take
        # the first city and map its country from the known list.
        parts = [p.strip() for p in re.split(r"[/|]", text) if p.strip()]
        if parts:
            city = cls._canonical_city(parts[0])
            return city, cls.CITY_COUNTRIES.get(city, "")

        return "", ""

    @classmethod
    def _canonical_country(cls, raw: str) -> str:
        lower = raw.strip().lower()
        if lower in {"uk", "united kingdom", "england"}:
            return "UK"
        if lower == "czech republic":
            return "Czechia"
        if lower == "the netherlands" or lower == "holland":
            return "Netherlands"
        if lower == "uae" or lower == "united arab emirates":
            return "UAE"
        return raw.strip().title()


__all__ = ["City", "CityNormalizer"]