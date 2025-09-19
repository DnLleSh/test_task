import pytest
from pathlib import Path

from app.services.image_processing import ImageProcessingService


class TestImageProcessingService:

    @pytest.fixture
    def service(self, temp_upload_dir: Path) -> ImageProcessingService:
        service = ImageProcessingService()
        service.upload_dir = temp_upload_dir
        service.original_dir = temp_upload_dir / "original"
        service.thumbnails_dir = temp_upload_dir / "thumbnails"
        return service

    async def test_save_original_image(
        self, 
        service: ImageProcessingService, 
        sample_image_bytes: bytes
    ) -> None:
        filename = "test.png"
        file_path = await service.save_original_image(sample_image_bytes, filename)
        
        assert Path(file_path).exists()
        assert Path(file_path).suffix == ".png"
        assert Path(file_path).parent == service.original_dir

    async def test_create_thumbnails(
        self, 
        service: ImageProcessingService, 
        sample_image_bytes: bytes
    ) -> None:
        filename = "test.png"
        original_path = await service.save_original_image(sample_image_bytes, filename)
        
        thumbnails = await service.create_thumbnails(original_path)
        
        assert len(thumbnails) == 3  # 100x100, 300x300, 1200x1200
        assert "100x100" in thumbnails
        assert "300x300" in thumbnails
        assert "1200x1200" in thumbnails
        
        for size, path in thumbnails.items():
            full_path = service.upload_dir / path
            assert full_path.exists()

    async def test_compress_image(
        self, 
        service: ImageProcessingService, 
        sample_image_bytes: bytes
    ) -> None:
        filename = "test.png"
        original_path = await service.save_original_image(sample_image_bytes, filename)
        
        compressed_path = await service.compress_image(original_path)
        
        assert Path(compressed_path).exists()
        assert "compressed" in Path(compressed_path).name

    def test_get_file_size(
        self, 
        service: ImageProcessingService, 
        sample_image_bytes: bytes
    ) -> None:   
        test_file = service.original_dir / "test.png"
        test_file.write_bytes(sample_image_bytes)
        
        file_size = service.get_file_size(str(test_file))
        assert file_size == len(sample_image_bytes)

    def test_is_valid_image(
        self, 
        service: ImageProcessingService, 
        sample_image_bytes: bytes
    ) -> None:
        valid_file = service.original_dir / "valid.png"
        valid_file.write_bytes(sample_image_bytes)
        
        assert service.is_valid_image(str(valid_file))
        
        invalid_file = service.original_dir / "invalid.txt"
        invalid_file.write_text("not an image")
        
        assert not service.is_valid_image(str(invalid_file))

    def test_get_image_info(
        self, 
        service: ImageProcessingService, 
        sample_image_bytes: bytes
    ) -> None:
        test_file = service.original_dir / "test.png"
        test_file.write_bytes(sample_image_bytes)
        
        info = service.get_image_info(str(test_file))
        
        assert "width" in info
        assert "height" in info
        assert "mode" in info
        assert "format" in info

    async def test_cleanup_file(
        self, 
        service: ImageProcessingService, 
        sample_image_bytes: bytes
    ) -> None:
        test_file = service.original_dir / "cleanup_test.png"
        test_file.write_bytes(sample_image_bytes)
        
        assert test_file.exists()
        
        await service.cleanup_file(str(test_file))
        
        assert not test_file.exists()
