from datetime import datetime, date, timezone

from sqlalchemy import Column, Integer, String, Float, Boolean, Text, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class RebateProgram(Base):
    __tablename__ = "rebate_programs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    province = Column(String(50), nullable=False, index=True)
    provider = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    max_amount = Column(Float, nullable=True)
    amount_description = Column(String(300), nullable=False)
    eligibility_summary = Column(Text, nullable=False)
    how_to_apply = Column(Text, nullable=False)
    website_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    end_date = Column(Date, nullable=True)
    is_income_tested = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=_utcnow)
    updated_at = Column(DateTime, nullable=False, default=_utcnow, onupdate=_utcnow)

    retrofit_types = relationship(
        "RetrofitType",
        secondary="rebate_retrofit_types",
        back_populates="rebate_programs",
    )


class RetrofitType(Base):
    __tablename__ = "retrofit_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)

    rebate_programs = relationship(
        "RebateProgram",
        secondary="rebate_retrofit_types",
        back_populates="retrofit_types",
    )


class RebateRetrofitType(Base):
    __tablename__ = "rebate_retrofit_types"

    rebate_id = Column(Integer, ForeignKey("rebate_programs.id"), primary_key=True)
    retrofit_type_id = Column(Integer, ForeignKey("retrofit_types.id"), primary_key=True)
    specific_amount = Column(String(200), nullable=True)
