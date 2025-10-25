"""
SQLAlchemy models for RetroVue broadcast scheduling domain.
"""
import sqlalchemy as sa
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from retrovue.infra.db import Base


class BroadcastChannel(Base):
    """Broadcast channel model for scheduling."""
    __tablename__ = "broadcast_channel"
    
    id = sa.Column(sa.Integer, primary_key=True)
    uuid = sa.Column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False, unique=True)
    name = sa.Column(sa.Text, nullable=False, unique=True)
    timezone = sa.Column(sa.Text, nullable=False)  # IANA tz string
    grid_size_minutes = sa.Column(sa.Integer, nullable=False)
    grid_offset_minutes = sa.Column(sa.Integer, nullable=False)
    rollover_minutes = sa.Column(sa.Integer, nullable=False)  # minutes after local midnight, e.g. 360 for 06:00
    is_active = sa.Column(sa.Boolean, nullable=False, server_default=sa.text("true"))
    created_at = sa.Column(sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()"))
    
    def __repr__(self):
        return f"<BroadcastChannel(id={self.id}, name='{self.name}', timezone='{self.timezone}')>"


class BroadcastTemplate(Base):
    """Broadcast template model for scheduling."""
    __tablename__ = "broadcast_template"
    
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.Text, nullable=False, unique=True)
    description = sa.Column(sa.Text, nullable=True)
    is_active = sa.Column(sa.Boolean, nullable=False, server_default=sa.text("true"))
    created_at = sa.Column(sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()"))

    blocks = sa.orm.relationship("BroadcastTemplateBlock", back_populates="template", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<BroadcastTemplate(id={self.id}, name='{self.name}')>"


class BroadcastTemplateBlock(Base):
    """Broadcast template block model for time blocks within templates."""
    __tablename__ = "broadcast_template_block"
    
    id = sa.Column(sa.Integer, primary_key=True)
    template_id = sa.Column(sa.Integer, sa.ForeignKey("broadcast_template.id", ondelete="CASCADE"), nullable=False, index=True)
    start_time = sa.Column(sa.Text, nullable=False)  # "HH:MM" local wallclock
    end_time = sa.Column(sa.Text, nullable=False)    # "HH:MM"
    rule_json = sa.Column(sa.Text, nullable=False)   # e.g. {"tags":["sitcom"], "episode_policy":"syndication"}
    created_at = sa.Column(sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()"))

    template = sa.orm.relationship("BroadcastTemplate", back_populates="blocks")
    
    def __repr__(self):
        return f"<BroadcastTemplateBlock(id={self.id}, template_id={self.template_id}, start='{self.start_time}', end='{self.end_time}')>"


class BroadcastScheduleDay(Base):
    """Broadcast schedule day model for assigning templates to channels on specific days."""
    __tablename__ = "broadcast_schedule_day"
    
    id = sa.Column(sa.Integer, primary_key=True)
    channel_id = sa.Column(sa.Integer, sa.ForeignKey("broadcast_channel.id", ondelete="CASCADE"), nullable=False, index=True)
    template_id = sa.Column(sa.Integer, sa.ForeignKey("broadcast_template.id", ondelete="RESTRICT"), nullable=False)
    schedule_date = sa.Column(sa.Text, nullable=False)  # "YYYY-MM-DD" broadcast-day label, 06:00→06:00 policy
    created_at = sa.Column(sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()"))

    __table_args__ = (
        sa.UniqueConstraint("channel_id", "schedule_date", name="uq_broadcast_schedule_day_channel_date"),
    )

    channel = sa.orm.relationship("BroadcastChannel")
    template = sa.orm.relationship("BroadcastTemplate")
    
    def __repr__(self):
        return f"<BroadcastScheduleDay(id={self.id}, channel_id={self.channel_id}, template_id={self.template_id}, date='{self.schedule_date}')>"


class CatalogAsset(Base):
    """Broadcast-approved catalog entry (airable). NOT the ingest library asset."""
    __tablename__ = "catalog_asset"
    
    id = sa.Column(sa.Integer, primary_key=True)
    uuid = sa.Column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False, unique=True)
    title = sa.Column(sa.Text, nullable=False)
    duration_ms = sa.Column(sa.Integer, nullable=False)
    tags = sa.Column(sa.Text, nullable=True)  # comma-separated tags like "sitcom,retro"
    file_path = sa.Column(sa.Text, nullable=False)
    canonical = sa.Column(sa.Boolean, nullable=False, server_default=sa.text("false"))
    source_ingest_asset_id = sa.Column(sa.Integer, sa.ForeignKey("assets.id", ondelete="SET NULL"), nullable=True)  # Reference to Library Domain asset.id for traceability
    created_at = sa.Column(sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()"))

    __table_args__ = (
        sa.Index("ix_catalog_asset_canonical", "canonical"),
        sa.Index("ix_catalog_asset_tags", "tags"),
        sa.Index("ix_catalog_asset_source_ingest_asset_id", "source_ingest_asset_id"),
    )
    
    def __repr__(self):
        return f"<CatalogAsset(id={self.id}, title='{self.title}', canonical={self.canonical})>"


class BroadcastPlaylogEvent(Base):
    """Broadcast playlog event model for tracking what was actually played."""
    __tablename__ = "broadcast_playlog_event"
    
    id = sa.Column(sa.Integer, primary_key=True)
    uuid = sa.Column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False, unique=True)
    channel_id = sa.Column(sa.Integer, sa.ForeignKey("broadcast_channel.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_id = sa.Column(sa.Integer, sa.ForeignKey("catalog_asset.id", ondelete="RESTRICT"), nullable=False)
    start_utc = sa.Column(sa.DateTime(timezone=True), nullable=False)
    end_utc = sa.Column(sa.DateTime(timezone=True), nullable=False)
    broadcast_day = sa.Column(sa.Text, nullable=False)  # "YYYY-MM-DD" broadcast day label
    created_at = sa.Column(sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()"))

    __table_args__ = (
        sa.Index("ix_broadcast_playlog_event_channel_start", "channel_id", "start_utc"),
        sa.Index("ix_broadcast_playlog_event_broadcast_day", "broadcast_day"),
    )

    channel = sa.orm.relationship("BroadcastChannel")
    asset = sa.orm.relationship("CatalogAsset")
    
    def __repr__(self):
        return f"<BroadcastPlaylogEvent(id={self.id}, channel_id={self.channel_id}, asset_id={self.asset_id}, start='{self.start_utc}')>"


