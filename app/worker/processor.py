import json
import logging
from typing import Any, Dict
from uuid import UUID

import aio_pika
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import AsyncSessionLocal
from app.models.image import Image, ImageStatus
from app.services.image_processing import image_processing_service
from app.config import settings
from pathlib import Path

logger = logging.getLogger(__name__)


class ImageProcessor:
    async def process_message(self, message: aio_pika.IncomingMessage) -> None:
        async with message.process():
            try:
                message_data = json.loads(message.body.decode())
                logger.info(f"Processing message: {message_data}")
                
                image_id = UUID(message_data["image_id"])
                original_path = message_data["original_path"]
                original_filename = message_data["original_filename"]
                
                await self._process_image(image_id, original_path, original_filename)
                
                logger.info(f"Successfully processed image: {image_id}")
                
            except Exception as e:
                logger.error(f"Failed to process message: {e}")

    async def _process_image(
        self, 
        image_id: UUID, 
        original_path: str, 
        original_filename: str
    ) -> None:
        async with AsyncSessionLocal() as db:
            try:
                from sqlalchemy import text
                result = await db.execute(
                    text("SELECT * FROM images WHERE id = :image_id"),
                    {"image_id": image_id}
                )
                image_data = result.fetchone()
                
                if not image_data:
                    raise ValueError(f"Image not found: {image_id}")
                
                await db.execute(
                    text("UPDATE images SET status = :status WHERE id = :image_id"),
                    {"status": ImageStatus.PROCESSING.value, "image_id": image_id}
                )
                await db.commit()
                
                logger.info(f"Started processing image: {image_id}")
                
                thumbnails = await image_processing_service.create_thumbnails(original_path)

                compressed_abs_path = await image_processing_service.compress_image(original_path)

                try:
                    compressed_rel_path = str(Path(compressed_abs_path).relative_to(Path(settings.upload_dir)))
                except Exception:
                    compressed_rel_path = compressed_abs_path

                try:
                    await image_processing_service.cleanup_file(original_path)
                except Exception as cleanup_err:
                    logger.warning(f"Failed to cleanup original file {original_path}: {cleanup_err}")

                await db.execute(
                    text("""
                    UPDATE images 
                    SET 
                        status = :status,
                        thumbnails = :thumbnails,
                        original_path = :compressed_path,
                        original_url = :original_url
                    WHERE id = :image_id
                    """),
                    {
                        "status": ImageStatus.DONE.value,
                        "thumbnails": json.dumps(thumbnails),
                        "compressed_path": compressed_rel_path,
                        "original_url": f"/uploads/{compressed_rel_path}",
                        "image_id": image_id
                    }
                )
                await db.commit()
                
                logger.info(f"Completed processing image: {image_id}")
                
            except Exception as e:
                logger.error(f"Error processing image {image_id}: {e}")
                
                await db.execute(
                    text("""
                    UPDATE images 
                    SET 
                        status = :status,
                        error_message = :error_message
                    WHERE id = :image_id
                    """),
                    {
                        "status": ImageStatus.ERROR.value,
                        "error_message": str(e),
                        "image_id": image_id
                    }
                )
                await db.commit()
                
                raise
