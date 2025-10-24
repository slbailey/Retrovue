"""
Producer Protocol (Capability Provider)

Pattern: Output Generator

The Producer is the component that actually emits audiovisual output for a channel.
Producers are swappable. ChannelManager chooses which Producer implementation to run for a channel.
All Producers must implement the same interface so ChannelManager can control them in a consistent way.

Key Responsibilities:
- Generate broadcast streams for assigned channel
- Support multiple output modes (normal, emergency, guide)
- Handle real-time encoding and streaming
- Ensure seamless transitions between content segments
- Provide stream URLs for viewer access

Boundaries:
- Producer IS allowed to: Generate output, handle encoding, manage streams, play provided content
- Producer IS NOT allowed to: Pick content, make content decisions, access Content Manager directly, make scheduling decisions
- Producer cannot talk to Content Manager or Schedule Manager directly. All instructions come from ChannelManager via the playout plan.

Design Principles:
- Pure output generation
- Mode-based operation
- Content-agnostic (plays what it's told to play)
- Real-time streaming and encoding
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class ProducerMode(Enum):
    """Producer operational modes"""
    NORMAL = "normal"
    EMERGENCY = "emergency"
    GUIDE = "guide"


class ProducerStatus(Enum):
    """Producer operational status"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class ProducerState:
    """Current state of a producer"""
    producer_id: str
    channel_id: str
    mode: ProducerMode
    status: ProducerStatus
    output_url: Optional[str]
    started_at: Optional[datetime]
    configuration: Dict[str, Any]


@dataclass
class ContentSegment:
    """Content segment to play"""
    asset_id: str
    start_time: datetime
    end_time: datetime
    segment_type: str  # e.g. "content", "commercial", "bumper", etc.
    metadata: Dict[str, Any]


class Producer(ABC):
    """
    Base class for output generators that create broadcast streams.

    Pattern: Output Generator

    This is the base class for all producers that generate broadcast output.
    It defines the interface for content playback and stream generation.

    Key Responsibilities:
    - Generate broadcast streams for assigned channel
    - Support multiple output modes (normal, emergency, guide)
    - Handle real-time encoding and streaming
    - Ensure seamless transitions between content segments
    - Provide stream URLs for viewer access

    Boundaries:
    - IS allowed to: Generate output, handle encoding, manage streams, play provided content
    - IS NOT allowed to: Pick content, make content decisions, access Content Manager directly, make scheduling decisions
    """

    def __init__(self, channel_id: str, mode: ProducerMode, configuration: Dict[str, Any]):
        """
        Initialize the Producer.

        Args:
            channel_id: Channel this producer serves
            mode: Producer operational mode
            configuration: Producer-specific settings
        """
        self.channel_id = channel_id
        self.mode = mode
        self.configuration = configuration
        self.status = ProducerStatus.STOPPED
        self.output_url = None
        self.started_at = None

    @abstractmethod
    def start(self, playout_plan: List[Dict[str, Any]], start_at_station_time: datetime) -> bool:
        """
        Begin output for this channel.

        Args:
            playout_plan: The resolved segment sequence that should air
            start_at_station_time: From MasterClock, allows us to join mid-program instead of always starting at frame 0

        Returns:
            True if producer started successfully
        """
        pass

    @abstractmethod
    def stop(self) -> bool:
        """
        Stop the producer and clean up resources.

        Returns:
            True if producer stopped successfully
        """
        pass

    @abstractmethod
    def play_content(self, content: ContentSegment) -> bool:
        """
        Play a content segment.

        Args:
            content: Content segment to play

        Returns:
            True if content started playing successfully
        """
        pass

    @abstractmethod
    def get_stream_endpoint(self) -> Optional[str]:
        """
        Return a handle / URL / socket description that viewers can attach to.

        Returns:
            Stream endpoint URL, or None if not available
        """
        pass

    @abstractmethod
    def health(self) -> str:
        """
        Report whether the Producer is running, degraded, or stopped.

        Returns:
            Health status: 'running', 'degraded', or 'stopped'
        """
        pass

    def get_state(self) -> ProducerState:
        """
        Get current state of the producer.

        Returns:
            ProducerState with current information
        """
        return ProducerState(
            producer_id=self.get_producer_id(),
            channel_id=self.channel_id,
            mode=self.mode,
            status=self.status,
            output_url=self.output_url,
            started_at=self.started_at,
            configuration=self.configuration,
        )

    @abstractmethod
    def get_producer_id(self) -> str:
        """
        Get unique identifier for this producer.

        Returns:
            Producer identifier
        """
        pass
