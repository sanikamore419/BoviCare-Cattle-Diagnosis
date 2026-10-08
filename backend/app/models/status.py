from enum import Enum


class CaseStatus(str, Enum):
    SUBMITTED = "submitted"
    AI_COMPLETE = "ai_complete"
    PENDING_REVIEW = "pending_review"
    IN_REVIEW = "in_review"
    COMPLETED = "completed"


CASE_STATUSES = tuple(status.value for status in CaseStatus)
CASE_STATUS_CHECK = "status IN ('submitted', 'ai_complete', 'pending_review', 'in_review', 'completed')"
