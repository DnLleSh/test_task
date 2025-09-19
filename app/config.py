import os
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/image_processing"

    rabbitmq_url: str = "amqp://rabbitmq:rabbitmq@localhost:5672/"

    upload_dir: str = "./uploads"

    log_level: str = "INFO"

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_title: str = "Image Processing Service"
    api_version: str = "0.1.0"

    thumbnail_sizes: str = "100x100,300x300,1200x1200"
    max_file_size: int = 10485760  # 10MB
    allowed_extensions: str = "jpg,jpeg,png,gif,bmp,webp"

    @property
    def thumbnail_size_list(self) -> List[tuple[int, int]]:
        sizes = []
        for size_str in self.thumbnail_sizes.split(","):
            width, height = map(int, size_str.strip().split("x"))
            sizes.append((width, height))
        return sizes

    @property
    def allowed_extensions_list(self) -> List[str]:
        return [ext.strip().lower() for ext in self.allowed_extensions.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
