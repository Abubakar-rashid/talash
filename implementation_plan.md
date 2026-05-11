# TALASH ΓÇö Publication Analysis + Bulk PDF (Multi-CV) Upload

## Overview

Two major features to implement:

1. **Publication Analysis** — Use the second Groq API key (from `GROQ_PUBLICATION_API_KEY` env var) exclusively for deep LLM-powered publication analysis that fills `publications`, `journal_details`, `conference_details`, `publication_co_authors`, `coauthor_analysis`, and `topic_variability` tables in the DB.

2. **Bulk PDF Upload (Multi-CV in one file)** ΓÇö Accept a single PDF containing multiple CVs separated by blank pages, split them automatically, and ingest each CV as a separate candidate.

---

## Proposed Changes

### Backend ΓÇö LLM Client

#### [MODIFY] [llm_client.py](file:///d:/talash/backend/app/llm/llm_client.py)

- Add a **second Groq client** (`publication_client`) using `GROQ_PUBLICATION_API_KEY` from `.env`.
- Expose `ask_publication_llm()` and `ask_publication_llm_text()` functions that use this second client.
- This keeps the two API keys completely separate (primary key for CV parsing/general analysis, secondary key for publication analysis).

---

### Backend ΓÇö `.env`

#### [MODIFY] [.env](file:///d:/talash/backend/.env)

- Add `GROQ_PUBLICATION_API_KEY=<your-groq-api-key-here>`
- Add `GROQ_PUBLICATION_MODEL=llama-3.3-70b-versatile` (a more capable model for deep analysis)

---

### Backend ΓÇö Publication Analysis Module

#### [MODIFY] [research_analysis.py](file:///d:/talash/backend/app/modules/research_analysis.py)

Replace the current stub with a full **LLM-powered publication analysis engine** that:

1. **Extracts raw publication list** from CV text using regex/keyword heuristics (as pre-filter).
2. **Sends to LLM** (publication client) asking for structured JSON with all fields needed for the DB tables:
   - `publications` ΓåÆ title, pub_type, authors_raw, year, authorship_role, candidate_author_position, quality_note
   - `journal_details` ΓåÆ journal_name, issn, is_wos_indexed, impact_factor, is_scopus_indexed, quartile, is_predatory
   - `conference_details` ΓåÆ conference_name, core_rank, is_a_star, is_scopus_indexed, is_ieee_xplore, is_springer, is_acm
   - `publication_co_authors` ΓåÆ co_author_name, author_position, is_recurring
   - `coauthor_analysis` ΓåÆ total_unique_coauthors, avg_coauthors_per_paper, recurring_collaborators, most_frequent_collaborator, collaboration_diversity_score, has_international_collaborations, collaboration_summary
   - `topic_variability` ΓåÆ dominant_topic, diversity_score, topic_clusters, topic_trend, variability_summary
3. **Handles large CVs** by chunking publication sections before sending.
4. Returns the rich structured dict.

---

### Backend ΓÇö DB Models

#### [MODIFY] [models.py](file:///d:/talash/backend/app/db/models.py)

- Add `publication_analysis_json` column to `Candidate` to cache the full publication analysis result (like `research_json` already exists for basic research).
- Add `publication_analysis_status` to track whether pub analysis has run.

#### [MODIFY] [database.py](file:///d:/talash/backend/app/db/database.py)

- Add migrations via `init_db()` to create new columns on startup if not present (using `ADD COLUMN IF NOT EXISTS`).

---

### Backend ΓÇö Analysis API

#### [MODIFY] [analysis.py](file:///d:/talash/backend/app/api/analysis.py)

Add two new endpoints:

- `POST /analysis/candidate/{id}/publications` ΓÇö Run deep publication analysis for a single candidate, persist results into DB tables (`publications`, `journal_details`, `conference_details`, `publication_co_authors`, `coauthor_analysis`, `topic_variability`), and store JSON cache in `publication_analysis_json`.
- `GET /analysis/candidate/{id}/publications` ΓÇö Return cached publication analysis from DB.

The POST endpoint will:
1. Fetch candidate's raw CV text.
2. Call the new `analyze_publications_deep()` function.
3. Use raw SQL (`text(...)`) to insert rows into the relevant normalized tables.
4. Store serialized JSON in `candidates.publication_analysis_json`.

---

### Backend ΓÇö Bulk Multi-CV PDF Splitting

#### [MODIFY] [cv_upload.py](file:///d:/talash/backend/app/api/cv_upload.py)

Add a new endpoint `POST /cv/upload/bulk-combined`:

**Algorithm:**
1. Accept a single PDF upload.
2. Use PyMuPDF (`fitz`) to iterate all pages.
3. Detect **blank pages** ΓåÆ a page is blank if `page.get_text().strip()` returns fewer than 20 characters.
4. Split the PDF at blank page boundaries ΓåÆ each segment becomes one CV.
5. Save each segment as a separate temporary PDF file.
6. Call `_ingest_cv_from_file()` for each segment.
7. Return summary of how many CVs were extracted.

**Robustness considerations:**
- Handles 1+ blank pages between CVs (consecutive blanks count as one separator).
- Handles last CV with no trailing blank page.
- Handles cases where blank pages can't be found ΓåÆ treats entire PDF as one CV.
- Minimum page threshold per CV segment (at least 1 non-blank page).

---

### Frontend ΓÇö API Client

#### [MODIFY] [api.js](file:///d:/talash/frontend/src/lib/api.js)

Add:
- `runPublicationAnalysis(candidateId)` ΓåÆ `POST /analysis/candidate/{id}/publications`
- `getPublicationAnalysis(candidateId)` ΓåÆ `GET /analysis/candidate/{id}/publications`
- `uploadCombinedBulkPDF(file)` ΓåÆ `POST /cv/upload/bulk-combined`

---

### Frontend ΓÇö Ingestion Page

#### [MODIFY] [IngestionPage.jsx](file:///d:/talash/frontend/src/pages/IngestionPage.jsx)

Add a new **"Combined CV PDF Upload"** card:
- A file input for a single PDF containing multiple CVs.
- Upload button that calls `uploadCombinedBulkPDF`.
- Shows how many CVs were extracted and ingested.
- Clear explanation label: *"Upload a single PDF containing multiple CVs separated by blank pages."*

---

### Frontend ΓÇö Candidate Insights Page

#### [MODIFY] [CandidateInsightsPage.jsx](file:///d:/talash/frontend/src/pages/CandidateInsightsPage.jsx)

Add a **"Publication Analysis"** section:
- Button: **"Run Deep Publication Analysis"** ΓåÆ calls `runPublicationAnalysis()`.
- Displays rich results:
  - Publications table (title, type, year, impact factor, indexing badges)
  - Co-author analysis summary (total co-authors, most frequent, collaboration score)
  - Topic variability (dominant topic, diversity score, trend)
  - Journal/conference quality indicators (WoS, Scopus, predatory flag badges)

---

## Verification Plan

### Automated
- Restart backend, confirm `/docs` shows new endpoints.
- Test `POST /analysis/candidate/{id}/publications` returns structured data.
- Test `POST /cv/upload/bulk-combined` with a multi-CV PDF, confirm multiple candidates created.

### Manual (Browser)
- Open frontend Ingestion page ΓåÆ verify "Combined CV PDF" upload card is visible.
- Open Candidate Insights ΓåÆ select a candidate ΓåÆ click "Run Deep Publication Analysis" ΓåÆ verify results populate.

---

## Open Questions

> [!IMPORTANT]
> The second Groq key will be stored in the `.env` file. Confirm this is acceptable.

> [!NOTE]
> For publication analysis, the LLM will infer journal quality signals (WoS, Scopus, predatory) from the CV text itself ΓÇö it **cannot** do live internet lookups. The analysis is based purely on what's stated or implied in the CV. Is that acceptable, or should we add a known-journals database lookup as well?
