from pydantic import BaseModel, Field


class RubricCriterion(BaseModel):
    id: str
    name: str
    description: str
    max_score: float = Field(..., gt=0)
    keywords: list[str] = Field(default_factory=list)


class Rubric(BaseModel):
    id: str
    title: str
    question: str
    answer_type: str = "algorithm"
    criteria: list[RubricCriterion]


class CriterionResult(BaseModel):
    criterion_id: str
    criterion_name: str
    score: float
    max_score: float
    reason: str


class EvaluationResult(BaseModel):
    student_name: str
    rubric_id: str
    total_score: float
    max_total_score: float
    percentage: float
    criterion_results: list[CriterionResult]
    strengths: list[str]
    improvements: list[str]
    instant_feedback: str


class GenerateRubricRequest(BaseModel):
    question: str = Field(..., min_length=4)
    answer_type: str = "algorithm"
    rubric_id: str | None = None
