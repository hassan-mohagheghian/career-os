from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CreateLLMConfigurationRequest(BaseModel):
    name: str = Field(..., min_length=1)
    model: str = Field(..., min_length=1)
    model_version: Optional[str] = None
    enabled: bool = True


class UpdateLLMConfigurationRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    model: Optional[str] = Field(None, min_length=1)
    model_version: Optional[str] = None
    enabled: Optional[bool] = None


class LLMConfigurationResponse(BaseModel):
    id: str
    name: str
    model: str
    model_version: Optional[str] = None
    enabled: bool
    executor: str = "OpenCode"
    provider: str = "OpenAI"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CreateLLMConfigurationResponse(BaseModel):
    id: str
