"""UUIDv7 generation utility.

UUIDv7 produces time-ordered UUIDs (sortable by creation time)
while being practically unique. Available since Python 3.13 (PEP 910).
"""

import uuid
from typing import Generator


def generate_uuid_v7() -> str:
    """Generate a UUIDv7 string."""
    return str(uuid.uuid7())


def generate_uuid_v7_bulk(count: int) -> Generator[str, None, None]:
    """Generate multiple UUIDv7 strings efficiently."""
    for _ in range(count):
        yield str(uuid.uuid7())
