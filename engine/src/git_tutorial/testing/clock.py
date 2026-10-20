from __future__ import annotations


class FakeClock:
    """Advances instead of blocking, so loop tests run at full speed."""

    def __init__(self, start: float = 1_700_000_000.0) -> None:
        self._t = start
        self.slept: list[float] = []

    def now(self) -> float:
        return self._t

    def monotonic(self) -> float:
        return self._t

    def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
        self._t += seconds

    def advance(self, seconds: float) -> None:
        self._t += seconds
