import json
import os
import re
from uuid import uuid4

from .models import Rubric

STOPWORDS = {
    "a", "an", "the", "to", "for", "of", "and", "or", "is", "are", "in", "on", "with", "using",
    "write", "create", "draw", "find", "calculate", "program", "algorithm", "flowchart", "pseudocode",
}


def _slug(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return s[:36] if s else uuid4().hex[:10]


def _keywords_from_question(question: str) -> list[str]:
    parts = re.findall(r"[A-Za-z0-9_+\-]+", question.lower())
    out = []
    for p in parts:
        if len(p) < 3 or p in STOPWORDS:
            continue
        if p not in out:
            out.append(p)
    return out[:8]


def _fallback_rubric(question: str, answer_type: str, rubric_id: str | None) -> Rubric:
    q_keywords = _keywords_from_question(question)
    generated_id = rubric_id or f"{answer_type[:5]}-{_slug(question)}-v1"

    if answer_type == "flowchart":
        criteria = [
            {"id": "symbols", "name": "Symbol Usage", "description": "Uses correct start/process/decision/end symbols", "max_score": 3, "keywords": ["start", "process", "decision", "end"] + q_keywords[:2]},
            {"id": "flow", "name": "Flow Logic", "description": "Correct path and decision branching", "max_score": 4, "keywords": ["yes", "no", "condition"] + q_keywords[:3]},
            {"id": "completeness", "name": "Completeness", "description": "Covers full problem flow including output", "max_score": 2, "keywords": ["input", "output"] + q_keywords[:2]},
            {"id": "clarity", "name": "Readability", "description": "Neat and readable chart with arrows", "max_score": 1, "keywords": ["arrow", "label"]},
        ]
    elif answer_type == "pseudocode":
        criteria = [
            {"id": "syntax", "name": "Pseudo Syntax", "description": "Uses consistent pseudocode conventions", "max_score": 3, "keywords": ["begin", "end", "if", "while"]},
            {"id": "logic", "name": "Logical Steps", "description": "Step-by-step correct logic for the question", "max_score": 4, "keywords": q_keywords[:4] or ["step", "logic"]},
            {"id": "vars", "name": "Variables and Conditions", "description": "Correct variables/conditions/updates", "max_score": 2, "keywords": ["variable", "condition", "update"] + q_keywords[:2]},
            {"id": "clarity", "name": "Clarity", "description": "Readable indentation and structure", "max_score": 1, "keywords": ["indent", "return"]},
        ]
    else:
        criteria = [
            {"id": "understanding", "name": "Problem Understanding", "description": "Captures required inputs/outputs", "max_score": 2, "keywords": ["input", "output"] + q_keywords[:2]},
            {"id": "logic", "name": "Core Logic", "description": "Correct algorithmic steps for solving the problem", "max_score": 4, "keywords": q_keywords[:5] or ["step", "condition", "loop"]},
            {"id": "correctness", "name": "Correctness", "description": "Handles conditions and expected result", "max_score": 2, "keywords": ["if", "else", "return"] + q_keywords[:2]},
            {"id": "complexity", "name": "Complexity / Efficiency", "description": "Mentions or implies reasonable efficiency", "max_score": 2, "keywords": ["time", "space", "complexity"]},
        ]

    return Rubric(
        id=generated_id,
        title=f"{question.strip().capitalize()} - {answer_type.capitalize()} Rubric",
        question=question,
        answer_type=answer_type,
        criteria=criteria,
    )


def _llm_rubric(question: str, answer_type: str, rubric_id: str | None) -> Rubric | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        prompt = {
            "task": "Create a grading rubric JSON for student answers.",
            "constraints": {
                "answer_type": answer_type,
                "total_score": 10,
                "criteria_count": 4,
                "fields": ["id", "title", "question", "answer_type", "criteria"],
                "criterion_fields": ["id", "name", "description", "max_score", "keywords"],
            },
            "question": question,
            "rubric_id": rubric_id,
            "output": "Return only strict JSON object.",
        }

        resp = client.responses.create(
            model="gpt-4o-mini",
            input=json.dumps(prompt),
            temperature=0.2,
        )
        text = (resp.output_text or "").strip()
        parsed = json.loads(text)
        if rubric_id:
            parsed["id"] = rubric_id
        return Rubric.model_validate(parsed)
    except Exception:
        return None


def generate_rubric(question: str, answer_type: str, rubric_id: str | None = None) -> Rubric:
    llm = _llm_rubric(question=question, answer_type=answer_type, rubric_id=rubric_id)
    if llm:
        return llm
    return _fallback_rubric(question=question, answer_type=answer_type, rubric_id=rubric_id)
