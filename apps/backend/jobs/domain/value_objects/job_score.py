"""JobScore value object — represents scoring metrics for a job."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

VALID_GRADES = ['P', 'E', 'D', 'C', 'B', 'A', 'A+', 'A++']
GRADE_RANK = {g: i for i, g in enumerate(VALID_GRADES)}
NUMERIC_TO_GRADE = {
    range(0, 30): 'D', range(30, 50): 'C', range(50, 70): 'B',
    range(70, 80): 'A', range(80, 90): 'A+', range(90, 101): 'A++',
}


def numeric_to_grade(score: int | float | None) -> str:
    """Convert a numeric score (0-100) to a letter grade."""
    if score is None:
        return 'P'
    n = max(0, min(100, int(score)))
    for r, g in NUMERIC_TO_GRADE.items():
        if n in r:
            return g
    return 'P'


def normalize_score(score) -> str:
    """Ensure score is a valid letter grade. Converts numeric or invalid values."""
    if isinstance(score, str):
        s = score.strip().upper().replace(' ', '')
        if s in VALID_GRADES:
            return s
        try:
            return numeric_to_grade(int(float(s)))
        except (ValueError, TypeError):
            pass
    elif isinstance(score, (int, float)):
        return numeric_to_grade(int(score))
    return 'P'


@dataclass(frozen=True)
class JobScore:
    """Value object representing job scoring metrics."""

    fit_score: Optional[int] = None
    success_score: Optional[int] = None
    overall_score: Optional[int] = None
    letter_grade: str = "P"

    @classmethod
    def calculate(cls, fit_score: int | None, success_score: int | None) -> JobScore:
        """Calculate overall score and letter grade from fit and success scores."""
        overall = None
        if fit_score is not None and success_score is not None:
            overall = round(fit_score * 0.6 + success_score * 0.4, 1)
        letter = numeric_to_grade(overall)
        return cls(
            fit_score=fit_score,
            success_score=success_score,
            overall_score=overall,
            letter_grade=letter,
        )
