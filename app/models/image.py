import enum
from datetime import datetime
from typing import Dict, Optional
from uuid import uuid4

from sqlalchemy import Column, DateTime, Enum, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from .database import Base


class ImageStatus(str, enum.Enum):
    NEW = "NEW"
    PROCESSING = "PROCESSING"
    DONE = "DONE"
    ERROR = "ERROR"


class Image(Base):
    __tablename__ = "images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    status = Column(Enum(ImageStatus), default=ImageStatus.NEW, nullable=False)
    original_filename = Column(String(255), nullable=False)
    original_path = Column(String(500), nullable=False)
    original_url = Column(String(500), nullable=True)
    thumbnails = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Image(id={self.id}, status={self.status}, filename={self.original_filename})>"

    def to_dict(self) -> Dict:
        return {
            "id": str(self.id),
            "status": self.status.value,
            "original_url": self.original_url,
            "thumbnails": self.thumbnails or {},
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
