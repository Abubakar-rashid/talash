from __future__ import annotations

from typing import Any

from app.modules.preprocessing import extract_education_records


async def analyze_education(raw_text: str) -> dict[str, Any]:
    """Build a structured educational profile summary from CV text."""
    records = extract_education_records(raw_text)

    levels = [record.get("degree_level") for record in records if record.get("degree_level")]
    years = sorted(
        {
            year
            for record in records
            for year in (record.get("year_start"), record.get("year_end"))
            if isinstance(year, int)
        }
    )

    gaps: list[dict[str, Any]] = []
    for idx in range(1, len(years)):
        gap_years = years[idx] - years[idx - 1]
        if gap_years >= 3:
            gaps.append(
                {
                    "gap_between": f"{years[idx - 1]}-{years[idx]}",
                    "gap_years": gap_years,
                }
            )

    return {
        "records": records,
        "highest_qualification": levels[-1] if levels else None,
        "degree_path": levels,
        "educational_years": years,
        "education_gaps": gaps,
        "summary": {
            "records_count": len(records),
            "has_school_stage": any(level in {"SSE / Matric", "HSSC / Intermediate"} for level in levels),
            "has_higher_education": any(level in {"BS / BSc", "MS / MPhil", "PhD"} for level in levels),
            "gap_count": len(gaps),
        },
    }
