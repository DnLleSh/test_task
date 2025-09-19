import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    HealthResponse,
    ImageResponse,
    ImageUploadResponse,
)
from app.models.database import get_db
from app.models.image import Image, ImageStatus
from app.services.rabbitmq import rabbitmq_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/images", response_model=ImageUploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> ImageUploadResponse:
    """Upload image for processing."""
    logger.info(f"Received image upload: {file.filename}")
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    file_extension = file.filename.split(".")[-1].lower()
    if file_extension not in ["jpg", "jpeg", "png", "gif", "bmp", "webp"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: jpg, jpeg, png, gif, bmp, webp"
        )
    
    file_content = await file.read()
    if len(file_content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
    
    try:
        image = Image(
            original_filename=file.filename,
            original_path="",
            status=ImageStatus.NEW
        )
        db.add(image)
        await db.commit()
        await db.refresh(image)
        
        from app.services.image_processing import image_processing_service
        original_path = await image_processing_service.save_original_image(
            file_content, file.filename
        )
        
        image.original_path = original_path
        await db.commit()
        
        message = {
            "image_id": str(image.id),
            "original_path": original_path,
            "original_filename": file.filename
        }
        
        await rabbitmq_service.publish_message("image_processing", message)
        
        image.status = ImageStatus.PROCESSING
        await db.commit()
        
        logger.info(f"Image uploaded successfully: {image.id}")
        
        return ImageUploadResponse(
            task_id=image.id,
            status=image.status.value,
            message="Image uploaded and queued for processing"
        )
        
    except Exception as e:
        logger.error(f"Failed to upload image: {e}")
        if 'image' in locals():
            await db.delete(image)
            await db.commit()
        raise HTTPException(status_code=500, detail="Failed to upload image")


@router.get("/images/{image_id}", response_model=ImageResponse)
async def get_image(
    image_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ImageResponse:
    logger.info(f"Getting image details: {image_id}")
    
    from sqlalchemy import text
    result = await db.execute(
        text("SELECT * FROM images WHERE id = :image_id"),
        {"image_id": image_id}
    )
    image_data = result.fetchone()
    
    if not image_data:
        raise HTTPException(status_code=404, detail="Image not found")
    
    image_dict = dict(image_data._mapping)
    
    original_url = None
    if image_dict.get("original_path"):
        original_url = f"/uploads/{image_dict['original_path']}"
    
    thumbnails = {}
    if image_dict.get("thumbnails"):
        thumbnails = image_dict["thumbnails"]
        thumbnails = {
            size: f"/uploads/{path}" 
            for size, path in thumbnails.items()
        }
    
    return ImageResponse(
        id=image_dict["id"],
        status=image_dict["status"],
        original_url=original_url,
        thumbnails=thumbnails
    )


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    logger.info("Health check requested")
    
    database_status = "healthy"
    try:
        from app.models.database import engine
        from sqlalchemy import text
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        database_status = "unhealthy"
    
    rabbitmq_status = "healthy"
    try:
        if not rabbitmq_service.connection or rabbitmq_service.connection.is_closed:
            rabbitmq_status = "unhealthy"
    except Exception as e:
        logger.error(f"RabbitMQ health check failed: {e}")
        rabbitmq_status = "unhealthy"
    
    service_status = "healthy" if database_status == "healthy" and rabbitmq_status == "healthy" else "unhealthy"
    
    return HealthResponse(
        status=service_status,
        database=database_status,
        rabbitmq=rabbitmq_status,
        service="image-processing"
    )
