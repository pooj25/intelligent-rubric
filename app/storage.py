import json
import sqlite3
from pathlib import Path

from .models import Rubric

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "rubrics.db"
LEGACY_JSON_PATH = DATA_DIR / "rubrics.json"

CREATE_RUBRICS_SQL = """
CREATE TABLE IF NOT EXISTS rubrics (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    question TEXT NOT NULL,
    answer_type TEXT NOT NULL,
    criteria_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_SUBMISSIONS_SQL = """
CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_name TEXT NOT NULL,
    rubric_id TEXT NOT NULL,
    rubric_type TEXT NOT NULL,
    total_score REAL NOT NULL,
    max_total_score REAL NOT NULL,
    percentage REAL NOT NULL,
    extracted_preview TEXT,
    extraction_warning TEXT,
    result_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute(CREATE_RUBRICS_SQL)
        conn.execute(CREATE_SUBMISSIONS_SQL)
        conn.commit()
    _migrate_legacy_json_if_needed()


def _migrate_legacy_json_if_needed() -> None:
    if not LEGACY_JSON_PATH.exists():
        return

    try:
        raw = json.loads(LEGACY_JSON_PATH.read_text(encoding="utf-8"))
    except Exception:
        return

    if not isinstance(raw, list) or not raw:
        return

    with _connect() as conn:
        row = conn.execute("SELECT COUNT(*) AS c FROM rubrics").fetchone()
        if row["c"] > 0:
            return

        for item in raw:
            rubric = Rubric.model_validate(item)
            conn.execute(
                """
                INSERT OR REPLACE INTO rubrics (id, title, question, answer_type, criteria_json, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    rubric.id,
                    rubric.title,
                    rubric.question,
                    rubric.answer_type,
                    json.dumps([c.model_dump() for c in rubric.criteria]),
                ),
            )
        conn.commit()


def _row_to_rubric(row: sqlite3.Row) -> Rubric:
    return Rubric(
        id=row["id"],
        title=row["title"],
        question=row["question"],
        answer_type=row["answer_type"],
        criteria=json.loads(row["criteria_json"]),
    )


def load_rubrics() -> list[Rubric]:
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, title, question, answer_type, criteria_json FROM rubrics ORDER BY updated_at DESC"
        ).fetchall()
    return [_row_to_rubric(r) for r in rows]


def get_rubric(rubric_id: str) -> Rubric | None:
    init_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT id, title, question, answer_type, criteria_json FROM rubrics WHERE id = ?",
            (rubric_id,),
        ).fetchone()
    return _row_to_rubric(row) if row else None


def upsert_rubric(rubric: Rubric) -> None:
    init_db()
    with _connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO rubrics (id, title, question, answer_type, criteria_json, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                rubric.id,
                rubric.title,
                rubric.question,
                rubric.answer_type,
                json.dumps([c.model_dump() for c in rubric.criteria]),
            ),
        )
        conn.commit()


def delete_rubric(rubric_id: str) -> bool:
    init_db()
    with _connect() as conn:
        cur = conn.execute("DELETE FROM rubrics WHERE id = ?", (rubric_id,))
        conn.commit()
        return cur.rowcount > 0


def save_submission(
    student_name: str,
    rubric_id: str,
    rubric_type: str,
    total_score: float,
    max_total_score: float,
    percentage: float,
    extracted_preview: str,
    extraction_warning: str | None,
    result_payload: dict,
) -> int:
    init_db()
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO submissions (
                student_name, rubric_id, rubric_type, total_score, max_total_score, percentage,
                extracted_preview, extraction_warning, result_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                student_name,
                rubric_id,
                rubric_type,
                total_score,
                max_total_score,
                percentage,
                extracted_preview,
                extraction_warning,
                json.dumps(result_payload),
            ),
        )
        conn.commit()
        return int(cur.lastrowid)


def list_submissions(limit: int = 200, answer_type: str | None = None, student_name: str | None = None) -> list[dict]:
    init_db()
    query = """
    SELECT id, student_name, rubric_id, rubric_type, total_score, max_total_score, percentage,
           extracted_preview, extraction_warning, result_json, created_at
    FROM submissions
    WHERE 1=1
    """
    params: list[object] = []

    if answer_type:
        query += " AND lower(rubric_type)=?"
        params.append(answer_type.lower())
    if student_name:
        query += " AND lower(student_name) LIKE ?"
        params.append(f"%{student_name.lower()}%")

    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    with _connect() as conn:
        rows = conn.execute(query, params).fetchall()

    out = []
    for r in rows:
        item = dict(r)
        item["result_json"] = json.loads(item["result_json"])
        out.append(item)
    return out


def get_analysis() -> dict:
    rows = list_submissions(limit=1000)
    total = len(rows)

    if total == 0:
        return {
            "total_submissions": 0,
            "average_percentage": 0,
            "by_type": [],
            "top_weak_criteria": [],
            "student_count": 0,
        }

    avg = round(sum(r["percentage"] for r in rows) / total, 2)

    type_map: dict[str, list[float]] = {}
    weak_map: dict[str, int] = {}
    student_set = set()

    for r in rows:
        t = r["rubric_type"]
        student_set.add(r["student_name"].strip().lower())
        type_map.setdefault(t, []).append(r["percentage"])

        result = r["result_json"]
        for c in result.get("criterion_results", []):
            max_score = c.get("max_score", 0) or 0
            score = c.get("score", 0) or 0
            if max_score > 0 and (score / max_score) < 0.6:
                name = c.get("criterion_name", "Unknown")
                weak_map[name] = weak_map.get(name, 0) + 1

    by_type = [
        {"type": k, "count": len(v), "avg_percentage": round(sum(v) / len(v), 2)}
        for k, v in type_map.items()
    ]
    by_type.sort(key=lambda x: x["type"])

    weak = [{"criterion": k, "count": v} for k, v in weak_map.items()]
    weak.sort(key=lambda x: x["count"], reverse=True)

    return {
        "total_submissions": total,
        "average_percentage": avg,
        "by_type": by_type,
        "top_weak_criteria": weak[:8],
        "student_count": len(student_set),
    }
