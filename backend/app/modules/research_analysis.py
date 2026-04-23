from __future__ import annotations

from typing import Any

from app.modules.preprocessing import extract_publication_records


async def analyze_research(raw_text: str) -> dict[str, Any]:
    """Partial research profile processing based on publication signals in CV text."""
    publications = extract_publication_records(raw_text)

    journal_count = sum(1 for pub in publications if pub.get("pub_type") == "journal")
    conference_count = sum(1 for pub in publications if pub.get("pub_type") == "conference")

    return {
        "publications": publications,
        "summary": {
            "publications_count": len(publications),
            "journal_count": journal_count,
            "conference_count": conference_count,
            "is_partial_processing": True,
        },
    }
