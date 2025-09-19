import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.image import Image, ImageStatus


class TestImageModel:
    async def test_create_image(self, test_db: AsyncSession) -> None:
        image = Image(
            original_filename="test.png",
            original_path="/path/to/test.png",
            status=ImageStatus.NEW
        )
        
        test_db.add(image)
        await test_db.commit()
        await test_db.refresh(image)
        
        assert image.id is not None
        assert image.original_filename == "test.png"
        assert image.original_path == "/path/to/test.png"
        assert image.status == ImageStatus.NEW
        assert image.created_at is not None
        assert image.updated_at is not None

    async def test_image_status_enum(self) -> None:
        assert ImageStatus.NEW == "NEW"
        assert ImageStatus.PROCESSING == "PROCESSING"
        assert ImageStatus.DONE == "DONE"
        assert ImageStatus.ERROR == "ERROR"

    async def test_image_to_dict(self, test_db: AsyncSession) -> None:
        image = Image(
            original_filename="test.png",
            original_path="/path/to/test.png",
            status=ImageStatus.NEW,
            original_url="/uploads/test.png",
            thumbnails={"100x100": "/uploads/thumb_100x100.jpg"}
        )
        
        test_db.add(image)
        await test_db.commit()
        await test_db.refresh(image)
        
        image_dict = image.to_dict()
        
        assert "id" in image_dict
        assert "status" in image_dict
        assert "original_url" in image_dict
        assert "thumbnails" in image_dict
        assert "created_at" in image_dict
        assert "updated_at" in image_dict
        assert image_dict["status"] == "NEW"
        assert image_dict["original_url"] == "/uploads/test.png"
        assert image_dict["thumbnails"]["100x100"] == "/uploads/thumb_100x100.jpg"

    async def test_image_repr(self, test_db: AsyncSession) -> None:
        image = Image(
            original_filename="test.png",
            original_path="/path/to/test.png",
            status=ImageStatus.NEW
        )
        
        test_db.add(image)
        await test_db.commit()
        await test_db.refresh(image)
        
        repr_str = repr(image)
        
        assert "Image" in repr_str
        assert str(image.id) in repr_str
        assert "NEW" in repr_str
        assert "test.png" in repr_str
