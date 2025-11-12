"""Master clock abstractions used for broadcasting logic.

The master clock supplies *station time*: a monotonic timeline that all runtime
components share. Station time may advance faster or slower than wall clock
time, but it never jumps backwards.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Callable, Protocol, runtime_checkable

import time

MonotonicFn = Callable[[], float]


@runtime_checkable
class MasterClock(Protocol):
    """Protocol implemented by master clock providers."""

    def now(self) -> float:
        """Return the current station time in seconds."""


@dataclass
class RealTimeMasterClock:
    """Master clock backed by a monotonic timer.

    Parameters
    ----------
    rate:
        Scale factor applied to elapsed monotonic time. A value of ``2.0``
        doubles perceived station time. Must be positive.
    start:
        Station time (seconds) to begin counting from.
    monotonic_fn:
        Injectable monotonic function, defaults to :func:`time.perf_counter`.
    """

    rate: float = 1.0
    start: float = 0.0
    monotonic_fn: MonotonicFn = field(default=time.perf_counter)

    def __post_init__(self) -> None:
        if self.rate <= 0.0:
            raise ValueError("rate must be greater than zero")
        self._origin_station: float = self.start
        self._origin_monotonic: float = self.monotonic_fn()

    def now(self) -> float:
        """Return the current station time in seconds."""
        elapsed = self.monotonic_fn() - self._origin_monotonic
        if elapsed < 0.0:
            # Guard against clock implementations that could return a smaller
            # value (should never happen with perf_counter, but keep safety).
            elapsed = 0.0
        return self._origin_station + elapsed * self.rate


class SteppedMasterClock:
    """Deterministic master clock used for tests.

    Station time advances only when :meth:`advance` is called.
    """

    def __init__(self, start: float = 0.0) -> None:
        self._current = start
        self._lock = Lock()

    def now(self) -> float:
        with self._lock:
            return self._current

    def advance(self, seconds: float) -> float:
        """Advance the clock by ``seconds`` (must be non-negative)."""
        if seconds < 0.0:
            raise ValueError("seconds must be non-negative")
        with self._lock:
            self._current += seconds
            return self._current

