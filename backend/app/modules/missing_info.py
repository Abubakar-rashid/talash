from __future__ import annotations

from typing import Any


def detect_missing_fields(
    candidate_snapshot: dict[str, Any],
    education: dict[str, Any],
    experience: dict[str, Any],
    research: dict[str, Any],
) -> list[str]:
    missing: list[str] = []

    if not candidate_snapshot.get("full_name"):
        missing.append("full name")
    if not candidate_snapshot.get("email"):
        missing.append("email address")
    if not candidate_snapshot.get("phone"):
        missing.append("phone number")
    if not candidate_snapshot.get("nationality"):
        missing.append("nationality")

    education_records = education.get("records") or []
    if not education_records:
        missing.append("education history")

    experience_records = experience.get("records") or []
    if not experience_records:
        missing.append("professional experience details")

    publications = research.get("publications") or []
    if not publications:
        missing.append("publication/research details")

    overlap_issues = (experience.get("timeline_checks") or {}).get("job_overlaps") or []
    if overlap_issues:
        missing.append("clarification for overlapping jobs")

    unexplained_gaps = [
        gap
        for gap in ((experience.get("timeline_checks") or {}).get("professional_gaps") or [])
        if gap.get("is_justified") is False
    ]
    if unexplained_gaps:
        missing.append("explanation for professional gaps")

    return sorted(set(missing))


async def draft_missing_info_email(full_name: str | None, missing_fields: list[str]) -> str:
    candidate_name = full_name or "Candidate"
    if not missing_fields:
        return (
            f"Subject: TALASH Profile Update Confirmation\n\n"
            f"Dear {candidate_name},\n\n"
            "Thank you for submitting your profile. At this stage, no additional information "
            "is required from your side.\n\n"
            "Best regards,\n"
            "TALASH Recruitment Team"
        )

    bullet_list = "\n".join(f"- {item}" for item in missing_fields)
    return (
        "Subject: Request for Missing Information - TALASH Profile Review\n\n"
        f"Dear {candidate_name},\n\n"
        "Thank you for sharing your CV. To complete your profile evaluation, "
        "please provide the following missing details:\n\n"
        f"{bullet_list}\n\n"
        "You may reply with the details directly or share an updated CV.\n\n"
        "Best regards,\n"
        "TALASH Recruitment Team"
    )
