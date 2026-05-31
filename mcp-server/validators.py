"""Pydantic input schemas for every MCP tool. Lab 8 requirement."""
from pydantic import BaseModel, Field, field_validator


class GetMaterialPriceInput(BaseModel):
    material: str = Field(..., min_length=2, max_length=100, description="Material name to look up")
    unit: str = Field(default="", max_length=20, description="Optional: unit filter")
    token: str | None = Field(default=None, description="Bearer token")

    @field_validator("material")
    @classmethod
    def material_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Material name cannot be blank")
        return v.strip()


class GetLaborCostInput(BaseModel):
    trade: str = Field(..., min_length=2, max_length=100, description="Trade or profession")
    hours: float = Field(default=8.0, ge=0.1, le=10000, description="Number of hours")
    token: str | None = Field(default=None, description="Bearer token")


class ListPricesInput(BaseModel):
    category: str = Field(default="", max_length=50, description="Category filter (optional)")
    token: str | None = Field(default=None, description="Bearer token")


class SearchKnowledgeInput(BaseModel):
    query: str = Field(..., min_length=3, max_length=500, description="Search query")
    top_k: int = Field(default=3, ge=1, le=10, description="Number of results")
    token: str | None = Field(default=None, description="Bearer token")
