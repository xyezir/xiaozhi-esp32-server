from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

RetrievalDomain = Literal["product", "publicKnowledge", "courseCatalog"]
RetrievalKind = Literal["product", "knowledge", "courseCatalog"]


class RetrieveRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    contract_version: Literal[1] = Field(default=1, alias="contractVersion")
    request_id: str | None = Field(
        default=None,
        alias="requestId",
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9._:-]+$",
    )
    query: str = Field(min_length=2, max_length=500)
    domains: list[RetrievalDomain] = Field(
        default_factory=lambda: ["product", "publicKnowledge", "courseCatalog"],
        min_length=1,
        max_length=3,
    )
    limit: int = Field(default=4, ge=1, le=10)

    @field_validator("query")
    @classmethod
    def normalize_query(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if len(normalized) < 2:
            raise ValueError("query is too short")
        return normalized

    @field_validator("domains")
    @classmethod
    def deduplicate_domains(cls, value: list[RetrievalDomain]) -> list[RetrievalDomain]:
        return list(dict.fromkeys(value))


class RetrievalItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    kind: RetrievalKind
    title: str = Field(min_length=1, max_length=300)
    summary: str = Field(default="", max_length=1200)
    score: float | None = Field(default=None, ge=0)
    source_ref: str | None = Field(default=None, alias="sourceRef", max_length=300)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrieveResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    contract_version: Literal[1] = Field(default=1, alias="contractVersion")
    provider: Literal["cyjdata-v2"] = "cyjdata-v2"
    answerable: bool
    items: list[RetrievalItem]
    source_refs: list[str] = Field(default_factory=list, alias="sourceRefs")
    degraded: bool = False
    degraded_reasons: list[str] = Field(default_factory=list, alias="degradedReasons")
    latency_ms: int = Field(default=0, alias="latencyMs", ge=0)
    cached: bool = False
