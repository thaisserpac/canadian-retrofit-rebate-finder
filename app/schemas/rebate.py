from datetime import date
from typing import Optional

from pydantic import BaseModel


class RetrofitTypeSchema(BaseModel):
    model_config = {"from_attributes": True}

    name: str
    display_name: str
    category: str


class RebateSchema(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    province: str
    provider: str
    description: str
    max_amount: Optional[float] = None
    amount_description: str
    eligibility_summary: str
    how_to_apply: str
    website_url: Optional[str] = None
    is_active: bool
    end_date: Optional[date] = None
    is_income_tested: bool
    retrofit_types: list[RetrofitTypeSchema] = []


class RebateListResponse(BaseModel):
    rebates: list[RebateSchema]
    count: int


class ProvinceInfo(BaseModel):
    code: str
    name: str
    program_count: int


class ProvinceListResponse(BaseModel):
    provinces: list[ProvinceInfo]
