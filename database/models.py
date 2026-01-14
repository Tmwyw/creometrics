"""Database models for Creo Bot."""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, BigInteger, String, Boolean, DateTime,
    Text, JSON, Float, ForeignKey, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()


class User(Base):
    """User model."""

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    is_subscribed = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    is_blocked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)

    # Relationships
    actions = relationship("ActionLog", back_populates="user")

    def __repr__(self):
        return f"<User {self.telegram_id} ({self.username})>"


class ActionType(enum.Enum):
    """Action types enum."""

    UNIQUE_PHOTO = "unique_photo"
    UNIQUE_VIDEO = "unique_video"
    COMPRESS_VIDEO = "compress_video"
    MP3_TO_VOICE = "mp3_to_voice"
    VIDEO_TO_CIRCLE = "video_to_circle"
    TRANSCRIBE = "transcribe"
    DOWNLOAD_YOUTUBE = "download_youtube"
    DOWNLOAD_INSTAGRAM = "download_instagram"


class ActionStatus(enum.Enum):
    """Action status enum."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ActionLog(Base):
    """Action log model for tracking user actions."""

    __tablename__ = 'action_logs'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    action_type = Column(SQLEnum(ActionType), nullable=False, index=True)
    status = Column(SQLEnum(ActionStatus), default=ActionStatus.PENDING, index=True)

    # File information
    file_size = Column(BigInteger, nullable=True)  # in bytes
    file_duration = Column(Float, nullable=True)  # in seconds
    file_format = Column(String(50), nullable=True)

    # Processing parameters
    parameters = Column(JSON, nullable=True)  # Store copies count, preset_id, etc.
    preset_id = Column(Integer, ForeignKey('uniquification_presets.id'), nullable=True)

    # Results
    result_count = Column(Integer, nullable=True)  # Number of generated files
    processing_time = Column(Float, nullable=True)  # in seconds
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="actions")
    preset = relationship("UniquificationPreset", back_populates="actions")

    def __repr__(self):
        return f"<ActionLog {self.id} ({self.action_type.value}) - {self.status.value}>"


class MediaType(enum.Enum):
    """Media type enum."""

    PHOTO = "photo"
    VIDEO = "video"


class UniquificationPreset(Base):
    """Uniquification preset model."""

    __tablename__ = 'uniquification_presets'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    media_type = Column(SQLEnum(MediaType), nullable=False, index=True)
    is_active = Column(Boolean, default=True, index=True)
    is_default = Column(Boolean, default=False)

    # Configuration stored as JSON
    # Example for photo:
    # {
    #     "methods": [
    #         {"name": "noise", "enabled": true, "intensity": [5, 15]},
    #         {"name": "sparkles", "enabled": true, "count": [10, 30], "size": [2, 5]},
    #         {"name": "lens_flare", "enabled": true, "intensity": [0.3, 0.7]},
    #         {"name": "rotate", "enabled": true, "angle": [-3, 3]},
    #         {"name": "brightness", "enabled": true, "factor": [0.95, 1.05]},
    #         {"name": "contrast", "enabled": true, "factor": [0.95, 1.05]},
    #         {"name": "hue", "enabled": true, "shift": [-5, 5]}
    #     ]
    # }
    config = Column(JSON, nullable=False)

    # Metadata
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)

    # Relationships
    actions = relationship("ActionLog", back_populates="preset")

    def __repr__(self):
        return f"<UniquificationPreset {self.name} ({self.media_type.value})>"


class BroadcastMessage(Base):
    """Broadcast message model."""

    __tablename__ = 'broadcast_messages'

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    message_text = Column(Text, nullable=False)

    # Statistics
    total_users = Column(Integer, default=0)
    sent_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)

    # Status
    is_completed = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<BroadcastMessage {self.id} - {self.sent_count}/{self.total_users}>"


class BotSettings(Base):
    """Bot settings model for dynamic configuration."""

    __tablename__ = 'bot_settings'

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    value_type = Column(String(50), nullable=False)  # str, int, bool, json
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(Integer, ForeignKey('users.id'), nullable=True)

    def __repr__(self):
        return f"<BotSettings {self.key}={self.value}>"
