from __future__ import annotations

import time
from datetime import datetime, timedelta

from retrovue.runtime.clock import RealTimeMasterClock, SteppedMasterClock
from retrovue.runtime.metrics import ChannelMetricsSample, MetricsPublisher
from retrovue.runtime.pace import PaceController
from retrovue.runtime.producer.ffmpeg_segment_producer import FFmpegSegmentProducer
from retrovue.runtime.producer.base import ContentSegment, ProducerStatus
from retrovue.runtime.channel_manager import ChannelManager


class ClockAdapter:
    """Wrap SteppedMasterClock with datetime support expected by ChannelManager."""

    def __init__(self) -> None:
        self._clock = SteppedMasterClock()
        self._basis = datetime.fromtimestamp(1_700_000_000)

    def now(self) -> float:
        return self._clock.now()

    def advance(self, seconds: float) -> None:
        self._clock.advance(seconds)

    def get_current_time(self) -> datetime:
        return self._basis + timedelta(seconds=self._clock.now())


class StubScheduleService:
    def get_playout_plan_now(self, channel_id: str, at_station_time: datetime) -> list[dict]:
        return []


class StubProgramDirector:
    def get_channel_mode(self, channel_id: str) -> str:
        return "normal"


def _make_segment(offset: float, duration: float) -> ContentSegment:
    start = datetime.fromtimestamp(1_700_000_000 + offset)
    end = start + timedelta(seconds=duration)
    return ContentSegment(
        asset_id=f"asset-{offset}",
        start_time=start,
        end_time=end,
        segment_type="content",
        metadata={},
    )


def test_metrics_publisher_ticks_without_viewers():
    clock = ClockAdapter()
    pace = PaceController(clock=clock, target_hz=10.0, sleep_fn=None)
    manager = ChannelManager("chan-1", clock=clock, schedule_service=StubScheduleService(), program_director=StubProgramDirector())
    publisher = MetricsPublisher(clock, pace, manager, sample_hz=2.0, aggregation_window=2.0)
    manager.attach_metrics_publisher(publisher)
    publisher.start()

    for _ in range(4):
        clock.advance(0.25)
        pace.run_once()

    sample = manager.get_channel_metrics()
    assert sample is not None
    assert sample.viewer_count == 0
    assert sample.channel_state == "idle"
    assert clock.now() - sample.station_time <= 0.5
    assert publisher.is_sample_fresh() is True

    clock.advance(5.0)
    assert publisher.is_sample_fresh() is False
    publisher.stop()


def test_metrics_publisher_tracks_active_segment():
    clock = ClockAdapter()
    pace = PaceController(clock=clock, target_hz=10.0, sleep_fn=None)
    manager = ChannelManager("chan-2", clock=clock, schedule_service=StubScheduleService(), program_director=StubProgramDirector())
    publisher = MetricsPublisher(clock, pace, manager, sample_hz=4.0, aggregation_window=1.0)
    manager.attach_metrics_publisher(publisher)

    segment_a = _make_segment(0.0, 5.0)
    segment_b = _make_segment(5.0, 5.0)
    producer = FFmpegSegmentProducer("chan-2", {"output_url": "pipe:1"})
    producer.start([segment_a, segment_b], segment_a.start_time + timedelta(seconds=1))
    manager.active_producer = producer
    manager.viewer_sessions["viewer-1"] = {"joined": clock.get_current_time()}
    publisher.start()

    for _ in range(5):
        clock.advance(0.1)
        pace.run_once()

    sample = manager.get_channel_metrics()
    assert sample is not None
    assert sample.viewer_count == 1
    assert sample.channel_state == "active"
    assert sample.segment_id == segment_a.asset_id
    assert sample.segment_position > 0.0
    assert sample.dropped_frames in (None, 0)
    assert sample.queued_frames in (None, 0)

    producer.on_paced_tick(clock.now(), 5.0)
    clock.advance(0.2)
    pace.run_once()
    sample = manager.get_channel_metrics()
    assert sample.segment_id == segment_b.asset_id or sample.segment_id is None
    publisher.stop()


def test_metrics_publisher_real_time_cadence():
    clock = RealTimeMasterClock()
    pace = PaceController(clock=clock, target_hz=5.0)

    class SimpleManager:
        def __init__(self) -> None:
            self.viewer_count = 0
            self.state = "idle"

        def populate_metrics_sample(self, sample: ChannelMetricsSample) -> None:
            sample.channel_state = self.state
            sample.viewer_count = self.viewer_count
            sample.producer_state = "stopped"
            sample.segment_id = None
            sample.segment_position = 0.0
            sample.dropped_frames = None
            sample.queued_frames = None

        def attach_metrics_publisher(self, publisher: MetricsPublisher) -> None:
            self.publisher = publisher

        def get_channel_metrics(self) -> ChannelMetricsSample:
            return self.publisher.get_latest_sample()

    manager = SimpleManager()
    publisher = MetricsPublisher(clock, pace, manager, sample_hz=2.0, aggregation_window=2.0)
    manager.attach_metrics_publisher(publisher)
    publisher.start()

    for _ in range(4):
        pace.run_once()
        time.sleep(0.25)

    sample = manager.get_channel_metrics()
    assert sample.station_time > 0.0
    assert publisher.is_sample_fresh() is True
    publisher.stop()

