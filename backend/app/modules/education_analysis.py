from __future__ import annotations

from typing import Any

from app.modules.preprocessing import extract_education_records
from app.modules.qs_ranking_matcher import get_qs_ranking


async def analyze_education(raw_text: str, candidate_universities: str | None = None) -> dict[str, Any]:
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

    qs_ranking = None
    institution_name = None
    if candidate_universities:
        institution_name, qs_ranking = get_qs_ranking(candidate_universities)

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

    # Attach the found QS ranking info to the last chronological record if records exist
    if records:
        records[-1]['institution_name'] = institution_name or candidate_universities
        records[-1]['qs_ranking'] = qs_ranking

    return {
        "records": records,
        "highest_qualification": levels[-1] if levels else None,
        "degree_path": levels,
        "educational_years": years,
        "education_gaps": gaps,
        "qs_ranking_info": {
            "searched_university": candidate_universities,
            "matched_institution": institution_name,
            "qs_ranking": qs_ranking
        },
        "summary": {
            "records_count": len(records),
            "has_school_stage": any(level in {"SSE / Matric", "HSSC / Intermediate"} for level in levels),
            "has_higher_education": any(level in {"BS / BSc", "MS / MPhil", "PhD"} for level in levels),
            "gap_count": len(gaps),
        },
    }
