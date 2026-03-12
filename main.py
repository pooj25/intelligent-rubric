from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request

from app.evaluator import evaluate_answer
from app.extractor import extract_text
from app.models import GenerateRubricRequest, Rubric
from app.rubric_generator import generate_rubric
from app.storage import (
    delete_rubric,
    get_analysis,
    get_rubric,
    init_db,
    list_submissions,
    load_rubrics,
    save_submission,
    upsert_rubric,
)

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_TYPES = {"algorithm", "flowchart", "pseudocode"}
ALLOWED_SUFFIXES = {".pdf", ".docx", ".png", ".jpg", ".jpeg", ".txt", ".md", ".bmp", ".tiff", ".webp"}

app = FastAPI(title="Intelligent Rubrics Evaluation API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.on_event("startup")
async def startup_event() -> None:
    init_db()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/teacher", response_class=HTMLResponse)
async def teacher_page(request: Request):
    return templates.TemplateResponse("teacher.html", {"request": request})


@app.get("/student", response_class=HTMLResponse)
async def student_page(request: Request):
    return templates.TemplateResponse("student.html", {"request": request})


@app.get("/records", response_class=HTMLResponse)
async def records_page(request: Request):
    return templates.TemplateResponse("records.html", {"request": request})


@app.get("/analysis", response_class=HTMLResponse)
async def analysis_page(request: Request):
    return templates.TemplateResponse("analysis.html", {"request": request})


@app.get("/api/rubrics")
async def list_rubrics(answer_type: str | None = Query(default=None)):
    rubrics = load_rubrics()
    if answer_type:
        normalized = answer_type.strip().lower()
        if normalized not in ALLOWED_TYPES:
            raise HTTPException(status_code=400, detail="answer_type must be algorithm, flowchart, or pseudocode")
        rubrics = [r for r in rubrics if r.answer_type.lower() == normalized]
    return [r.model_dump() for r in rubrics]


@app.post("/api/rubrics")
async def create_or_update_rubric(rubric: Rubric):
    if rubric.answer_type.lower() not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Rubric answer_type must be algorithm, flowchart, or pseudocode")
    upsert_rubric(rubric)
    return {"message": "Rubric saved", "rubric_id": rubric.id}


@app.post("/api/rubrics/generate")
async def generate_rubric_api(payload: GenerateRubricRequest):
    answer_type = payload.answer_type.strip().lower()
    if answer_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="answer_type must be algorithm, flowchart, or pseudocode")

    rubric = generate_rubric(
        question=payload.question,
        answer_type=answer_type,
        rubric_id=payload.rubric_id,
    )
    return rubric.model_dump()


@app.delete("/api/rubrics/{rubric_id}")
async def remove_rubric(rubric_id: str):
    ok = delete_rubric(rubric_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Rubric not found")
    return {"message": "Rubric deleted", "rubric_id": rubric_id}


@app.post("/api/evaluate")
async def evaluate_submission(
    rubric_id: str = Form(...),
    student_name: str = Form(...),
    answer_file: UploadFile = File(...),
):
    rubric = get_rubric(rubric_id)
    if not rubric:
        raise HTTPException(status_code=404, detail="Rubric not found")

    suffix = Path(answer_file.filename or "upload.bin").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    saved = UPLOAD_DIR / f"{uuid4().hex}{suffix}"
    with saved.open("wb") as f:
        f.write(await answer_file.read())

    extracted_text = extract_text(saved)
    extraction_warning = None
    if not extracted_text.strip():
        extraction_warning = (
            "No readable text extracted. Evaluated with low-confidence placeholder. "
            "For better results use clearer image/PDF or enable OCR dependencies."
        )
        extracted_text = (
            "Student submitted content but OCR extraction returned empty text. "
            "Evaluate structure manually if needed."
        )

    result = evaluate_answer(rubric=rubric, student_name=student_name, answer_text=extracted_text)
    payload = result.model_dump()
    payload["extracted_preview"] = extracted_text[:1200]
    payload["rubric_type"] = rubric.answer_type
    payload["extraction_warning"] = extraction_warning

    submission_id = save_submission(
        student_name=student_name,
        rubric_id=rubric.id,
        rubric_type=rubric.answer_type,
        total_score=payload["total_score"],
        max_total_score=payload["max_total_score"],
        percentage=payload["percentage"],
        extracted_preview=payload["extracted_preview"],
        extraction_warning=payload["extraction_warning"],
        result_payload=payload,
    )
    payload["submission_id"] = submission_id

    return payload


@app.get("/api/submissions")
async def get_submissions(
    answer_type: str | None = Query(default=None),
    student_name: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
):
    if answer_type and answer_type.lower() not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="answer_type must be algorithm, flowchart, or pseudocode")
    return list_submissions(limit=limit, answer_type=answer_type, student_name=student_name)


@app.get("/api/analysis")
async def analysis_api():
    return get_analysis()


@app.get("/api/health")
async def health():
    return {"status": "ok"}
