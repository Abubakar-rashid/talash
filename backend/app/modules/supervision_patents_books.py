"""
Supervision, Patents, and Books Analysis (CS 417 Spec 3.3, 3.4, 3.5)

Analyzes:
- MS/PhD students supervised (main and co-supervisor)
- Books authored or co-authored
- Patents filed or co-invented
- ISBN/Patent verification metadata

Returns structured data for research profile assessment.
"""

from __future__ import annotations

import re
from typing import Any

from app.llm.llm_client import ask_llm


async def extract_supervision_info(raw_text: str) -> dict[str, Any]:
    """
    Extract information about supervised MS/PhD students.
    
    Returns:
        - Main supervised students (MS/PhD)
        - Co-supervised students
        - Years of supervision
        - Student outcomes (publications, dissertations)
    """
    if not raw_text or len(raw_text.strip()) < 100:
        return {
            "ms_students_supervised": 0,
            "phd_students_supervised": 0,
            "co_supervised_students": 0,
            "total_students": 0,
            "students_list": [],
            "publications_with_students": 0,
            "supervision_note": "No supervision information found in CV.",
        }
    
    system_prompt = """You are an expert at extracting academic supervision information from CVs.
Extract the following from the CV text:
1. Number of MS/PhD students supervised (as main supervisor)
2. Number of students co-supervised
3. Names and graduation years of supervised students (if available)
4. Any joint publications with supervised students

Return a JSON object with:
{
    "ms_students_main": <number>,
    "phd_students_main": <number>,
    "co_supervised_count": <number>,
    "students": [
        {
            "name": "Student Name",
            "level": "MS" or "PhD",
            "graduation_year": YYYY,
            "role": "main" or "co",
            "joint_publications": <count>
        }
    ],
    "total_joint_publications": <number>,
    "supervision_strength": "strong" | "moderate" | "limited" | "none"
}

If no supervision information is found, return zeros."""

    user_prompt = f"Extract supervision information from this CV:\n\n{raw_text[:3000]}"
    
    try:
        result = await ask_llm(system_prompt, user_prompt, provider="groq", max_tokens=1000)
        supervision_data = result if isinstance(result, dict) else {"total_students": 0, "supervision_strength": "none"}
    except Exception:
        supervision_data = {"total_students": 0, "supervision_strength": "none"}
    
    ms_main = supervision_data.get("ms_students_main", 0)
    phd_main = supervision_data.get("phd_students_main", 0)
    co_supervised = supervision_data.get("co_supervised_count", 0)
    
    return {
        "ms_students_supervised": ms_main,
        "phd_students_supervised": phd_main,
        "co_supervised_students": co_supervised,
        "total_students": ms_main + phd_main + co_supervised,
        "students_list": supervision_data.get("students", []),
        "publications_with_students": supervision_data.get("total_joint_publications", 0),
        "supervision_strength": supervision_data.get("supervision_strength", "none"),
        "supervision_assessment": (
            "Strong academic mentorship with multiple supervised dissertations."
            if supervision_data.get("supervision_strength") == "strong"
            else "Active supervision of graduate students."
            if supervision_data.get("supervision_strength") == "moderate"
            else "Limited supervision experience documented."
            if supervision_data.get("supervision_strength") == "limited"
            else "No supervision experience documented in CV."
        ),
    }


async def extract_books_info(raw_text: str) -> dict[str, Any]:
    """
    Extract information about authored or co-authored books.
    
    Returns:
        - Book titles and metadata
        - Publishers
        - ISBN/DOI
        - Authorship role (sole, lead, co-author)
    """
    if not raw_text or len(raw_text.strip()) < 100:
        return {
            "books_authored": 0,
            "sole_authored": 0,
            "lead_authored": 0,
            "co_authored": 0,
            "books": [],
            "books_note": "No books documented in CV.",
        }
    
    system_prompt = """You are an expert at extracting book publication information from CVs.
Extract information about books authored or co-authored.
For each book, identify:
1. Book title
2. Authors (list all)
3. Publisher name
4. Publication year
5. ISBN (if available)
6. Authorship role (sole author, lead author, or co-author)

Return a JSON object with:
{
    "books": [
        {
            "title": "Book Title",
            "authors": ["Author1", "Author2"],
            "publisher": "Publisher Name",
            "year": YYYY,
            "isbn": "ISBN-13 or not provided",
            "authorship_role": "sole" | "lead" | "co-author",
            "importance": "primary" | "contributing"
        }
    ],
    "total_books": <number>,
    "scholarly_value": "high" | "moderate" | "low"
}

If no books found, return empty list."""

    user_prompt = f"Extract book publication information from this CV:\n\n{raw_text[:3000]}"
    
    try:
        result = await ask_llm(system_prompt, user_prompt, provider="groq", max_tokens=1000)
        books_data = result if isinstance(result, dict) else {"books": []}
    except Exception:
        books_data = {"books": []}
    
    books = books_data.get("books", [])
    sole_authored = sum(1 for b in books if b.get("authorship_role") == "sole")
    lead_authored = sum(1 for b in books if b.get("authorship_role") == "lead")
    co_authored = sum(1 for b in books if b.get("authorship_role") == "co-author")
    
    return {
        "books_authored": len(books),
        "sole_authored": sole_authored,
        "lead_authored": lead_authored,
        "co_authored": co_authored,
        "books": books,
        "scholarly_value": books_data.get("scholarly_value", "low"),
        "books_assessment": (
            f"Authored {len(books)} book(s) demonstrating substantial academic contribution."
            if len(books) > 0
            else "No books documented in CV."
        ),
    }


async def extract_patents_info(raw_text: str) -> dict[str, Any]:
    """
    Extract information about patents filed or granted.
    
    Returns:
        - Patent numbers and titles
        - Filing and grant dates
        - Inventors list
        - Patent status (filed, granted, pending)
    """
    if not raw_text or len(raw_text.strip()) < 100:
        return {
            "patents_filed": 0,
            "patents_granted": 0,
            "patents_pending": 0,
            "patents": [],
            "patents_note": "No patents documented in CV.",
        }
    
    system_prompt = """You are an expert at extracting patent information from CVs.
Extract information about patents filed, granted, or pending.
For each patent, identify:
1. Patent number (if available)
2. Patent title
3. Filing date and/or grant date
4. Inventors (list all)
5. Country of filing
6. Patent status (filed, granted, pending)

Return a JSON object with:
{
    "patents": [
        {
            "title": "Patent Title",
            "number": "US Patent Number or not provided",
            "filing_year": YYYY,
            "grant_year": YYYY or null,
            "inventors": ["Inventor1", "Inventor2"],
            "country": "US or other country code",
            "status": "filed" | "granted" | "pending",
            "contribution_role": "lead_inventor" | "co_inventor"
        }
    ],
    "total_patents": <number>,
    "patent_innovation_score": <0-100>
}

If no patents found, return empty list."""

    user_prompt = f"Extract patent information from this CV:\n\n{raw_text[:3000]}"
    
    try:
        result = await ask_llm(system_prompt, user_prompt, provider="groq", max_tokens=1000)
        patents_data = result if isinstance(result, dict) else {"patents": []}
    except Exception:
        patents_data = {"patents": []}
    
    patents = patents_data.get("patents", [])
    granted = sum(1 for p in patents if p.get("status") == "granted")
    pending = sum(1 for p in patents if p.get("status") == "pending")
    filed = len(patents) - granted - pending
    
    return {
        "patents_filed": filed,
        "patents_granted": granted,
        "patents_pending": pending,
        "patents": patents,
        "innovation_score": patents_data.get("patent_innovation_score", 0),
        "patents_assessment": (
            f"Has {granted} granted patent(s) and {pending} pending patent(s), demonstrating innovation contribution."
            if (granted + pending) > 0
            else "No patents documented in CV."
        ),
    }


async def analyze_innovation_profile(
    supervision: dict[str, Any],
    books: dict[str, Any],
    patents: dict[str, Any],
) -> dict[str, Any]:
    """
    Generate overall innovation and leadership profile assessment.
    """
    supervision_score = min(100, supervision.get("total_students", 0) * 10 + supervision.get("publications_with_students", 0) * 5)
    books_score = min(100, books.get("books_authored", 0) * 20)
    patents_score = min(100, (patents.get("patents_granted", 0) * 25 + patents.get("patents_pending", 0) * 15))
    
    overall_innovation_score = (supervision_score + books_score + patents_score) / 3
    
    return {
        "supervision_score": supervision_score,
        "books_score": books_score,
        "patents_score": patents_score,
        "overall_innovation_score": round(overall_innovation_score, 1),
        "leadership_assessment": (
            "Strong research leadership with active supervision, publications, and innovation output."
            if overall_innovation_score >= 60
            else "Moderate research contribution including some academic leadership."
            if overall_innovation_score >= 30
            else "Limited documentation of academic leadership or innovation."
        ),
    }
