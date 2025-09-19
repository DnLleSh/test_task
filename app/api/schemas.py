from typing import Dict, Optional
from uuid import UUID

from pydantic import BaseModel


class ImageUploadResponse(BaseModel):
    task_id: UUID
    status: str
    message: str


class ThumbnailResponse(BaseModel):
    url: str


class ImageResponse(BaseModel):
    id: UUID
    status: str
    original_url: Optional[str] = None
    thumbnails: Dict[str, str] = {}


class HealthResponse(BaseModel):
    status: str
    database: str
    rabbitmq: str
    service: str
