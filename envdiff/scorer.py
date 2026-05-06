"""Score an .env file for overall quality and hygiene."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envdiff.linter import lint_env_file, LintIssue
from envdiff.profiler import profile_env_file
from envdiff.redactor import Redactor

_ERROR_PENALTY = 20
_WARNING_PENALTY = 5
_EMPTY_PENALTY = 3
_SENSITIVE_UNREDACTED_PENALTY = 10


@dataclass
class ScoreReport:
    file: str
    score: int
    max_score: int = 100
    penalties: List[str] = field(default_factory=list)

    @property
    def grade(self) -> str:
        pct = self.score / self.max_score * 100
        if pct >= 90:
            return "A"
        if pct >= 75:
            return "B"
        if pct >= 60:
            return "C"
        if pct >= 40:
            return "D"
        return "F"

    def to_dict(self) -> dict:
        return {
            "file": self.file,
            "score": self.score,
            "max_score": self.max_score,
            "grade": self.grade,
            "penalties": self.penalties,
        }


def score_env_file(path: str) -> ScoreReport:
    """Compute a quality score for the given .env file."""
    score = 100
    penalties: List[str] = []

    lint_result = lint_env_file(path)
    errors = [i for i in lint_result.issues if i.severity == "error"]
    warnings = [i for i in lint_result.issues if i.severity == "warning"]

    if errors:
        deduction = min(len(errors) * _ERROR_PENALTY, 60)
        score -= deduction
        penalties.append(f"{len(errors)} lint error(s) (-{deduction})")

    if warnings:
        deduction = min(len(warnings) * _WARNING_PENALTY, 20)
        score -= deduction
        penalties.append(f"{len(warnings)} lint warning(s) (-{deduction})")

    profile = profile_env_file(path)
    if profile.empty_keys:
        deduction = min(len(profile.empty_keys) * _EMPTY_PENALTY, 15)
        score -= deduction
        penalties.append(f"{len(profile.empty_keys)} empty key(s) (-{deduction})")

    redactor = Redactor()
    sensitive_plain = [
        k for k in profile.sensitive_keys
        if not redactor.is_sensitive(k) or profile.env.get(k, "") != ""
    ]
    if sensitive_plain:
        deduction = min(len(sensitive_plain) * _SENSITIVE_UNREDACTED_PENALTY, 20)
        score -= deduction
        penalties.append(f"{len(sensitive_plain)} sensitive key(s) with values (-{deduction})")

    score = max(score, 0)
    return ScoreReport(file=path, score=score, penalties=penalties)
