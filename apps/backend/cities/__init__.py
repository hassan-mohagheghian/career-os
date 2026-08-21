"""Cities bounded context — normalized canonical locations.

Every city referenced by jobs, companies or the candidate profile is normalized
to a unique city+country pair and linked to a row in the ``city.cities`` table.
The cities page lists them with per-city job counts, default-sorted by job
count descending.
"""

__all__: list[str] = []