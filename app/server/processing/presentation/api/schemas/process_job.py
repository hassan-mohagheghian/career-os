from __future__ import annotations

from pydantic import BaseModel


class ProcessJobResponse(BaseModel):
    execution_id: str
    status: str
