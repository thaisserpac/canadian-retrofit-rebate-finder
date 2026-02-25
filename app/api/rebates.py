from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.rebate import RebateProgram, RetrofitType
from app.schemas.rebate import (
    RebateSchema,
    RebateListResponse,
    RetrofitTypeSchema,
    ProvinceInfo,
    ProvinceListResponse,
)
from app.services.rebate_service import get_all_rebates, search_rebates, PROVINCE_NAMES

router = APIRouter(prefix="/api/rebates", tags=["rebates"])


def _rebate_to_schema(r: RebateProgram) -> RebateSchema:
    return RebateSchema(
        id=r.id,
        name=r.name,
        province=r.province,
        provider=r.provider,
        description=r.description,
        max_amount=r.max_amount,
        amount_description=r.amount_description,
        eligibility_summary=r.eligibility_summary,
        how_to_apply=r.how_to_apply,
        website_url=r.website_url,
        is_active=r.is_active,
        end_date=r.end_date,
        is_income_tested=r.is_income_tested,
        retrofit_types=[
            RetrofitTypeSchema(name=rt.name, display_name=rt.display_name, category=rt.category)
            for rt in r.retrofit_types
        ],
    )


@router.get("", response_model=RebateListResponse)
def list_rebates(
    province: Optional[str] = Query(None, description="Province code (ON, BC, QC, etc.)"),
    active_only: bool = Query(True, description="Only return active programs"),
    db: Session = Depends(get_db),
):
    rebates = get_all_rebates(db, province=province, active_only=active_only)
    return RebateListResponse(
        rebates=[_rebate_to_schema(r) for r in rebates],
        count=len(rebates),
    )


@router.get("/search", response_model=RebateListResponse)
def search(
    province: str = Query(..., description="Province code (required)"),
    retrofit_type: Optional[str] = Query(None, description="Retrofit type name"),
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
):
    rebates = search_rebates(db, province=province, retrofit_type=retrofit_type, active_only=active_only)
    return RebateListResponse(
        rebates=[_rebate_to_schema(r) for r in rebates],
        count=len(rebates),
    )


@router.get("/retrofit-types")
def list_retrofit_types(db: Session = Depends(get_db)):
    """List all available retrofit types grouped by category."""
    types = db.query(RetrofitType).order_by(RetrofitType.category, RetrofitType.display_name).all()
    return {
        "types": [
            {"name": t.name, "display_name": t.display_name, "category": t.category}
            for t in types
        ]
    }


@router.get("/provinces", response_model=ProvinceListResponse)
def list_provinces(db: Session = Depends(get_db)):
    rows = (
        db.query(RebateProgram.province, func.count(RebateProgram.id))
        .filter(RebateProgram.is_active == True)  # noqa: E712
        .group_by(RebateProgram.province)
        .order_by(RebateProgram.province)
        .all()
    )
    provinces = [
        ProvinceInfo(
            code=code,
            name=PROVINCE_NAMES.get(code, code),
            program_count=count,
        )
        for code, count in rows
    ]
    return ProvinceListResponse(provinces=provinces)
