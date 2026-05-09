"""
Skill Alignment Module (CS 417 Spec 3.9)

Analyzes whether skills claimed in CV are supported by:
- Job titles and responsibilities
- Research publications and research themes
- Target job description (if provided)

Returns skill evidence scoring and alignment assessment.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from app.modules.preprocessing import extract_skill_records


def _extract_job_responsibilities(experience_records: list[dict[str, Any]]) -> str:
    """Extract job titles and descriptions as searchable text."""
    responsibilities = []
    for record in experience_records:
        if record.get("job_title"):
            responsibilities.append(record["job_title"])
        if record.get("company"):
            responsibilities.append(record["company"])
        if record.get("description"):
            responsibilities.append(record["description"])
    return " ".join(responsibilities).lower()


def _extract_publication_keywords(publications: list[dict[str, Any]]) -> str:
    """Extract publication titles, abstracts, keywords as searchable text."""
    keywords = []
    for pub in publications:
        if pub.get("title"):
            keywords.append(pub["title"])
        if pub.get("abstract"):
            keywords.append(pub["abstract"])
        if pub.get("keywords"):
            keywords.append(" ".join(pub["keywords"]))
    return " ".join(keywords).lower()


def _score_skill_evidence(
    skill: str,
    job_text: str,
    publication_text: str,
    cv_raw_text: str,
) -> tuple[str, float]:
    """
    Score how well a skill is evidenced in CV profile.
    Returns (evidence_level, confidence_score)
    
    Evidence levels: "strongly_evidenced", "partially_evidenced", "weakly_evidenced", "unsupported"
    """
    skill_lower = skill.lower()
    
    # Count occurrences in different sections
    job_mentions = len(re.findall(rf"\b{re.escape(skill_lower)}\b", job_text))
    pub_mentions = len(re.findall(rf"\b{re.escape(skill_lower)}\b", publication_text))
    cv_mentions = len(re.findall(rf"\b{re.escape(skill_lower)}\b", cv_raw_text.lower()))
    
    # Calculate total evidence score
    total_mentions = job_mentions * 2 + pub_mentions * 1.5 + cv_mentions * 0.5  # Weighted
    
    # Determine evidence level
    if total_mentions >= 4:
        return "strongly_evidenced", min(0.95, total_mentions / 10)
    elif total_mentions >= 2:
        return "partially_evidenced", min(0.75, total_mentions / 5)
    elif total_mentions >= 1:
        return "weakly_evidenced", min(0.5, total_mentions / 3)
    else:
        return "unsupported", 0.0


def analyze_skill_alignment(
    raw_text: str,
    experience_records: list[dict[str, Any]] | None = None,
    publications: list[dict[str, Any]] | None = None,
    job_description: str | None = None,
) -> dict[str, Any]:
    """
    Analyze skill alignment with job roles and research output.
    
    Args:
        raw_text: CV raw text
        experience_records: Extracted experience/job history
        publications: Extracted research publications
        job_description: Target job description (optional)
    
    Returns:
        Skill alignment analysis including evidence scoring and recommendations
    """
    experience_records = experience_records or []
    publications = publications or []
    
    # Extract skills from CV
    skill_records = extract_skill_records(raw_text)
    claimed_skills = [record["skill_name"] for record in skill_records]
    
    # Build searchable text from different profile sections
    job_text = _extract_job_responsibilities(experience_records)
    pub_text = _extract_publication_keywords(publications)
    
    # Score each skill
    skill_evidence: dict[str, dict[str, Any]] = {}
    for record in skill_records:
        skill = record["skill_name"]
        evidence_level, confidence = _score_skill_evidence(
            skill,
            job_text,
            pub_text,
            raw_text,
        )
        skill_evidence[skill] = {
            "skill_category": record.get("skill_category"),
            "evidence_level": evidence_level,
            "confidence_score": round(confidence, 2),
            "mentions": {
                "in_jobs": len(re.findall(rf"\b{re.escape(skill.lower())}\b", job_text)),
                "in_publications": len(re.findall(rf"\b{re.escape(skill.lower())}\b", pub_text)),
            },
            "supported_by_experience": record.get("supported_by_experience", False),
            "supported_by_publications": record.get("supported_by_publications", False),
        }
    
    # Categorize skills
    categorized = {
        "strongly_evidenced": [],
        "partially_evidenced": [],
        "weakly_evidenced": [],
        "unsupported": [],
    }
    for skill, evidence in skill_evidence.items():
        level = evidence["evidence_level"]
        categorized[level].append(skill)
    
    # Assess job alignment if job description provided
    job_alignment = None
    if job_description:
        job_skill_records = extract_skill_records(job_description)
        job_skills = set(s.lower() for s in [r["skill_name"] for r in job_skill_records])
        claimed_skills_set = set(s.lower() for s in claimed_skills)
        matched_skills = claimed_skills_set & job_skills
        job_alignment = {
            "required_skills": list(job_skills),
            "matched_skills": list(matched_skills),
            "match_percentage": round(len(matched_skills) / max(len(job_skills), 1) * 100, 1),
            "coverage_assessment": "strong" if len(matched_skills) >= len(job_skills) * 0.8
            else "moderate" if len(matched_skills) >= len(job_skills) * 0.5
            else "weak",
        }
    
    # Calculate overall skill consistency score
    total_skills = len(claimed_skills)
    strongly_evidenced_count = len(categorized["strongly_evidenced"])
    partially_evidenced_count = len(categorized["partially_evidenced"])
    
    consistency_score = round(
        (strongly_evidenced_count * 1.0 + partially_evidenced_count * 0.6) / max(total_skills, 1) * 100,
        1,
    )
    
    return {
        "total_claimed_skills": total_skills,
        "skill_evidence": skill_evidence,
        "categorized_skills": categorized,
        "consistency_score": consistency_score,
        "skill_consistency_assessment": "excellent"
        if consistency_score >= 80
        else "good"
        if consistency_score >= 60
        else "moderate"
        if consistency_score >= 40
        else "poor",
        "job_alignment": job_alignment,
        "top_evidenced_skills": categorized["strongly_evidenced"][:5],
        "skills_needing_verification": categorized["unsupported"],
        "recommendations": _generate_skill_recommendations(categorized, consistency_score),
    }


def _generate_skill_recommendations(categorized: dict[str, list[str]], score: float) -> list[str]:
    """Generate recommendations based on skill evidence analysis."""
    recommendations = []
    
    if len(categorized["unsupported"]) > 3:
        recommendations.append(
            f"Consider removing or evidencing {len(categorized['unsupported'])} unsupported skills with concrete examples."
        )
    
    if score < 60:
        recommendations.append(
            "Skills claim low evidence in job history or publications. "
            "Consider adding specific projects or publications that demonstrate these skills."
        )
    
    if len(categorized["strongly_evidenced"]) >= 5:
        recommendations.append(
            "Excellent skill documentation. Consider highlighting top 5 skills in a dedicated skills summary."
        )
    
    if not recommendations:
        recommendations.append("Skill profile is well-evidenced. Continue showcasing skills through publications and work experience.")
    
    return recommendations
