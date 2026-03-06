import json
import os
import re
from dataclasses import dataclass

from .models import CriterionResult, EvaluationResult, Rubric


@dataclass
class ScoreConfig:
    min_text_len: int = 50
    keyword_weight: float = 0.8
    length_weight: float = 0.2


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _keyword_coverage(text: str, keywords: list[str]) -> float:
    if not keywords:
        return 0.7

    t = _normalize(text)
    hit = 0
    for kw in keywords:
        if kw.lower() in t:
            hit += 1
    return hit / len(keywords)


def _score_criterion(answer_text: str, max_score: float, keywords: list[str], cfg: ScoreConfig) -> float:
    coverage = _keyword_coverage(answer_text, keywords)
    length_factor = min(len(answer_text) / cfg.min_text_len, 1.0)
    weighted = (coverage * cfg.keyword_weight) + (length_factor * cfg.length_weight)
    return round(max_score * max(0.0, min(weighted, 1.0)), 2)


def _reason(score: float, max_score: float, keywords: list[str], answer_text: str) -> str:
    if score >= 0.85 * max_score:
        return "Criterion largely satisfied with relevant technical content."
    if score >= 0.55 * max_score:
        return "Partially satisfied. Add clearer logic and more rubric keywords."
    if len(answer_text.strip()) < 15:
        return "Very limited answer content found after extraction."
    if keywords:
        return f"Key rubric concepts missing: {', '.join(keywords[:3])}."
    return "Criterion needs more complete and structured explanation."


def _generate_llm_feedback(rubric: Rubric, answer_text: str, result: EvaluationResult) -> str | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        prompt = {
            "rubric": rubric.model_dump(),
            "answer_excerpt": answer_text[:3000],
            "evaluation": result.model_dump(),
            "instruction": "Give concise student feedback with strengths, weak areas, and exact next improvements for algorithm/flowchart/pseudocode writing.",
        }
        resp = client.responses.create(
            model="gpt-4o-mini",
            input=json.dumps(prompt),
            temperature=0.2,
        )
        return (resp.output_text or "").strip()[:2000]
    except Exception:
        return None


def evaluate_answer(rubric: Rubric, student_name: str, answer_text: str) -> EvaluationResult:
    cfg = ScoreConfig()
    rows: list[CriterionResult] = []

    for c in rubric.criteria:
        s = _score_criterion(answer_text, c.max_score, c.keywords, cfg)
        rows.append(
            CriterionResult(
                criterion_id=c.id,
                criterion_name=c.name,
                score=s,
                max_score=c.max_score,
                reason=_reason(s, c.max_score, c.keywords, answer_text),
            )
        )

    total = round(sum(x.score for x in rows), 2)
    max_total = round(sum(x.max_score for x in rows), 2)
    percentage = round((total / max_total) * 100, 2) if max_total else 0.0

    strengths = [x.criterion_name for x in rows if x.score >= 0.75 * x.max_score]
    improvements = [x.criterion_name for x in rows if x.score < 0.75 * x.max_score]

    feedback = (
        f"Hi {student_name}, your score is {total}/{max_total} ({percentage}%). "
        f"Strong areas: {', '.join(strengths) if strengths else 'none yet'}. "
        f"Improve next: {', '.join(improvements) if improvements else 'keep the same quality across all criteria'}."
    )

    result = EvaluationResult(
        student_name=student_name,
        rubric_id=rubric.id,
        total_score=total,
        max_total_score=max_total,
        percentage=percentage,
        criterion_results=rows,
        strengths=strengths,
        improvements=improvements,
        instant_feedback=feedback,
    )

    llm_feedback = _generate_llm_feedback(rubric, answer_text, result)
    if llm_feedback:
        result.instant_feedback = llm_feedback

    return result
