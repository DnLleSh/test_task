import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestImageUpload:
    async def test_upload_valid_image(
        self, 
        test_client: AsyncClient, 
        sample_image_bytes: bytes
    ) -> None:
        files = {"file": ("test.png", sample_image_bytes, "image/png")}
        
        response = await test_client.post("/api/v1/images", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "PROCESSING"
        assert "message" in data

    async def test_upload_invalid_file_type(
        self, 
        test_client: AsyncClient
    ) -> None:
        files = {"file": ("test.txt", b"not an image", "text/plain")}
        
        response = await test_client.post("/api/v1/images", files=files)
        
        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]

    async def test_upload_no_filename(self, test_client: AsyncClient) -> None:
        files = {"file": (None, b"some content", "image/png")}
        
        response = await test_client.post("/api/v1/images", files=files)
        
        assert response.status_code == 400
        assert "No filename provided" in response.json()["detail"]

    async def test_upload_large_file(self, test_client: AsyncClient) -> None:
        large_content = b"x" * (11 * 1024 * 1024)
        files = {"file": ("large.png", large_content, "image/png")}
        
        response = await test_client.post("/api/v1/images", files=files)
        
        assert response.status_code == 400
        assert "File size exceeds" in response.json()["detail"]


class TestImageDetails:
    async def test_get_nonexistent_image(
        self, 
        test_client: AsyncClient
    ) -> None:
        response = await test_client.get("/api/v1/images/00000000-0000-0000-0000-000000000000")
        
        assert response.status_code == 404
        assert "Image not found" in response.json()["detail"]

    async def test_get_image_details(
        self, 
        test_client: AsyncClient,
        test_db: AsyncSession,
        sample_image_bytes: bytes
    ) -> None:
        # First upload an image
        files = {"file": ("test.png", sample_image_bytes, "image/png")}
        upload_response = await test_client.post("/api/v1/images", files=files)
        task_id = upload_response.json()["task_id"]
        
        response = await test_client.get(f"/api/v1/images/{task_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id
        assert "status" in data
        assert "thumbnails" in data


class TestHealthCheck:
    async def test_health_check(self, test_client: AsyncClient) -> None:
        response = await test_client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "rabbitmq" in data
        assert "service" in data
        assert data["service"] == "image-processing"


class TestRootEndpoint:
    async def test_root_endpoint(self, test_client: AsyncClient) -> None:
        response = await test_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "redoc" in data
