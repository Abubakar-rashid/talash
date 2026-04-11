# =============================================================================
# TALASH - CV Parser and Database Storage
# app/api/cv_upload.py
# =============================================================================

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import fitz
import os
import shutil
from datetime import datetime

from app.db.database import get_db
from app.db.models import Candidate, ProcessingStatus
from app.llm.llm_client import ask_llm

router = APIRouter(prefix="/cv", tags=["CV Upload"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")


def _candidate_analysis_prompts(raw_text: str) -> tuple[str, str]:
    system_prompt = """
You are an expert CV parser for hiring systems.
Return ONLY valid JSON (no markdown, no prose).
If a value is missing, use null.
carefully analyze the CV and dont put value of one field in another field
Read the text multiple time if needed to find the correct answer.
i have added the comments using # to guide you about the fields,dont include them in response, please follow them
Use exactly this JSON schema:
{
  "full_name": string|null, # Use the full name as it appears on the CV
  "email": string|null,  # email of the candidate
  "phone": string|null,  # phone number of the candidate can start with country code or not like +1 or 001 or just 1234567890
  "address": string|null,  # currently living address of the candidate if available
  "linkedin_url": string|null,  # linkedin profile of the candidate, must have linkedin in the url dont mix it wiht github link or any other link
  "nationality": string|null,
  "overall_summary": string|null,
  "overall_score": number|null
}

Rules:
- Keep overall_summary concise (max 120 words).
- overall_score must be 0 to 100 when present.
- Do not invent facts not supported by the CV.
"""

    user_prompt = f"""
Extract candidate profile fields from this CV raw text.

CV RAW TEXT:
{raw_text[:15000]}
"""

    return system_prompt, user_prompt


# HELPER — Extract raw text from PDF using PyMuPDF
def extract_text_from_pdf(filepath: str) -> str:
    """
    Opens a PDF file and extracts all text page by page.
    Returns a single clean string of the full CV text.
    """
    try:
        doc = fitz.open(filepath)
        full_text = ""

        for page_num in range(len(doc)):
            page = doc[page_num]
            full_text += page.get_text()
            full_text += "\n"  # Separator between pages

        doc.close()

        # Basic cleanup
        full_text = full_text.strip()
        full_text = "\n".join(
            line.strip() for line in full_text.splitlines() if line.strip()
        )

        return full_text

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract text from PDF: {str(e)}"
        )


# HELPER — Save candidate to database
async def save_candidate_to_db(
    db: AsyncSession,
    filename: str,
    filepath: str,
    raw_text: str
) -> Candidate:
    """
    Creates a new candidate record in the database with the extracted CV text.
    Status is set to 'pending' — LLM analysis runs separately after this.
    """
    candidate = Candidate(
        cv_filename=filename,
        cv_filepath=filepath,
        cv_raw_text=raw_text,
        status=ProcessingStatus.PENDING
    )

    db.add(candidate)
    await db.commit()
    await db.refresh(candidate)

    return candidate


@router.post("/upload")
async def upload_and_parse_cv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Receives a CV PDF from frontend, saves it to uploads/, extracts text,
    and inserts it into the database as a new candidate.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported."
        )

    # Ensure upload directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Save the file
    filepath = os.path.join(UPLOAD_DIR, file.filename)
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Extract raw text from PDF
    print(f"Parsing CV: {file.filename}")
    raw_text = extract_text_from_pdf(filepath)

    if not raw_text or len(raw_text) < 50:
        raise HTTPException(
            status_code=422,
            detail="Could not extract meaningful text from this PDF. It may be scanned or image-based."
        )

    print(f"Extracted {len(raw_text)} characters from {file.filename}")

    # Save to database
    candidate = await save_candidate_to_db(
        db=db,
        filename=file.filename,
        filepath=filepath,
        raw_text=raw_text
    )

    print(f"Saved candidate ID {candidate.id} to database")

    try:
        os.remove(filepath)
        print(f"Deleted parsed CV from uploads: {filepath}")
    except Exception as e:
        print(f"Failed to delete file {filepath}: {e}")

    return {
        "success": True,
        "candidate_id": candidate.id,
        "filename": file.filename,
        "characters_extracted": len(raw_text),
        "status": candidate.status,
        "message": f"CV uploaded and parsed successfully. Candidate ID: {candidate.id}"
    }

# ENDPOINT — POST /cv/parse
# Called after frontend saves the PDF to uploads/ folder
# Frontend sends just the filename, backend does the rest
@router.post("/parse")
async def parse_cv(
    filename: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Parses a CV PDF that already exists in the uploads/ folder.
    Extracts raw text and saves the candidate record to the database.

    Steps:
    1. Check the file exists in uploads/
    2. Extract text using PyMuPDF
    3. Save candidate record to DB with raw text
    4. Return candidate ID for frontend to track

    Frontend calls this AFTER saving the PDF to uploads/.
    """

    # Step 1 — Build full file path and check it exists
    filepath = os.path.join(UPLOAD_DIR, filename)

    if not os.path.exists(filepath):
        raise HTTPException(
            status_code=404,
            detail=f"File '{filename}' not found in uploads folder. Make sure it was uploaded first."
        )

    # Check it's actually a PDF
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported."
        )

    # Step 2 — Extract raw text from PDF
    print(f"Parsing CV: {filename}")
    raw_text = extract_text_from_pdf(filepath)

    if not raw_text or len(raw_text) < 50:
        raise HTTPException(
            status_code=422,
            detail="Could not extract meaningful text from this PDF. It may be scanned or image-based."
        )

    print(f"Extracted {len(raw_text)} characters from {filename}")

    # Step 3 — Save to database
    candidate = await save_candidate_to_db(
        db=db,
        filename=filename,
        filepath=filepath,
        raw_text=raw_text
    )

    print(f"Saved candidate ID {candidate.id} to database")

    # Step 3.5 — Delete the PDF file after successful processing
    try:
        os.remove(filepath)
        print(f"Deleted parsed CV from uploads: {filepath}")
    except Exception as e:
        print(f"Failed to delete file {filepath}: {e}")

    # Step 4 — Return response to frontend
    return {
        "success": True,
        "candidate_id": candidate.id,
        "filename": filename,
        "characters_extracted": len(raw_text),
        "status": candidate.status,
        "message": f"CV parsed successfully. Candidate ID: {candidate.id}"
    }


# ENDPOINT — GET /cv/candidates
# Returns all candidates in the database (for dashboard)
@router.get("/candidates")
async def get_all_candidates(db: AsyncSession = Depends(get_db)):
    """
    Returns a list of all candidates with their basic info and status.
    Used by the frontend dashboard to show uploaded CVs.
    """
    result = await db.execute(
        select(Candidate).order_by(Candidate.uploaded_at.desc())
    )
    candidates = result.scalars().all()

    return {
        "total": len(candidates),
        "candidates": [
            {
                "id": c.id,
                "full_name": c.full_name or "Not yet extracted",
                "filename": c.cv_filename,
                "status": c.status,
                "uploaded_at": c.uploaded_at,
            }
            for c in candidates
        ]
    }


# ENDPOINT — GET /cv/candidate/{id}
# Returns full candidate record including raw text
@router.get("/candidate/{candidate_id}")
async def get_candidate(
    candidate_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Returns full details of a single candidate by ID.
    """
    result = await db.execute(
        select(Candidate).where(Candidate.id == candidate_id)
    )
    candidate = result.scalar_one_or_none()

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail=f"Candidate with ID {candidate_id} not found."
        )

    return {
        "id": candidate.id,
        "full_name": candidate.full_name,
        "email": candidate.email,
        "phone": candidate.phone,
        "address": candidate.address,
        "linkedin_url": candidate.linkedin_url,
        "nationality": candidate.nationality,
        "filename": candidate.cv_filename,
        "status": candidate.status,
        "overall_summary": candidate.overall_summary,
        "overall_score": candidate.overall_score,
        "raw_text": candidate.cv_raw_text,
        "raw_text_preview": candidate.cv_raw_text[:500] if candidate.cv_raw_text else None,
        "uploaded_at": candidate.uploaded_at,
        "processed_at": candidate.processed_at,
    }


@router.post("/candidate/{candidate_id}/analyze")
async def analyze_candidate(
    candidate_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Sends stored raw CV text to Groq, parses JSON, and persists extracted fields
    for the selected candidate entry.
    """
    result = await db.execute(
        select(Candidate).where(Candidate.id == candidate_id)
    )
    candidate = result.scalar_one_or_none()

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail=f"Candidate with ID {candidate_id} not found."
        )

    if not candidate.cv_raw_text or len(candidate.cv_raw_text.strip()) < 50:
        raise HTTPException(
            status_code=422,
            detail="Candidate has no usable raw CV text to analyze."
        )

    candidate.status = ProcessingStatus.PROCESSING
    await db.commit()

    try:
        system_prompt, user_prompt = _candidate_analysis_prompts(candidate.cv_raw_text)
        parsed = await ask_llm(system_prompt=system_prompt, user_prompt=user_prompt, temperature=0.1)

        candidate.full_name = parsed.get("full_name")
        candidate.email = parsed.get("email")
        candidate.phone = parsed.get("phone")
        candidate.address = parsed.get("address")
        candidate.linkedin_url = parsed.get("linkedin_url")
        candidate.nationality = parsed.get("nationality")
        candidate.overall_summary = parsed.get("overall_summary")

        score = parsed.get("overall_score")
        if isinstance(score, (int, float)):
            candidate.overall_score = max(0.0, min(100.0, float(score)))

        candidate.status = ProcessingStatus.COMPLETED
        candidate.processed_at = datetime.utcnow()

        await db.commit()
        await db.refresh(candidate)

        return {
            "success": True,
            "message": "Candidate analyzed and saved successfully.",
            "candidate_id": candidate.id,
            "status": candidate.status,
            "analysis": parsed,
        }

    except Exception as e:
        candidate.status = ProcessingStatus.FAILED
        await db.commit()
        raise HTTPException(
            status_code=500,
            detail=f"LLM analysis failed: {str(e)}"
        )