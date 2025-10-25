"""
SQLAlchemy models for RetroVue infrastructure.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Channel(Base):
    """Channel model for TV channels."""
    __tablename__ = 'channels'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    timezone = Column(String(50), nullable=False)
    grid_size_minutes = Column(Integer, nullable=False)
    grid_offset_minutes = Column(Integer, nullable=False)
    rollover_minutes = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    schedule_days = relationship("ScheduleDay", back_populates="channel")
    playlog_events = relationship("PlaylogEvent", back_populates="channel")
    
    def __repr__(self):
        return f"<Channel(id={self.id}, name='{self.name}', timezone='{self.timezone}')>"


class Template(Base):
    """Template model for scheduling templates."""
    __tablename__ = 'templates'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    template_blocks = relationship("TemplateBlock", back_populates="template")
    schedule_days = relationship("ScheduleDay", back_populates="template")
    
    def __repr__(self):
        return f"<Template(id={self.id}, name='{self.name}')>"


class TemplateBlock(Base):
    """Template block model for time blocks within templates."""
    __tablename__ = 'template_blocks'
    
    id = Column(Integer, primary_key=True)
    template_id = Column(Integer, ForeignKey('templates.id'), nullable=False)
    start_time = Column(String(5), nullable=False)  # HH:MM format
    end_time = Column(String(5), nullable=False)    # HH:MM format
    rule_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    template = relationship("Template", back_populates="template_blocks")
    
    def __repr__(self):
        return f"<TemplateBlock(id={self.id}, template_id={self.template_id}, start='{self.start_time}', end='{self.end_time}')>"


class ScheduleDay(Base):
    """Schedule day model for assigning templates to channels on specific days."""
    __tablename__ = 'schedule_days'
    
    id = Column(Integer, primary_key=True)
    channel_id = Column(Integer, ForeignKey('channels.id'), nullable=False)
    template_id = Column(Integer, ForeignKey('templates.id'), nullable=False)
    schedule_date = Column(String(10), nullable=False)  # YYYY-MM-DD format
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    channel = relationship("Channel", back_populates="schedule_days")
    template = relationship("Template", back_populates="schedule_days")
    
    def __repr__(self):
        return f"<ScheduleDay(id={self.id}, channel_id={self.channel_id}, template_id={self.template_id}, date='{self.schedule_date}')>"


class Asset(Base):
    """Asset model for media content."""
    __tablename__ = 'assets'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    duration_ms = Column(Integer, nullable=False)
    tags = Column(String(1000), nullable=False)  # comma-separated tags
    file_path = Column(String(1000), nullable=False)
    canonical = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    playlog_events = relationship("PlaylogEvent", back_populates="asset")
    
    def __repr__(self):
        return f"<Asset(id={self.id}, title='{self.title}', canonical={self.canonical})>"


class PlaylogEvent(Base):
    """Playlog event model for tracking what was actually played."""
    __tablename__ = 'playlog_events'
    
    id = Column(Integer, primary_key=True)
    channel_id = Column(Integer, ForeignKey('channels.id'), nullable=False)
    asset_id = Column(Integer, ForeignKey('assets.id'), nullable=False)
    start_utc = Column(DateTime, nullable=False)
    end_utc = Column(DateTime, nullable=False)
    broadcast_day = Column(String(10), nullable=False)  # YYYY-MM-DD format
    
    # Relationships
    channel = relationship("Channel", back_populates="playlog_events")
    asset = relationship("Asset", back_populates="playlog_events")
    
    def __repr__(self):
        return f"<PlaylogEvent(id={self.id}, channel_id={self.channel_id}, asset_id={self.asset_id}, start='{self.start_utc}')>"


def create_all_tables(engine):
    """Create all tables in the database."""
    Base.metadata.create_all(engine)
