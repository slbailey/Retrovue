from __future__ import annotations

import time

import pytest

from retrovue.runtime.clock import RealTimeMasterClock, SteppedMasterClock


def test_real_time_master_clock_monotonic():
    clock = RealTimeMasterClock()
    first = clock.now()
    time.sleep(0.01)
    second = clock.now()
    assert second >= first


def test_real_time_master_clock_scale_factor():
    current = 0.0

    def fake_monotonic() -> float:
        return current

    clock = RealTimeMasterClock(rate=2.0, start=10.0, monotonic_fn=fake_monotonic)
    assert clock.now() == pytest.approx(10.0)
    current += 5.0
    assert clock.now() == pytest.approx(20.0)
    current += 1.25
    assert clock.now() == pytest.approx(22.5)


def test_real_time_master_clock_requires_positive_rate():
    with pytest.raises(ValueError):
        RealTimeMasterClock(rate=0.0)
    with pytest.raises(ValueError):
        RealTimeMasterClock(rate=-1.0)


def test_stepped_master_clock_advances_only_when_requested():
    clock = SteppedMasterClock(start=5.0)
    assert clock.now() == pytest.approx(5.0)
    time.sleep(0.01)
    assert clock.now() == pytest.approx(5.0)
    clock.advance(3.25)
    assert clock.now() == pytest.approx(8.25)


def test_stepped_master_clock_rejects_negative_advances():
    clock = SteppedMasterClock()
    with pytest.raises(ValueError):
        clock.advance(-0.1)


