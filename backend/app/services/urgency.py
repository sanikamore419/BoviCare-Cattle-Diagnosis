"""Pure urgency scoring rules for review prioritization.

These are design constants, not clinically validated thresholds. Veterinary
review is required before using the score for clinical decisions.
"""
from __future__ import annotations

import math
from collections.abc import Iterable


DISEASE_SEVERITY_WEIGHT = 30
AI_CONFIDENCE_WEIGHT = 25
SYMPTOM_COUNT_WEIGHT = 20
WAITING_TIME_WEIGHT = 15
ANIMAL_AGE_RISK_WEIGHT = 10

SYMPTOM_POINTS_EACH = 4
MAX_SYMPTOMS_COUNTED = SYMPTOM_COUNT_WEIGHT // SYMPTOM_POINTS_EACH
WAITING_TIME_SATURATION_HOURS = 12

AGE_RISK_MODERATE_YEARS = 3
AGE_RISK_ELEVATED_YEARS = 5
AGE_RISK_HIGH_YEARS = 8
AGE_RISK_MODERATE_POINTS = 3
AGE_RISK_ELEVATED_POINTS = 6
AGE_RISK_HIGH_POINTS = ANIMAL_AGE_RISK_WEIGHT

HIGH_URGENCY_MIN = 70
MEDIUM_URGENCY_MIN = 40
MAX_URGENCY_SCORE = 100

SEVERITY_POINTS = {"low": 5, "medium": 15, "high": 30, "urgent": 30}
DISEASE_SEVERITY = {
    "healthy": "low", "healthy appearance": "low",
    "fmd": "high", "foot-and-mouth disease": "high", "foot-and-mouth": "high",
    "lsd": "high", "lumpy skin disease": "high", "lumpy": "high",
    "ringworm": "medium", "ibk": "medium", "pediculosis": "medium",
    "dermatophilosis": "medium",
}


def _severity(finding: str | None) -> tuple[int, str]:
    normalized = str(finding or "").strip().lower().replace("_", " ")
    level = DISEASE_SEVERITY.get(normalized, normalized)
    return SEVERITY_POINTS.get(level, 0), level if level in SEVERITY_POINTS else "unknown"


def _confidence(value: float | int | None) -> float:
    try:
        parsed = float(value) if value is not None else 0.0
    except (TypeError, ValueError):
        return 0.0
    if not math.isfinite(parsed):
        return 0.0
    return min(1.0, max(0.0, parsed))


def calculate_urgency(
    *,
    findings: Iterable[str | None],
    confidence_scores: Iterable[float | int | None],
    symptom_count: int,
    waiting_hours: float,
    animal_age_years: float | None,
) -> dict:
    """Return score and full component breakdown without side effects.

    Findings and confidences are reduced independently by maximum. Separate
    model outputs are never averaged or merged into a synthetic probability.
    """
    severity_candidates = [(_severity(item)[0], _severity(item)[1], str(item or "")) for item in findings]
    disease_points, severity_level, top_finding = max(severity_candidates, default=(0, "unknown", ""), key=lambda row: row[0])

    confidences = [_confidence(item) for item in confidence_scores]
    confidence = max(confidences, default=0.0)
    confidence_points = confidence * AI_CONFIDENCE_WEIGHT

    count = max(0, int(symptom_count or 0))
    counted_symptoms = min(count, MAX_SYMPTOMS_COUNTED)
    symptom_points = counted_symptoms * SYMPTOM_POINTS_EACH

    try:
        wait = max(0.0, float(waiting_hours))
    except (TypeError, ValueError):
        wait = 0.0
    if not math.isfinite(wait):
        wait = 0.0
    waiting_points = min(WAITING_TIME_WEIGHT, wait / WAITING_TIME_SATURATION_HOURS * WAITING_TIME_WEIGHT)

    try:
        age = float(animal_age_years) if animal_age_years is not None else None
    except (TypeError, ValueError):
        age = None
    if age is not None and not math.isfinite(age):
        age = None
    age_points = 0
    if age is not None:
        if age >= AGE_RISK_HIGH_YEARS:
            age_points = AGE_RISK_HIGH_POINTS
        elif age >= AGE_RISK_ELEVATED_YEARS:
            age_points = AGE_RISK_ELEVATED_POINTS
        elif age >= AGE_RISK_MODERATE_YEARS:
            age_points = AGE_RISK_MODERATE_POINTS

    total = min(MAX_URGENCY_SCORE, disease_points + confidence_points + symptom_points + waiting_points + age_points)
    score = round(total, 2)
    level = "HIGH" if score >= HIGH_URGENCY_MIN else "MEDIUM" if score >= MEDIUM_URGENCY_MIN else "LOW"
    return {
        "score": score,
        "level": level,
        "breakdown": {
            "disease_severity_points": disease_points,
            "disease_severity_level": severity_level,
            "highest_severity_finding": top_finding,
            "ai_confidence": round(confidence, 4),
            "ai_confidence_points": round(confidence_points, 2),
            "symptoms_count": count,
            "symptoms_counted": counted_symptoms,
            "symptom_points": symptom_points,
            "waiting_hours": round(wait, 2),
            "waiting_points": round(waiting_points, 2),
            "animal_age_years": age,
            "animal_age_points": age_points,
            "weights": {
                "disease_severity": DISEASE_SEVERITY_WEIGHT,
                "ai_confidence": AI_CONFIDENCE_WEIGHT,
                "symptoms": SYMPTOM_COUNT_WEIGHT,
                "waiting_time": WAITING_TIME_WEIGHT,
                "animal_age_risk": ANIMAL_AGE_RISK_WEIGHT,
            },
        },
    }
