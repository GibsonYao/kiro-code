"""Tests for admin AI model configuration management API."""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.deps import get_current_user, get_db
from app.main import app
from app.models.ai_config import AIModelConfig
from app.models.audit_log import AuditLog
from app.models.base import Base
from app.models.user import User
from app.utils.encryption import decrypt_value, encrypt_value, mask_api_key


# ─── Test Fixtures ─────────────────────────────────────────────────────────────

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DB_URL, echo=False)
TestSessionFactory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(autouse=True)
async def setup_db():
    """Create tables before each test and drop after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db():
    """Override DB dependency for tests."""
    async with TestSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def make_admin_user() -> User:
    """Create a mock admin user."""
    user = User()
    user.id = uuid.uuid4()
    user.nickname = "Admin"
    user.is_admin = True
    user.phone = "13800000001"
    return user


def make_regular_user() -> User:
    """Create a mock regular (non-admin) user."""
    user = User()
    user.id = uuid.uuid4()
    user.nickname = "Regular"
    user.is_admin = False
    user.phone = "13800000002"
    return user


@pytest.fixture
def admin_user():
    return make_admin_user()


@pytest.fixture
def regular_user():
    return make_regular_user()


@pytest.fixture
def admin_client(admin_user):
    """HTTP client with admin user dependency override."""
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: admin_user

    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://test")
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def regular_client(regular_user):
    """HTTP client with regular user dependency override."""
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: regular_user

    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://test")
    yield client
    app.dependency_overrides.clear()


# ─── Encryption Tests (Task 14.4) ─────────────────────────────────────────────


class TestEncryption:
    """Tests for AES-256-CBC encryption utilities."""

    def test_encrypt_decrypt_roundtrip(self):
        """Encrypting then decrypting should return the original value."""
        original = "sk-test-api-key-12345"
        encrypted = encrypt_value(original)
        decrypted = decrypt_value(encrypted)
        assert decrypted == original

    def test_encrypt_produces_different_output(self):
        """Each encryption should produce different ciphertext (due to random IV)."""
        original = "sk-test-api-key-12345"
        encrypted1 = encrypt_value(original)
        encrypted2 = encrypt_value(original)
        assert encrypted1 != encrypted2

    def test_encrypt_empty_string(self):
        """Encrypting empty string returns empty string."""
        assert encrypt_value("") == ""
        assert decrypt_value("") == ""

    def test_mask_api_key_normal(self):
        """Masking shows only last 4 characters."""
        assert mask_api_key("sk-1234567890abcdef") == "****cdef"

    def test_mask_api_key_short(self):
        """Masking short keys returns just stars."""
        assert mask_api_key("abc") == "****"
        assert mask_api_key("") == "****"

    def test_mask_api_key_exactly_4(self):
        """Masking a 4-char key returns just stars."""
        assert mask_api_key("abcd") == "****"


# ─── Admin Permission Tests (Task 14.6) ───────────────────────────────────────


class TestAdminPermission:
    """Tests for admin permission middleware."""

    @pytest.mark.asyncio
    async def test_non_admin_gets_403(self, regular_client):
        """Non-admin users should receive 403 Forbidden."""
        async with regular_client as client:
            response = await client.get("/api/v1/admin/ai-configs")
            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_gets_200(self, admin_client):
        """Admin users should be able to access admin endpoints."""
        async with admin_client as client:
            response = await client.get("/api/v1/admin/ai-configs")
            assert response.status_code == 200


# ─── CRUD Tests (Task 14.1) ───────────────────────────────────────────────────


class TestAIConfigCRUD:
    """Tests for AI config CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_ai_config(self, admin_client):
        """Creating a config should return 201 with masked API key."""
        async with admin_client as client:
            payload = {
                "config_key": "text_generation",
                "provider": "deepseek",
                "model_name": "deepseek-chat",
                "api_key": "sk-test-key-1234567890",
                "api_base_url": "https://api.deepseek.com/v1",
                "parameters": {"temperature": 0.7},
                "is_active": True,
                "priority": 10,
            }
            response = await client.post("/api/v1/admin/ai-configs", json=payload)
            assert response.status_code == 201
            data = response.json()
            assert data["config_key"] == "text_generation"
            assert data["provider"] == "deepseek"
            assert data["model_name"] == "deepseek-chat"
            # API key should be masked
            assert data["api_key"] == "****7890"
            assert data["is_active"] is True
            assert data["priority"] == 10
            assert "id" in data

    @pytest.mark.asyncio
    async def test_list_ai_configs_empty(self, admin_client):
        """Listing configs when none exist should return empty list."""
        async with admin_client as client:
            response = await client.get("/api/v1/admin/ai-configs")
            assert response.status_code == 200
            data = response.json()
            assert data["items"] == []
            assert data["total"] == 0
            assert data["page"] == 1

    @pytest.mark.asyncio
    async def test_list_ai_configs_paginated(self, admin_client):
        """Listing configs should support pagination."""
        async with admin_client as client:
            # Create 3 configs
            for i in range(3):
                payload = {
                    "config_key": f"key_{i}",
                    "provider": "deepseek",
                    "model_name": f"model_{i}",
                    "api_key": f"sk-key-{i}-abcdefgh",
                    "priority": i,
                }
                await client.post("/api/v1/admin/ai-configs", json=payload)

            # Get page 1 with page_size=2
            response = await client.get("/api/v1/admin/ai-configs?page=1&page_size=2")
            assert response.status_code == 200
            data = response.json()
            assert len(data["items"]) == 2
            assert data["total"] == 3
            assert data["has_more"] is True

            # Get page 2
            response = await client.get("/api/v1/admin/ai-configs?page=2&page_size=2")
            data = response.json()
            assert len(data["items"]) == 1
            assert data["has_more"] is False

    @pytest.mark.asyncio
    async def test_update_ai_config(self, admin_client):
        """Updating a config should change the specified fields."""
        async with admin_client as client:
            # Create
            payload = {
                "config_key": "text_generation",
                "provider": "deepseek",
                "model_name": "deepseek-chat",
                "api_key": "sk-original-key-1234",
                "priority": 5,
            }
            create_resp = await client.post("/api/v1/admin/ai-configs", json=payload)
            config_id = create_resp.json()["id"]

            # Update
            update_payload = {
                "model_name": "deepseek-chat-v2",
                "priority": 20,
            }
            response = await client.put(
                f"/api/v1/admin/ai-configs/{config_id}", json=update_payload
            )
            assert response.status_code == 200
            data = response.json()
            assert data["model_name"] == "deepseek-chat-v2"
            assert data["priority"] == 20
            # Unchanged fields
            assert data["provider"] == "deepseek"

    @pytest.mark.asyncio
    async def test_update_nonexistent_config(self, admin_client):
        """Updating a non-existent config should return 404."""
        async with admin_client as client:
            fake_id = str(uuid.uuid4())
            response = await client.put(
                f"/api/v1/admin/ai-configs/{fake_id}",
                json={"model_name": "new-model"},
            )
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_ai_config(self, admin_client):
        """Deleting a config should return 204 and remove it."""
        async with admin_client as client:
            # Create
            payload = {
                "config_key": "text_generation",
                "provider": "deepseek",
                "model_name": "deepseek-chat",
                "api_key": "sk-delete-me-1234",
            }
            create_resp = await client.post("/api/v1/admin/ai-configs", json=payload)
            config_id = create_resp.json()["id"]

            # Delete
            response = await client.delete(f"/api/v1/admin/ai-configs/{config_id}")
            assert response.status_code == 204

            # Verify it's gone
            list_resp = await client.get("/api/v1/admin/ai-configs")
            assert list_resp.json()["total"] == 0

    @pytest.mark.asyncio
    async def test_delete_nonexistent_config(self, admin_client):
        """Deleting a non-existent config should return 404."""
        async with admin_client as client:
            fake_id = str(uuid.uuid4())
            response = await client.delete(f"/api/v1/admin/ai-configs/{fake_id}")
            assert response.status_code == 404


# ─── Activate/Deactivate Tests (Task 14.3) ────────────────────────────────────


class TestAIConfigActivate:
    """Tests for activate/deactivate toggle."""

    @pytest.mark.asyncio
    async def test_toggle_activate(self, admin_client):
        """Toggling should flip is_active and invalidate cache."""
        async with admin_client as client:
            # Create active config
            payload = {
                "config_key": "text_generation",
                "provider": "deepseek",
                "model_name": "deepseek-chat",
                "api_key": "sk-toggle-test-1234",
                "is_active": True,
            }
            create_resp = await client.post("/api/v1/admin/ai-configs", json=payload)
            config_id = create_resp.json()["id"]

            # Toggle to inactive
            with patch("app.api.v1.endpoints.admin.invalidate_ai_config_cache", new_callable=AsyncMock) as mock_cache:
                response = await client.put(f"/api/v1/admin/ai-configs/{config_id}/activate")
                assert response.status_code == 200
                data = response.json()
                assert data["is_active"] is False
                assert "停用" in data["message"]

    @pytest.mark.asyncio
    async def test_toggle_activate_nonexistent(self, admin_client):
        """Toggling a non-existent config should return 404."""
        async with admin_client as client:
            fake_id = str(uuid.uuid4())
            response = await client.put(f"/api/v1/admin/ai-configs/{fake_id}/activate")
            assert response.status_code == 404


# ─── Test Connectivity Tests (Task 14.2) ──────────────────────────────────────


class TestAIConfigConnectivity:
    """Tests for model connectivity test endpoint."""

    @pytest.mark.asyncio
    async def test_connectivity_nonexistent(self, admin_client):
        """Testing a non-existent config should return 404."""
        async with admin_client as client:
            fake_id = str(uuid.uuid4())
            response = await client.post(f"/api/v1/admin/ai-configs/{fake_id}/test")
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_connectivity_returns_result(self, admin_client):
        """Testing connectivity should return a structured response."""
        async with admin_client as client:
            # Create config
            payload = {
                "config_key": "text_generation",
                "provider": "deepseek",
                "model_name": "deepseek-chat",
                "api_key": "sk-test-connectivity-1234",
                "api_base_url": "https://api.deepseek.com/v1",
            }
            create_resp = await client.post("/api/v1/admin/ai-configs", json=payload)
            config_id = create_resp.json()["id"]

            # Mock httpx to avoid real API calls
            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_response = AsyncMock()
                mock_response.status_code = 200
                mock_client_instance = AsyncMock()
                mock_client_instance.post = AsyncMock(return_value=mock_response)
                mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
                mock_client_instance.__aexit__ = AsyncMock(return_value=None)
                mock_client_cls.return_value = mock_client_instance

                response = await client.post(f"/api/v1/admin/ai-configs/{config_id}/test")
                assert response.status_code == 200
                data = response.json()
                assert "success" in data
                assert "message" in data
                assert "response_time_ms" in data


# ─── Audit Log Tests (Task 14.5) ──────────────────────────────────────────────


class TestAuditLogging:
    """Tests for operation audit logging."""

    @pytest.mark.asyncio
    async def test_create_generates_audit_log(self, admin_client):
        """Creating a config should generate an audit log entry."""
        async with admin_client as client:
            payload = {
                "config_key": "text_generation",
                "provider": "deepseek",
                "model_name": "deepseek-chat",
                "api_key": "sk-audit-test-1234",
            }
            await client.post("/api/v1/admin/ai-configs", json=payload)

        # Verify audit log was created
        async with TestSessionFactory() as session:
            stmt = select(AuditLog).where(AuditLog.action == "create")
            result = await session.execute(stmt)
            logs = result.scalars().all()
            assert len(logs) == 1
            assert logs[0].resource_type == "ai_config"
            assert logs[0].action == "create"

    @pytest.mark.asyncio
    async def test_delete_generates_audit_log(self, admin_client):
        """Deleting a config should generate an audit log entry."""
        async with admin_client as client:
            # Create
            payload = {
                "config_key": "text_generation",
                "provider": "deepseek",
                "model_name": "deepseek-chat",
                "api_key": "sk-audit-delete-1234",
            }
            create_resp = await client.post("/api/v1/admin/ai-configs", json=payload)
            config_id = create_resp.json()["id"]

            # Delete
            await client.delete(f"/api/v1/admin/ai-configs/{config_id}")

        # Verify audit log
        async with TestSessionFactory() as session:
            stmt = select(AuditLog).where(AuditLog.action == "delete")
            result = await session.execute(stmt)
            logs = result.scalars().all()
            assert len(logs) == 1
            assert logs[0].resource_type == "ai_config"
