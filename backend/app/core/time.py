from datetime import datetime, timezone


def utcnow_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def elapsed_hours_since(value: datetime | None, *, now: datetime | None = None) -> float:
    timestamp = as_utc(value)
    if timestamp is None:
        return 0.0
    current = as_utc(now or datetime.now(timezone.utc))
    return max((current - timestamp).total_seconds() / 3600, 0.0)
