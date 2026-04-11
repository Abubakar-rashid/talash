# TALASH

Talent Acquisition & Learning Automation for Smart Hiring.

TALASH is an in-progress full-stack project for CV ingestion, parsing, and candidate profiling. It currently supports PDF upload, text extraction, candidate storage, and LLM-based profile analysis.

## Project Status (So Far)

Implemented now:
- FastAPI backend with async PostgreSQL connection
- PDF upload and text extraction (PyMuPDF)
- Candidate records stored in database
- LLM analysis via Groq to extract structured profile fields
- React + Vite frontend for upload and candidate dashboard

Planned/partially scaffolded:
- Expanded research and analytics schema in `database_structure.csv`
- Additional modules under `backend/app/modules/`

## Tech Stack

Backend:
- FastAPI
- SQLAlchemy (async)
- PostgreSQL (`asyncpg`)
- PyMuPDF (`fitz`)
- Groq API client

Frontend:
- React
- Vite

## Repository Structure

```text
talash/
  backend/
    app/
      api/
      db/
      llm/
      modules/
    requirements.txt
  frontend/
    src/
  database_structure.csv
```

## Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Groq API key

## Backend Setup

From `talash/backend`:

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
```

Create `.env` in `talash/backend`:

```env
DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/talash
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-8b-instant
UPLOAD_DIR=uploads
```

Run backend:

```bash
uvicorn app.main:app --reload
```

Backend URLs:
- API root: http://localhost:8000/
- Health: http://localhost:8000/health
- Docs: http://localhost:8000/docs

## Frontend Setup

From `talash/frontend`:

```bash
npm install
npm run dev
```

Frontend default URL:
- http://localhost:5173

Note: frontend components currently call backend at `http://localhost:8000` directly.

## Current API Endpoints

Base prefix: `/cv`

- `POST /cv/upload`
  - Upload a PDF CV (`multipart/form-data`, field: `file`)
  - Extracts text and creates a candidate record
- `POST /cv/parse`
  - Parses a PDF already present in uploads folder (filename input)
- `GET /cv/candidates`
  - List all candidate records (summary)
- `GET /cv/candidate/{candidate_id}`
  - Get full candidate details, including raw text
- `POST /cv/candidate/{candidate_id}/analyze`
  - Run LLM analysis and persist structured fields

## Database Notes

- The running backend currently relies on the `candidates` table model in `backend/app/db/models.py`.
- A broader target schema for future modules exists in `database_structure.csv`.

## Quick Test Commands

From `talash/backend`:

```bash
python test_db.py
python app/test_llm.py
```

## Next Milestones

- Add migrations (Alembic flow) for the full schema
- Implement remaining extraction/analysis modules   
- Add authentication and role-based access
- Improve frontend UX and API configuration via environment variables
- Add automated tests for API and parsing pipeline
