from pydantic import BaseModel, Field
from typing import Any


class BotStartRequest(BaseModel):
    config: str = Field(default="config.yaml")
    input: str = Field(default="")
    output: str = Field(default="")
    query: str = Field(default="")
    params: dict[str, Any] = Field(default_factory=dict)


class StatusResponse(BaseModel):
    status: str
    pid: int | None = None


class LogsResponse(BaseModel):
    logs: list[str]


class ExportsResponse(BaseModel):
    files: list[str]
