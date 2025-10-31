"""
Master Clock

Pattern: Authority

The MasterClock is the authoritative time source for the entire system.
It provides synchronized time across all components and handles timezone conversions.

Key Responsibilities:
- Provide authoritative time for the entire system
- Synchronize all components to common time source
- Handle time zone conversions for different channels
- Ensure time consistency across all operations
- Manage time-based events and triggers

Boundaries:
- MasterClock IS allowed to: Provide time, handle timezone conversions, synchronize components, manage time-based events
- MasterClock IS NOT allowed to: Make content decisions, handle scheduling, manage viewers, access external systems

Design Principles:
- Single source of truth for time
- High precision and accuracy
- Timezone awareness
- Event coordination
"""

import zoneinfo
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class TimePrecision(Enum):
    """Time precision levels"""

    SECOND = "second"
    MILLISECOND = "millisecond"
    MICROSECOND = "microsecond"


@dataclass
class TimeInfo:
    """Comprehensive time information"""

    utc_time: datetime
    local_time: datetime
    timezone: str
    precision: TimePrecision
    is_synchronized: bool


@dataclass
class TimeEvent:
    """Time-based event"""

    event_id: str
    trigger_time: datetime
    event_type: str
    payload: dict[str, Any]


class MasterClock:
    """
    Authority over system time and synchronization.

    Pattern: Authority

    This is the single source of truth for time in the entire system.
    All components must use MasterClock for time-based operations to ensure
    consistency and synchronization across the system.

    Key Responsibilities:
    - Provide authoritative time for the entire system
    - Synchronize all components to common time source
    - Handle time zone conversions for different channels
    - Ensure time consistency across all operations
    - Manage time-based events and triggers

    Boundaries:
    - IS allowed to: Provide time, handle timezone conversions, synchronize components, manage time-based events
    - IS NOT allowed to: Make content decisions, handle scheduling, manage viewers, access external systems
    """

    def __init__(self, precision: TimePrecision = TimePrecision.MILLISECOND):
        """
        Initialize the Master Clock.

        Args:
            precision: Time precision level for the system
        """
        self.precision = precision
        self.is_synchronized = True
        self.timezone_cache: dict[str, zoneinfo.ZoneInfo] = {}
        self.scheduled_events: dict[str, TimeEvent] = {}

    def now_utc(self) -> datetime:
        """
        Get current UTC time as the system's master reference.

        Returns:
            Current UTC time with specified precision
        """
        now = datetime.now(UTC)

        # Apply precision based on settings
        if self.precision == TimePrecision.SECOND:
            return now.replace(microsecond=0)
        elif self.precision == TimePrecision.MILLISECOND:
            return now.replace(microsecond=(now.microsecond // 1000) * 1000)
        else:  # MICROSECOND
            return now

    def now_local(self, channel_tz: str | None = None) -> datetime:
        """
        Return current time for the given channel timezone as an aware datetime.
        - If channel_tz is None, default to system/station timezone (we can keep a default in the class).
        - If the timezone string is invalid, fall back to UTC but mark that in a warning/flag.
        - Uses Python's zoneinfo for tz conversion.

        Args:
            channel_tz: Channel timezone (e.g., "America/New_York"). If None, uses system local time.

        Returns:
            Current local time in the specified timezone
        """
        utc_now = self.now_utc()

        if channel_tz is None:
            # Use system local timezone
            return utc_now.astimezone()

        try:
            # Get timezone info (with caching)
            tz_info = self._get_timezone_info(channel_tz)
            return utc_now.astimezone(tz_info)
        except Exception:
            # If timezone is invalid, fall back to UTC
            # TODO: Add warning/flag mechanism for invalid timezone
            return utc_now

    def seconds_since(self, dt: datetime) -> float:
        """
        Return max(0, now_utc() - dt_in_utc).total_seconds()
        - Accept both aware UTC datetimes and aware local datetimes.
        - If dt is naive, raise ValueError.
        - If dt is in the future, return 0.0 instead of a negative number.
        This gives ChannelManager a sane non-negative playout offset.

        Args:
            dt: Reference datetime

        Returns:
            Seconds elapsed since the reference datetime (clamped to 0.0 minimum)
        """
        if dt.tzinfo is None:
            raise ValueError("datetime must be timezone-aware")

        now = self.now_utc()

        # Convert dt to UTC if it's not already
        if dt.tzinfo != UTC:
            dt_utc = dt.astimezone(UTC)
        else:
            dt_utc = dt

        delta = now - dt_utc
        return max(0.0, delta.total_seconds())

    def to_channel_time(self, dt: datetime, channel_tz: str) -> datetime:
        """
        Convert an aware UTC datetime to an aware datetime in that channel's timezone.
        - If channel_tz is invalid, fall back to UTC.
        - If dt is naive, raise ValueError.

        Args:
            dt: UTC datetime to convert
            channel_tz: Target channel timezone

        Returns:
            Datetime in channel's timezone
        """
        if dt.tzinfo is None:
            raise ValueError("datetime must be timezone-aware")

        try:
            tz_info = self._get_timezone_info(channel_tz)
            return dt.astimezone(tz_info)
        except Exception:
            # If timezone is invalid, fall back to UTC
            return dt

    def get_current_time(self) -> datetime:
        """
        Get current system time with high precision.

        Returns:
            Current UTC time with specified precision
        """
        return self.now_utc()

    def get_time_info(self) -> TimeInfo:
        """
        Get comprehensive time information.

        Returns:
            TimeInfo with current time details
        """
        utc_time = self.now_utc()
        local_time = self.now_local()

        return TimeInfo(
            utc_time=utc_time,
            local_time=local_time,
            timezone=str(local_time.tzinfo),
            precision=self.precision,
            is_synchronized=self.is_synchronized,
        )

    def convert_timezone(self, dt: datetime, from_tz: str, to_tz: str) -> datetime:
        """
        Convert datetime between timezones.

        Args:
            dt: Datetime to convert
            from_tz: Source timezone
            to_tz: Target timezone

        Returns:
            Converted datetime
        """
        # Get timezone info
        from_tz_info = self._get_timezone_info(from_tz)
        to_tz_info = self._get_timezone_info(to_tz)

        # Ensure input datetime is timezone-aware
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=from_tz_info)
        elif dt.tzinfo != from_tz_info:
            dt = dt.astimezone(from_tz_info)

        # Convert to target timezone
        return dt.astimezone(to_tz_info)

    def get_channel_time(self, channel_id: str, channel_tz: str) -> datetime:
        """
        Get current time for a specific channel's timezone.

        Args:
            channel_id: Channel identifier (for logging/debugging)
            channel_tz: Channel's timezone

        Returns:
            Current time in channel's timezone
        """
        return self.now_local(channel_tz)

    def synchronize_time(self) -> bool:
        """
        Synchronize system time with external time source.

        Returns:
            True if synchronization successful
        """
        # In v0.1, we use system time as authoritative
        # Future versions may add NTP/PTP synchronization
        self.is_synchronized = True
        return True

    def schedule_event(
        self, event_id: str, trigger_time: datetime, event_type: str, payload: dict[str, Any]
    ) -> bool:
        """
        Schedule a time-based event.

        Args:
            event_id: Unique event identifier
            trigger_time: When to trigger the event
            event_type: Type of event
            payload: Event data

        Returns:
            True if event scheduled successfully
        """
        # Ensure trigger_time is timezone-aware
        if trigger_time.tzinfo is None:
            trigger_time = trigger_time.replace(tzinfo=UTC)

        event = TimeEvent(
            event_id=event_id, trigger_time=trigger_time, event_type=event_type, payload=payload
        )

        self.scheduled_events[event_id] = event
        return True

    def cancel_event(self, event_id: str) -> bool:
        """
        Cancel a scheduled time-based event.

        Args:
            event_id: Event identifier to cancel

        Returns:
            True if event cancelled successfully
        """
        if event_id in self.scheduled_events:
            del self.scheduled_events[event_id]
            return True
        return False

    def get_scheduled_events(self, start_time: datetime, end_time: datetime) -> list[TimeEvent]:
        """
        Get scheduled events in a time range.

        Args:
            start_time: Start of time range
            end_time: End of time range

        Returns:
            List of scheduled events in range
        """
        events = []
        for event in self.scheduled_events.values():
            if start_time <= event.trigger_time <= end_time:
                events.append(event)
        return events

    def trigger_scheduled_events(self) -> list[TimeEvent]:
        """
        Trigger all events that are due.

        Returns:
            List of triggered events
        """
        now = self.now_utc()
        triggered = []

        for event_id, event in list(self.scheduled_events.items()):
            if event.trigger_time <= now:
                triggered.append(event)
                del self.scheduled_events[event_id]

        return triggered

    def get_time_precision(self) -> TimePrecision:
        """
        Get current time precision level.

        Returns:
            Current time precision
        """
        return self.precision

    def set_time_precision(self, precision: TimePrecision) -> bool:
        """
        Set time precision level.

        Args:
            precision: New precision level

        Returns:
            True if precision set successfully
        """
        self.precision = precision
        return True

    def validate_time_consistency(self) -> bool:
        """
        Validate that all components are using consistent time.

        Returns:
            True if time is consistent across system
        """
        # In v0.1, we assume consistency since we use system time
        # Future versions may validate against external sources
        return True

    def get_timezone_info(self, timezone_name: str) -> dict[str, Any]:
        """
        Get information about a timezone.

        Args:
            timezone_name: Name of timezone

        Returns:
            Dictionary with timezone information
        """
        try:
            tz_info = self._get_timezone_info(timezone_name)
            return {
                "name": timezone_name,
                "offset": tz_info.utcoffset(datetime.now()),
                "dst": tz_info.dst(datetime.now()),
                "zone": str(tz_info),
            }
        except Exception:
            return {"name": timezone_name, "error": "Invalid timezone"}

    def handle_timezone_changes(self) -> list[str]:
        """
        Handle timezone changes and updates.

        Returns:
            List of timezone changes processed
        """
        # Clear cache to force refresh of timezone data
        self.timezone_cache.clear()
        return ["timezone_cache_cleared"]

    def _get_timezone_info(self, timezone_name: str) -> zoneinfo.ZoneInfo:
        """
        Get timezone info with caching.

        Args:
            timezone_name: Name of timezone

        Returns:
            ZoneInfo object for the timezone
        """
        if timezone_name not in self.timezone_cache:
            self.timezone_cache[timezone_name] = zoneinfo.ZoneInfo(timezone_name)

        return self.timezone_cache[timezone_name]
