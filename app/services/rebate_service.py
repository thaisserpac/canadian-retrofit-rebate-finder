import re
from typing import Optional

from sqlalchemy.orm import Session

from app.models.rebate import RebateProgram, RetrofitType, RebateRetrofitType

# ── Province detection ───────────────────────────────────────

PROVINCE_KEYWORDS: dict[str, str] = {
    # Full names
    "ontario": "ON",
    "british columbia": "BC",
    "quebec": "QC",
    "québec": "QC",
    "alberta": "AB",
    "nova scotia": "NS",
    "new brunswick": "NB",
    "prince edward island": "PE",
    "manitoba": "MB",
    "saskatchewan": "SK",
    "newfoundland": "NL",
    "labrador": "NL",
    "northwest territories": "NT",
    "yukon": "YT",
    "nunavut": "NU",
    # Abbreviations
    "on": "ON",
    "bc": "BC",
    "qc": "QC",
    "ab": "AB",
    "ns": "NS",
    "nb": "NB",
    "pe": "PE",
    "pei": "PE",
    "mb": "MB",
    "sk": "SK",
    "nl": "NL",
    "nt": "NT",
    "nwt": "NT",
    "yt": "YT",
    "nu": "NU",
    # Major cities
    "toronto": "ON",
    "ottawa": "ON",
    "mississauga": "ON",
    "hamilton": "ON",
    "kingston": "ON",
    "vancouver": "BC",
    "victoria": "BC",
    "surrey": "BC",
    "montreal": "QC",
    "montréal": "QC",
    "quebec city": "QC",
    "calgary": "AB",
    "edmonton": "AB",
    "halifax": "NS",
    "fredericton": "NB",
    "saint john": "NB",
    "moncton": "NB",
    "charlottetown": "PE",
    "winnipeg": "MB",
    "regina": "SK",
    "saskatoon": "SK",
    "st. john's": "NL",
    "yellowknife": "NT",
    "whitehorse": "YT",
    "iqaluit": "NU",
}

# Two-letter abbreviations that must be matched as whole words to avoid false positives
_ABBREV_CODES = {"on", "bc", "qc", "ab", "ns", "nb", "pe", "pei", "mb", "sk", "nl", "nt", "nwt", "yt", "nu"}


def extract_province(text: str, session_province: Optional[str] = None) -> Optional[str]:
    """Detect a Canadian province from free-text. Falls back to session province."""
    lower = text.lower()

    # Check multi-word names first (longest match wins)
    for phrase in sorted(PROVINCE_KEYWORDS, key=len, reverse=True):
        if phrase in _ABBREV_CODES:
            # Whole-word match for short codes
            if re.search(rf"\b{re.escape(phrase)}\b", lower):
                return PROVINCE_KEYWORDS[phrase]
        else:
            if phrase in lower:
                return PROVINCE_KEYWORDS[phrase]

    return session_province


# ── Retrofit type detection ──────────────────────────────────

RETROFIT_SYNONYMS: dict[str, list[str]] = {
    "heat pump": ["heat_pump_air_source", "heat_pump_ground_source", "heat_pump_mini_split"],
    "air source heat pump": ["heat_pump_air_source"],
    "air-source heat pump": ["heat_pump_air_source"],
    "ground source heat pump": ["heat_pump_ground_source"],
    "ground-source heat pump": ["heat_pump_ground_source"],
    "geothermal": ["heat_pump_ground_source"],
    "mini split": ["heat_pump_mini_split"],
    "mini-split": ["heat_pump_mini_split"],
    "minisplit": ["heat_pump_mini_split"],
    "ductless": ["heat_pump_mini_split"],
    "insulation": ["insulation_attic", "insulation_wall", "insulation_basement"],
    "attic insulation": ["insulation_attic"],
    "wall insulation": ["insulation_wall"],
    "basement insulation": ["insulation_basement"],
    "window": ["windows_doors"],
    "windows": ["windows_doors"],
    "door": ["windows_doors"],
    "doors": ["windows_doors"],
    "windows and doors": ["windows_doors"],
    "solar": ["solar_panels"],
    "solar panel": ["solar_panels"],
    "solar panels": ["solar_panels"],
    "solar battery": ["solar_battery"],
    "battery storage": ["solar_battery"],
    "water heater": ["heat_pump_water_heater"],
    "hot water": ["heat_pump_water_heater"],
    "heat pump water heater": ["heat_pump_water_heater"],
    "thermostat": ["smart_thermostat"],
    "smart thermostat": ["smart_thermostat"],
    "air sealing": ["air_sealing"],
    "air seal": ["air_sealing"],
    "draft": ["air_sealing"],
    "drafty": ["air_sealing"],
    "weatherstripping": ["air_sealing"],
    "furnace": ["heat_pump_air_source"],
    "oil furnace": ["heat_pump_air_source"],
    "oil heating": ["heat_pump_air_source"],
    "ev charger": ["ev_charger"],
    "electric vehicle charger": ["ev_charger"],
    "ev charging": ["ev_charger"],
    "charging station": ["ev_charger"],
    "hrv": ["heat_recovery_ventilator"],
    "heat recovery ventilator": ["heat_recovery_ventilator"],
    "heat recovery": ["heat_recovery_ventilator"],
    "erv": ["heat_recovery_ventilator"],
    "energy recovery ventilator": ["heat_recovery_ventilator"],
    "ventilator": ["heat_recovery_ventilator"],
}


def extract_retrofit_types(text: str) -> list[str]:
    """Detect retrofit types mentioned in free-text."""
    lower = text.lower()
    found: set[str] = set()

    for phrase in sorted(RETROFIT_SYNONYMS, key=len, reverse=True):
        if phrase in lower:
            found.update(RETROFIT_SYNONYMS[phrase])

    return list(found)


# ── Database queries ─────────────────────────────────────────

def find_matching_rebates(
    db: Session,
    province: Optional[str] = None,
    retrofit_types: Optional[list[str]] = None,
    active_only: bool = True,
    limit: int = 8,
) -> list[RebateProgram]:
    """Find rebate programs matching province and/or retrofit types."""
    query = db.query(RebateProgram)

    if active_only:
        query = query.filter(RebateProgram.is_active == True)  # noqa: E712

    if province:
        # Include both province-specific and federal programs
        query = query.filter(RebateProgram.province.in_([province, "FED"]))

    if retrofit_types:
        # Join through the association table to filter by retrofit type
        query = (
            query.join(RebateRetrofitType, RebateProgram.id == RebateRetrofitType.rebate_id)
            .join(RetrofitType, RebateRetrofitType.retrofit_type_id == RetrofitType.id)
            .filter(RetrofitType.name.in_(retrofit_types))
            .distinct()
        )

    return query.limit(limit).all()


def get_all_rebates(
    db: Session,
    province: Optional[str] = None,
    active_only: bool = True,
) -> list[RebateProgram]:
    """List all rebate programs, optionally filtered."""
    query = db.query(RebateProgram)

    if active_only:
        query = query.filter(RebateProgram.is_active == True)  # noqa: E712

    if province:
        query = query.filter(RebateProgram.province.in_([province, "FED"]))

    return query.order_by(RebateProgram.province, RebateProgram.name).all()


def search_rebates(
    db: Session,
    province: str,
    retrofit_type: Optional[str] = None,
    active_only: bool = True,
) -> list[RebateProgram]:
    """Search rebates by province and optional retrofit type."""
    return find_matching_rebates(
        db,
        province=province,
        retrofit_types=[retrofit_type] if retrofit_type else None,
        active_only=active_only,
        limit=50,
    )


# ── Context formatting for LLM ──────────────────────────────

PROVINCE_NAMES: dict[str, str] = {
    "ON": "Ontario",
    "BC": "British Columbia",
    "QC": "Quebec",
    "AB": "Alberta",
    "NS": "Nova Scotia",
    "NB": "New Brunswick",
    "PE": "Prince Edward Island",
    "MB": "Manitoba",
    "SK": "Saskatchewan",
    "NL": "Newfoundland & Labrador",
    "NT": "Northwest Territories",
    "YT": "Yukon",
    "NU": "Nunavut",
    "FED": "Federal (all provinces)",
}


def format_rebates_for_context(rebates: list[RebateProgram]) -> str:
    """Format rebate programs into structured text for LLM system prompt injection."""
    if not rebates:
        return "No specific rebate programs matched the current query. Ask the user for their province and what type of retrofit they are considering."

    lines = ["=== AVAILABLE REBATE PROGRAMS ===", ""]

    for r in rebates:
        province_name = PROVINCE_NAMES.get(r.province, r.province)
        status = "ACTIVE" if r.is_active else "CLOSED"
        deadline = f" (ends {r.end_date})" if r.end_date else ""

        lines.append(f"--- {r.name} ---")
        lines.append(f"Province: {province_name}")
        lines.append(f"Provider: {r.provider}")
        lines.append(f"Status: {status}{deadline}")
        lines.append(f"Amount: {r.amount_description}")
        lines.append(f"Eligibility: {r.eligibility_summary}")
        lines.append(f"How to apply: {r.how_to_apply}")
        if r.website_url:
            lines.append(f"Website: {r.website_url}")
        if r.is_income_tested:
            lines.append("Note: Income-tested — enhanced benefits for qualifying households")
        lines.append("")

    lines.append("=== END REBATE PROGRAMS ===")
    return "\n".join(lines)
