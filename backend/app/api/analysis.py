# =============================================================================
# TALASH - Full Candidate Analysis API
# app/api/analysis.py
# =============================================================================

import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import Candidate, ProcessingStatus
from app.modules.education_analysis import analyze_education
from app.modules.experience_analysis import analyze_experience
from app.modules.missing_info import detect_missing_fields, draft_missing_info_email
from app.modules.research_analysis import analyze_research
from app.llm.llm_client import ask_llm

router = APIRouter(prefix="/analysis", tags=["Analysis"])


# =============================================================================
# LLM ROUTING - Multi-Provider Analysis
# =============================================================================
# Option A: Task-Based Specialization
# - Groq: education, experience, missing_info (heuristic-based)
# - Gemini: research enrichment, advanced analysis
# =============================================================================

async def enrich_research_with_gemini(raw_text: str, base_research: dict) -> dict:
    """
    Enrich research analysis with Gemini for better understanding of:
    - Publication quality and impact
    - Research domain expertise
    - Citation patterns and influence
    - Interdisciplinary research
    """
    if not raw_text or not base_research.get("publications"):
        return base_research
    
    try:
        system_prompt = """
You are an expert research analyst. Analyze the CV text and provide deeper insights into the candidate's research profile.
Return ONLY valid JSON (no markdown, no prose).
{
  "research_quality_assessment": "string|null",
  "domain_expertise_score": number|null (0-100),
  "citation_influence": "string|null",
  "interdisciplinary_focus": [string],
  "publication_strategy": "string|null",
  "research_maturity": "string|null",
  "collaboration_strength": "string|null"
}
"""
        user_prompt = f"""
Based on this CV, assess the candidate's research profile:

{raw_text[:3000]}

Existing research data:
{json.dumps(base_research, indent=2)[:1000]}

Provide deeper insights on research quality, impact, and expertise level.
"""
        
        enrichment = await ask_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,
            max_tokens=400,
            provider="gemini"
        )
        
        # Merge enrichment into base research
        if enrichment:
            base_research["gemini_enrichment"] = enrichment
        return base_research
        
    except Exception as e:
        # Silently fail on enrichment - don't block main analysis
        print(f"Warning: Gemini enrichment failed: {e}")
        return base_research


def _load_json_col(value: str | None) -> dict | list | None:
    if not value:
        return None
    try:
        return json.loads(value)
    except Exception:
        return None


def _dump_json(obj: dict | list | None) -> str | None:
    if obj is None:
        return None
    try:
        return json.dumps(obj, ensure_ascii=False)
    except Exception:
        return None


@router.post("/candidate/{candidate_id}/full")
async def run_full_analysis(
    candidate_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = result.scalar_one_or_none()

    if not candidate:
        raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found.")

    raw = candidate.cv_raw_text or ""
    if len(raw.strip()) < 50:
        raise HTTPException(status_code=422, detail="Not enough CV text to analyze.")

    candidate.status = ProcessingStatus.PROCESSING
    await db.commit()

    try:
        education = await analyze_education(raw, candidate_universities=candidate.universities)
        experience = await analyze_experience(raw)
        research = await analyze_research(raw)
        
        # Enrich research analysis with Gemini for deeper insights
        research = await enrich_research_with_gemini(raw, research)

        candidate_snapshot = {
            "full_name": candidate.full_name,
            "email": candidate.email,
            "phone": candidate.phone,
            "nationality": candidate.nationality,
        }
        missing_fields = detect_missing_fields(candidate_snapshot, education, experience, research)
        draft_email = await draft_missing_info_email(candidate.full_name, missing_fields)

        await db.execute(
            text(
                """
                UPDATE candidates
                SET education_json    = :edu,
                    experience_json   = :exp,
                    research_json     = :res,
                    missing_info_json = :miss,
                    missing_info_email = :email,
                    status            = CAST(:status AS processing_status),
                    processed_at      = :now
                WHERE id = :cid
                """
            ),
            {
                "edu": _dump_json(education),
                "exp": _dump_json(experience),
                "res": _dump_json(research),
                "miss": _dump_json(missing_fields),
                "email": draft_email,
                "status": ProcessingStatus.COMPLETED.value,
                "now": datetime.utcnow(),
                "cid": candidate_id,
            },
        )
        await db.commit()

        return {
            "success": True,
            "candidate_id": candidate_id,
            "education": education,
            "experience": experience,
            "research": research,
            "missing_fields": missing_fields,
            "draft_email": draft_email,
        }

    except Exception as exc:
        await db.rollback()
        try:
            result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
            fresh_candidate = result.scalar_one_or_none()
            if fresh_candidate:
                fresh_candidate.status = ProcessingStatus.FAILED
                fresh_candidate.processed_at = datetime.utcnow()
                await db.commit()
        except Exception:
            await db.rollback()

        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(exc)}")


@router.get("/candidate/{candidate_id}")
async def get_analysis(
    candidate_id: int,
    db: AsyncSession = Depends(get_db),
):
    row = await db.execute(
        text(
            """
            SELECT id, full_name, education_json, experience_json,
                   research_json, missing_info_json, missing_info_email, status
            FROM candidates
            WHERE id = :cid
            """
        ),
        {"cid": candidate_id},
    )
    record = row.mappings().first()

    if not record:
        raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found.")

    edu = _load_json_col(record["education_json"])
    exp = _load_json_col(record["experience_json"])
    res = _load_json_col(record["research_json"])
    miss = _load_json_col(record["missing_info_json"])

    return {
        "candidate_id": candidate_id,
        "full_name": record["full_name"],
        "status": record["status"],
        "education": edu,
        "experience": exp,
        "research": res,
        "missing_fields": miss or [],
        "draft_email": record["missing_info_email"] or "",
        "is_analysed": edu is not None or exp is not None,
    }


@router.post("/candidate/{candidate_id}/email")
async def redraft_email(
    candidate_id: int,
    db: AsyncSession = Depends(get_db),
):
    row = await db.execute(
        text("SELECT full_name, missing_info_json FROM candidates WHERE id = :cid"),
        {"cid": candidate_id},
    )
    record = row.mappings().first()
    if not record:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    missing_fields = _load_json_col(record["missing_info_json"]) or []
    draft = await draft_missing_info_email(record["full_name"], missing_fields)

    await db.execute(
        text("UPDATE candidates SET missing_info_email = :email WHERE id = :cid"),
        {"email": draft, "cid": candidate_id},
    )
    await db.commit()

    return {"success": True, "draft_email": draft}
