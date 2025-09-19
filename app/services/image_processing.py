import logging
import os
import uuid
from pathlib import Path
from typing import Dict, List, Tuple

import aiofiles
from PIL import Image

from app.config import settings

logger = logging.getLogger(__name__)


class ImageProcessingService:
    def __init__(self) -> None:
        self.upload_dir = Path(settings.upload_dir)
        self.original_dir = self.upload_dir / "original"
        self.thumbnails_dir = self.upload_dir / "thumbnails"
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        self.original_dir.mkdir(parents=True, exist_ok=True)
        self.thumbnails_dir.mkdir(parents=True, exist_ok=True)

    async def save_original_image(self, file_content: bytes, filename: str) -> str:
        file_extension = Path(filename).suffix.lower()
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = self.original_dir / unique_filename
        
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(file_content)
        
        logger.info(f"Saved original image: {file_path}")
        return str(file_path)

    async def create_thumbnails(self, original_path: str) -> Dict[str, str]:
        original_file = Path(original_path)
        if not original_file.exists():
            raise FileNotFoundError(f"Original image not found: {original_path}")
        
        thumbnails = {}
        
        try:
            with Image.open(original_file) as img:
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                
                for width, height in settings.thumbnail_size_list:
                    thumbnail = img.copy()
                    thumbnail.thumbnail((width, height), Image.Resampling.LANCZOS)
                    
                    thumbnail_filename = f"{original_file.stem}_{width}x{height}.jpg"
                    thumbnail_path = self.thumbnails_dir / thumbnail_filename
                    
                    thumbnail.save(thumbnail_path, "JPEG", quality=85, optimize=True)
                    
                    thumbnails[f"{width}x{height}"] = str(thumbnail_path.relative_to(self.upload_dir))
                    
                    logger.info(f"Created thumbnail: {thumbnail_path}")
        
        except Exception as e:
            logger.error(f"Failed to create thumbnails for {original_path}: {e}")
            raise
        
        return thumbnails

    async def compress_image(self, image_path: str, quality: int = 85) -> str:
        file_path = Path(image_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        try:
            with Image.open(file_path) as img:
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                
                compressed_filename = f"{file_path.stem}_compressed.jpg"
                compressed_path = file_path.parent / compressed_filename
                
                img.save(compressed_path, "JPEG", quality=quality, optimize=True)
                
                logger.info(f"Compressed image: {compressed_path}")
                return str(compressed_path)
        
        except Exception as e:
            logger.error(f"Failed to compress image {image_path}: {e}")
            raise

    def get_file_size(self, file_path: str) -> int:
        return Path(file_path).stat().st_size

    def is_valid_image(self, file_path: str) -> bool:
        try:
            with Image.open(file_path) as img:
                img.verify()
            return True
        except Exception:
            return False

    def get_image_info(self, file_path: str) -> Dict[str, int]:
        try:
            with Image.open(file_path) as img:
                return {
                    "width": img.width,
                    "height": img.height,
                    "mode": img.mode,
                    "format": img.format
                }
        except Exception as e:
            logger.error(f"Failed to get image info for {file_path}: {e}")
            raise

    async def cleanup_file(self, file_path: str) -> None:
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.info(f"Cleaned up file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to cleanup file {file_path}: {e}")


image_processing_service = ImageProcessingService()
