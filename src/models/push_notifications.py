

from datetime import datetime
from enum import StrEnum
import uuid

from sqlalchemy import UUID, Boolean, DateTime, Enum, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB, UUID

from src.database import Base


class DevicePlatform(StrEnum):
    android = "android"
    windows = "windows"


class PushDeliveryState(StrEnum):
    active = "active"
    disabled = "disabled"
    inactive = "inactive"
    invalid_token = "invalid_token"
    unknown = "unknown"
    
device_platform = Enum(
    DevicePlatform,
    name="device_platform",
    create_type=False,   
)
push_delivery_state = Enum(
    PushDeliveryState,
    name="push_delivery_state",
    create_type=False,   
)

class Device(Base):
    __tablename__ = "devices"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    platform: Mapped[DevicePlatform] = mapped_column(
        device_platform,
        nullable=False,
    )
    push_token: Mapped[str] = mapped_column(String, nullable=False)
    device_id: Mapped[str] = mapped_column(String, nullable=False)
    
    push_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_seen_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_push_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    last_push_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_push_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    disabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    user = relationship("User", back_populates="devices")
    
    __table_args__ = (
        UniqueConstraint("user_id", "device_id", name="uq_devices_user_device"),
        Index("ix_devices_user_platform_active", "user_id", "platform", "is_active"),
        Index("ix_devices_user_push_enabled", "user_id", "push_enabled"),
    )
    def __repr__(self):
        return f"<Device(id={self.id}, user_id={self.user_id}, is_active={self.is_active})>"
class UserNotificationSettings(Base):
    __tablename__ = "user_notification_settings"

    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    push_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user = relationship("User", back_populates="notification_settings", lazy="raise")