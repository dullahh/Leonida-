from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ReplayClock:
    def __init__(self, origin: datetime):
        if origin.tzinfo is None:
            raise ValueError("aware origin required")
        self._now = origin

    def now(self) -> datetime:
        return self._now

    def advance_to(self, at: datetime) -> None:
        if at.tzinfo is None or at < self._now:
            raise ValueError("clock cannot go backwards or become naive")
        self._now = at
