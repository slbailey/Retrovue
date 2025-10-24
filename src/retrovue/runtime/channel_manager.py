"""
Channel Manager

Pattern: Per-Channel Orchestrator

The ChannelManager is RetroVue's per-channel runtime controller. It's responsible for managing
live playback on ONE channel at a time, ensuring that the correct content is playing at the
right time with the proper timing offset.

ChannelManager is subordinate to ProgramDirector and must obey global mode (normal / emergency / guide).
It never invents content, never fixes schedule gaps, and never talks to the ingest pipeline.

ChannelManager is where "the channel goes on the air" — it is the board operator for that channel.

Key Responsibilities:
- Ask ScheduleService (Schedule Manager) what should be airing "right now" for this channel
- Use MasterClock to compute the correct offset into the current program
- Resolve the playout plan and hand it to a Producer
- Ensure the correct Producer is active for the current mode
- Track active viewer sessions and apply the fanout model
- Report health/status up to ProgramDirector

Boundaries:
- ChannelManager IS allowed to: Read schedules, manage producers, handle viewers, apply channel policies
- ChannelManager IS NOT allowed to: Write schedules, pick content, make scheduling decisions, bypass Schedule Manager
- ChannelManager is not allowed to ask Content Manager or Schedule Manager for 'new content' on demand
- If something is missing from the schedule, that's considered a scheduling failure upstream, not permission to improvise
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List, Protocol

# Producer Protocol / types from runtime.producer package.
# Note: ProducerMode / ProducerStatus are imported even if not all are used yet
# because ChannelManager needs to reason about mode and status coherently.
from retrovue.runtime.producer import (
    Producer,
    ProducerState,
    ProducerStatus,
    ProducerMode,
)

# MasterClock is the single source of authoritative "now"
from .clock import MasterClock


class ScheduleService(Protocol):
    """Read-only schedule accessor."""

    def get_playout_plan_now(
        self,
        channel_id: str,
        at_station_time: datetime,
    ) -> List[Dict[str, Any]]:
        """
        Return the resolved segment sequence that should be airing 'right now' on this channel.

        Must include correct timing offsets so we can join mid-program instead of restarting at frame 0.
        Must NOT mutate schedule state.
        """
        ...


class ProgramDirector(Protocol):
    """Global policy/mode provider."""

    def get_channel_mode(self, channel_id: str) -> str:
        """
        Return the required mode for this channel: "normal", "emergency", "guide", etc.
        ChannelManager is not allowed to make this decision on its own.
        """
        ...


@dataclass
class ChannelRuntimeState:
    """
    Runtime state that ChannelManager is responsible for tracking and reporting up to ProgramDirector.
    ProgramDirector and any operator UI should treat ChannelManager as the source of truth for on-air status.
    """

    channel_id: str
    current_mode: str  # "normal" | "emergency" | "guide"
    viewer_count: int
    producer_status: str  # mirrors ProducerStatus as string
    producer_started_at: Optional[datetime]
    stream_endpoint: Optional[str]  # what viewers attach to
    last_health: Optional[str]  # "running", "degraded", "stopped", etc.

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert runtime state to dictionary for reporting/telemetry.
        """
        return {
            "channel_id": self.channel_id,
            "current_mode": self.current_mode,
            "viewer_count": self.viewer_count,
            "producer_status": self.producer_status,
            "producer_started_at": (
                self.producer_started_at.isoformat()
                if self.producer_started_at
                else None
            ),
            "stream_endpoint": self.stream_endpoint,
            "last_health": self.last_health,
        }


class ChannelManager:
    """
    Per-channel runtime controller that manages individual channel operations.

    Pattern: Per-Channel Orchestrator

    ChannelManager is the per-channel board operator. It runs the fanout model. It is the only
    component that actually starts/stops Producers. It obeys ProgramDirector's global mode.
    It consumes the schedule but does not write it. It never chooses content; it only plays
    what it is told.

    ChannelManager is how a RetroVue channel actually goes on-air.

    Responsibilities (enforced here):
    - Ask ScheduleService what should be airing 'right now', using MasterClock for authoritative time
    - Start/stop the Producer based on viewer fanout rules (first viewer starts, last viewer stops)
    - Swap Producers when ProgramDirector changes global mode (normal/emergency/guide)
    - Expose the Producer's stream endpoint so viewers can attach
    - Surface health/status upward to ProgramDirector

    Hard boundaries:
    - ChannelManager does NOT pick content
    - ChannelManager does NOT modify schedule
    - ChannelManager does NOT call ffmpeg or manage OS processes directly
    - ChannelManager does NOT "fill gaps" if schedule is missing
    """

    def __init__(
        self,
        channel_id: str,
        clock: MasterClock,
        schedule_service: ScheduleService,
        program_director: ProgramDirector,
    ):
        """
        Initialize the ChannelManager for a specific channel.

        Args:
            channel_id: Channel this manager controls
            clock: MasterClock for authoritative time
            schedule_service: ScheduleService for read-only access to current playout plan
            program_director: ProgramDirector for global policy/mode
        """
        self.channel_id = channel_id
        self.clock = clock
        self.schedule_service = schedule_service
        self.program_director = program_director

        # Track active tuning sessions (viewer_id -> session data)
        # NOTE: We intentionally store dicts for now instead of a ViewerSession class,
        # but this can later become a @dataclass that matches the DB model.
        self.viewer_sessions: Dict[str, Dict[str, Any]] = {}

        # At most one active producer for this channel.
        self.active_producer: Optional[Producer] = None

        # Runtime snapshot for ProgramDirector / dashboards / analytics.
        self.runtime_state = ChannelRuntimeState(
            channel_id=channel_id,
            current_mode="normal",
            viewer_count=0,
            producer_status="stopped",
            producer_started_at=None,
            stream_endpoint=None,
            last_health=None,
        )

    def _get_current_mode(self) -> str:
        """
        Ask ProgramDirector which mode this channel must be in:
        "normal", "emergency", "guide", etc.

        ChannelManager does NOT decide policy. It just obeys.
        """
        mode = self.program_director.get_channel_mode(self.channel_id)
        # Keep runtime_state.current_mode in sync so ProgramDirector can read it back cheaply.
        self.runtime_state.current_mode = mode
        return mode

    def _get_playout_plan(self) -> List[Dict[str, Any]]:
        """
        Ask ScheduleService what should be airing right now for this channel.

        Rules:
        - Must call MasterClock for authoritative 'now' (station time), not system time.
        - Must NOT mutate schedules or request "new" content.
        - Must get the correct offset into the currently airing segment so we can join mid-program.

        Returns:
            List of segment dicts for current playout plan.

        Raises:
            NoScheduleDataError if ScheduleService has nothing for "right now".
        """
        station_time = self.clock.get_current_time()
        playout_plan = self.schedule_service.get_playout_plan_now(
            self.channel_id, station_time
        )

        if not playout_plan:
            raise NoScheduleDataError(
                f"No schedule data for channel {self.channel_id} at {station_time}"
            )

        return playout_plan

    def viewer_join(self, session_id: str, session_info: Dict[str, Any]) -> None:
        """
        Called when a viewer starts watching this channel.

        Behavior:
        - Track/refresh the ViewerSession in memory.
        - Update viewer_count.
        - If this is the first active viewer (0 -> 1), ensure the Producer is running.
        - Refresh runtime_state.stream_endpoint so we can hand a URL/handle back.

        Viewers never talk to Producers directly; they attach via the stream endpoint
        exposed by ChannelManager.
        """
        now = self.clock.get_current_time()

        if session_id in self.viewer_sessions:
            # Refresh last activity timestamp.
            self.viewer_sessions[session_id]["last_activity"] = now
        else:
            # Create a new session record.
            self.viewer_sessions[session_id] = {
                "session_id": session_id,
                "channel_id": self.channel_id,
                "started_at": now,
                "last_activity": now,
                "client_info": session_info,
            }

        old_count = self.runtime_state.viewer_count
        self.runtime_state.viewer_count = len(self.viewer_sessions)

        # Fanout rule: first viewer starts Producer.
        if old_count == 0 and self.runtime_state.viewer_count == 1:
            self._ensure_producer_running()

        # If we have an active producer, surface its endpoint for new viewers.
        if self.active_producer:
            self.runtime_state.stream_endpoint = (
                self.active_producer.get_stream_endpoint()
            )

    def viewer_leave(self, session_id: str) -> None:
        """
        Called when a viewer stops watching.

        Behavior:
        - Remove that ViewerSession.
        - Update viewer_count.
        - If viewer_count just dropped to 0, stop the Producer.
        """
        if session_id in self.viewer_sessions:
            del self.viewer_sessions[session_id]

        old_count = self.runtime_state.viewer_count
        self.runtime_state.viewer_count = len(self.viewer_sessions)

        # Fanout rule: last viewer stops Producer.
        if old_count == 1 and self.runtime_state.viewer_count == 0:
            self._stop_producer_if_idle()

    def _ensure_producer_running(self) -> None:
        """
        Enforce "channel goes on-air."

        Steps:
        1. Ask ProgramDirector what mode this channel must run in.
        2. If we already have a Producer in that mode and it's healthy -> done.
        3. Otherwise:
           - stop the old Producer (if any)
           - construct the correct Producer for that mode (NormalProducer / EmergencyProducer / GuideProducer)
           - ask ScheduleService for current playout plan
           - call producer.start(plan, station_time)
           - update runtime_state with status, started_at, endpoint

        IMPORTANT:
        - ChannelManager does not call ffmpeg directly.
        - ChannelManager does not pick content.
        - ChannelManager only ever runs EmergencyProducer if ProgramDirector says mode=emergency.
        """

        required_mode = self._get_current_mode()

        # If there's an active producer and it's both:
        # - in the correct mode,
        # - and healthy ("running"),
        # we don't need to touch anything.
        if (
            self.active_producer
            and self.active_producer.mode.value == required_mode
            and self.active_producer.health() == "running"
        ):
            return

        # Otherwise we're going to need to (re)start.
        # First shut down whatever was running.
        if self.active_producer:
            self.active_producer.stop()
            self.active_producer = None

        # TODO: ProducerFactory selection based on required_mode.
        # This factory will encapsulate which Producer subclass to instantiate
        # (NormalProducer, EmergencyProducer, GuideProducer, etc.)
        # and with what configuration.
        producer = self._build_producer_for_mode(required_mode)
        if producer is None:
            # We could not build a producer for this mode.
            self.runtime_state.producer_status = "error"
            raise ProducerStartupError(
                f"Channel {self.channel_id}: cannot create Producer for mode '{required_mode}'"
            )

        # We now consider this producer "active" for this channel.
        self.active_producer = producer

        # Get authoritative station time and playout plan.
        station_time = self.clock.get_current_time()
        playout_plan = self._get_playout_plan()

        # Ask the Producer to start.
        started_ok = self.active_producer.start(playout_plan, station_time)
        if not started_ok:
            self.runtime_state.producer_status = "error"
            self.active_producer = None
            raise ProducerStartupError(
                f"Channel {self.channel_id}: Producer failed to start in mode '{required_mode}'"
            )

        # Producer is up. Record runtime state.
        self.runtime_state.producer_status = "running"
        self.runtime_state.producer_started_at = station_time
        self.runtime_state.stream_endpoint = (
            self.active_producer.get_stream_endpoint()
        )

    def _stop_producer_if_idle(self) -> None:
        """
        Stop the Producer if there are no active viewers.

        If viewer_count == 0:
        - stop() the Producer
        - clear active_producer
        - update runtime_state to reflect "stopped"

        If viewer_count > 0, do nothing.
        """
        if self.runtime_state.viewer_count == 0:
            if self.active_producer:
                self.active_producer.stop()
                self.active_producer = None

            self.runtime_state.producer_status = "stopped"
            self.runtime_state.stream_endpoint = None
            # Do NOT clear current_mode here; ProgramDirector still "owns" desired mode.

    def check_health(self) -> None:
        """
        Poll Producer health and update runtime_state.

        Rules:
        - If there's no active Producer, status is "stopped".
        - If there is a Producer:
          - Call health() -> "running", "degraded", "stopped", etc.
          - Call get_state() for richer info.
        - If degraded/error:
          - We DO NOT immediately panic-restart here.
          - Recovery policy is defined by ProgramDirector (e.g. switch to emergency).
            ChannelManager will execute that policy, not invent its own fallback.
        """
        if self.active_producer is None:
            self.runtime_state.producer_status = "stopped"
            self.runtime_state.last_health = "stopped"
            return

        health_status = self.active_producer.health()
        producer_state: ProducerState = self.active_producer.get_state()

        # Update runtime snapshot.
        self.runtime_state.last_health = health_status
        self.runtime_state.producer_status = producer_state.status.value
        self.runtime_state.stream_endpoint = producer_state.output_url
        self.runtime_state.producer_started_at = producer_state.started_at

        # TODO (policy hook):
        # If health_status == "degraded" or "error":
        # - Ask ProgramDirector how to respond (stay in normal, restart normal,
        #   escalate to emergency, etc.)
        # - Then either restart or swap via _ensure_producer_running()
        #   after ProgramDirector updates channel mode.

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_producer_for_mode(self, mode: str) -> Optional[Producer]:
        """
        Factory hook: build the correct Producer implementation for the given mode.

        This method is intentionally a stub here to avoid importing specific producer
        implementations (NormalProducer, EmergencyProducer, GuideProducer) and
        accidentally binding ChannelManager to ffmpeg details.

        Eventually this will likely call into a ProducerFactory that knows how to
        construct each Producer subclass with appropriate configuration.

        ChannelManager MUST NOT reach into Producer internals or manage ffmpeg directly.
        """
        # TODO: Implement ProducerFactory / dependency injection.
        # Something like:
        #   return self.producer_factory.create(mode=mode, channel_id=self.channel_id)
        #
        # For now we return None to force ProducerStartupError in _ensure_producer_running().
        _ = mode  # avoid unused var lint
        return None


# ----------------------------------------------------------------------
# Custom exceptions for failure states
# ----------------------------------------------------------------------

class ChannelManagerError(Exception):
    """Base exception for ChannelManager errors."""
    pass


class ProducerStartupError(ChannelManagerError):
    """Raised when a Producer cannot be constructed or fails to start."""
    pass


class NoScheduleDataError(ChannelManagerError):
    """
    Raised if ScheduleService returns nothing for "right now".

    This is considered an upstream scheduling failure, NOT permission for
    ChannelManager to improvise content.
    """
    pass


class ChannelFailedError(ChannelManagerError):
    """
    Raised if ChannelManager cannot get any Producer on-air for this channel.

    This encodes the invariant that a channel is either on-air or failed:
    we do not allow a 'partially started' channel.
    """
    pass
