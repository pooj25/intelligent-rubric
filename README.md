# Intelligent Rubrics Evaluation System

Python FastAPI project for rubric-based evaluation of algorithm / flowchart / pseudocode submissions.

## New Dashboard Structure
- `/` Home
- `/teacher` Teacher Dashboard
- `/student` Student Dashboard
- `/records` Student Records Dashboard
- `/analysis` Analysis Dashboard

## Core Features
- Teacher can auto-generate rubric from any question.
- Teacher can edit/save/delete rubric cards.
- Separate rubric access by answer type (`algorithm`, `flowchart`, `pseudocode`).
- Student uploads `PDF/DOCX/PNG/JPG/TXT/...` and gets instant score + feedback.
- Every evaluation is stored as submission record.
- Analysis API provides overall stats and weak criteria trends.

## Auto Rubric Generation
- API: `POST /api/rubrics/generate`
- Input: `question`, `answer_type`, optional `rubric_id`
- If `OPENAI_API_KEY` available: smarter AI-generated rubric
- Else: built-in heuristic rubric generator fallback

## Database
- SQLite file: `data/rubrics.db`
- Tables:
  - `rubrics`
  - `submissions`
- Legacy `data/rubrics.json` auto-migrates to DB on startup (if rubrics table is empty).

## Run
```bash
cd intelligent-rubrics
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Open in browser:
- `http://127.0.0.1:8000/`

## APIs
- `GET /api/rubrics`
- `POST /api/rubrics`
- `POST /api/rubrics/generate`
- `DELETE /api/rubrics/{rubric_id}`
- `POST /api/evaluate`
- `GET /api/submissions`
- `GET /api/analysis`

## Notes
- OCR quality depends on document clarity and Tesseract availability.
- Install Tesseract and ensure it is in PATH for better image/PDF text extraction.
