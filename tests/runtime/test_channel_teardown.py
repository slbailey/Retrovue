from __future__ import annotations

from datetime import datetime, timedelta

from retrovue.runtime.channel_manager import ChannelManager
from retrovue.runtime.metrics import ChannelMetricsSample
from retrovue.runtime.producer.base import ContentSegment, ProducerStatus
from retrovue.runtime.producer.ffmpeg_segment_producer import FFmpegSegmentProducer


class ClockAdapter:
    """Wrap SteppedMasterClock semantics for channel manager tests."""

    def __init__(self) -> None:
        from retrovue.runtime.clock import SteppedMasterClock

        self._clock = SteppedMasterClock()
        self._baseline = datetime.fromtimestamp(1_700_100_000)

    def now(self) -> float:
        return self._clock.now()

    def advance(self, seconds: float) -> None:
        self._clock.advance(seconds)

    def get_current_time(self) -> datetime:
        return self._baseline + timedelta(seconds=self._clock.now())


class StubScheduleService:
    def get_playout_plan_now(self, channel_id: str, at_station_time: datetime) -> list[dict]:
        return []


class StubProgramDirector:
    def get_channel_mode(self, channel_id: str) -> str:
        return "normal"


def _make_segment(start_offset: float, duration: float) -> ContentSegment:
    start = datetime.fromtimestamp(1_700_100_000 + start_offset)
    end = start + timedelta(seconds=duration)
    return ContentSegment(
        asset_id=f"asset-{start_offset}",
        start_time=start,
        end_time=end,
        segment_type="content",
        metadata={},
    )


def test_channel_manager_graceful_teardown():
    clock = ClockAdapter()
    manager = ChannelManager(
        channel_id="chan-teardown",
        clock=clock,
        schedule_service=StubScheduleService(),
        program_director=StubProgramDirector(),
    )

    segment = _make_segment(0.0, 5.0)
    producer = FFmpegSegmentProducer("chan-teardown", {"output_url": "pipe:1"})
    producer.start([segment], segment.start_time)

    manager.active_producer = producer
    manager.runtime_state.producer_status = "running"
    manager.runtime_state.stream_endpoint = producer.get_stream_endpoint()
    manager.viewer_sessions["viewer-1"] = {"joined": clock.get_current_time()}
    manager.runtime_state.viewer_count = 1

    manager.viewer_leave("viewer-1")
    assert manager.runtime_state.viewer_count == 0
    assert producer.teardown_in_progress() is True
    assert producer.status == ProducerStatus.STOPPING

    # Advance time so teardown can complete.
    for _ in range(5):
        clock.advance(0.2)
        producer.on_paced_tick(clock.now(), 0.2)
        manager.check_health()

    assert manager.active_producer is None
    assert manager.runtime_state.producer_status == "stopped"

    sample = ChannelMetricsSample()
    manager.populate_metrics_sample(sample)
    assert sample.channel_state == "idle"
    assert sample.viewer_count == 0
    assert sample.producer_state == "stopped"

