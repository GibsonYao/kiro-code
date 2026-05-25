"""Tests for the points API endpoints."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.v1.endpoints.points import router
from app.models.family import FamilyMember, FamilyRole
from app.models.points import PointsAccount, PointsTransaction, PointsTransactionType
from app.models.user import User


# ─── Test App Setup ────────────────────────────────────────────────────────────


def create_test_app() -> FastAPI:
    """Create a minimal FastAPI app with the points router for testing."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/points")
    return app


# ─── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def user_id():
    return uuid.uuid4()


@pytest.fixture
def family_id():
    return uuid.uuid4()


@pytest.fixture
def mock_user(user_id):
    return User(id=user_id, nickname="TestUser")


@pytest.fixture
def mock_membership(family_id, user_id):
    return FamilyMember(
        id=uuid.uuid4(),
        family_id=family_id,
        user_id=user_id,
        role=FamilyRole.admin,
        nickname_in_family="Admin",
    )


@pytest.fixture
def sample_account(family_id, user_id):
    """Create a sample points account."""
    return PointsAccount(
        id=uuid.uuid4(),
        family_id=family_id,
        user_id=user_id,
        balance=150,
        total_earned=200,
        total_spent=50,
    )


@pytest.fixture
def sample_transactions(user_id):
    """Create sample points transactions."""
    account_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    return [
        PointsTransaction(
            id=uuid.uuid4(),
            account_id=account_id,
            type=PointsTransactionType.reward,
            amount=10,
            balance_after=110,
            source_type="task",
            source_id=uuid.uuid4(),
            description="完成任务奖励",
            created_at=now,
        ),
        PointsTransaction(
            id=uuid.uuid4(),
            account_id=account_id,
            type=PointsTransactionType.penalty,
            amount=-5,
            balance_after=105,
            source_type="task",
            source_id=uuid.uuid4(),
            description="任务超时扣分",
            created_at=now,
        ),
    ]


@pytest.fixture
def app(mock_user, mock_membership):
    """Create test app with mocked dependencies."""
    from app.core.deps import get_current_family, get_current_user, get_db

    app = create_test_app()

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_current_family] = lambda: mock_membership
    app.dependency_overrides[get_db] = lambda: AsyncMock()

    yield app

    app.dependency_overrides.clear()


@pytest.fixture
async def client(app):
    """Create an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ─── GET /api/v1/points/balance Tests ─────────────────────────────────────────


class TestGetBalance:
    """Tests for the GET /api/v1/points/balance endpoint."""

    @pytest.mark.asyncio
    @patch("app.api.v1.endpoints.points.get_or_create_account")
    async def test_returns_balance(self, mock_get_account, client, sample_account):
        """Should return the user's points balance."""
        mock_get_account.return_value = sample_account

        response = await client.get("/api/v1/points/balance")

        assert response.status_code == 200
        data = response.json()
        assert data["balance"] == 150
        assert data["total_earned"] == 200
        assert data["total_spent"] == 50

    @pytest.mark.asyncio
    @patch("app.api.v1.endpoints.points.get_or_create_account")
    async def test_returns_zero_balance_for_new_account(
        self, mock_get_account, client, family_id, user_id
    ):
        """Should return zero balance for a new account."""
        new_account = PointsAccount(
            id=uuid.uuid4(),
            family_id=family_id,
            user_id=user_id,
            balance=0,
            total_earned=0,
            total_spent=0,
        )
        mock_get_account.return_value = new_account

        response = await client.get("/api/v1/points/balance")

        assert response.status_code == 200
        data = response.json()
        assert data["balance"] == 0
        assert data["total_earned"] == 0
        assert data["total_spent"] == 0


# ─── GET /api/v1/points/history Tests ─────────────────────────────────────────


class TestGetHistory:
    """Tests for the GET /api/v1/points/history endpoint."""

    @pytest.mark.asyncio
    @patch("app.api.v1.endpoints.points.get_points_history")
    async def test_returns_empty_history(self, mock_get_history, client):
        """Should return empty list when no transactions exist."""
        mock_get_history.return_value = ([], 0)

        response = await client.get("/api/v1/points/history")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert data["has_more"] is False

    @pytest.mark.asyncio
    @patch("app.api.v1.endpoints.points.get_points_history")
    async def test_returns_transaction_history(
        self, mock_get_history, client, sample_transactions
    ):
        """Should return transaction history."""
        mock_get_history.return_value = (sample_transactions, 2)

        response = await client.get("/api/v1/points/history")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["items"][0]["type"] == "reward"
        assert data["items"][0]["amount"] == 10
        assert data["items"][1]["type"] == "penalty"
        assert data["items"][1]["amount"] == -5
        assert data["total"] == 2
        assert data["has_more"] is False

    @pytest.mark.asyncio
    @patch("app.api.v1.endpoints.points.get_points_history")
    async def test_pagination_parameters(self, mock_get_history, client):
        """Should pass pagination parameters correctly."""
        mock_get_history.return_value = ([], 0)

        response = await client.get("/api/v1/points/history?page=2&page_size=10")

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 10

    @pytest.mark.asyncio
    @patch("app.api.v1.endpoints.points.get_points_history")
    async def test_type_filter(self, mock_get_history, client, sample_transactions):
        """Should filter by transaction type."""
        # Only return reward transactions
        reward_txns = [t for t in sample_transactions if t.type == PointsTransactionType.reward]
        mock_get_history.return_value = (reward_txns, 1)

        response = await client.get("/api/v1/points/history?type=reward")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["type"] == "reward"

    @pytest.mark.asyncio
    @patch("app.api.v1.endpoints.points.get_points_history")
    async def test_has_more_when_more_pages(
        self, mock_get_history, client, sample_transactions
    ):
        """Should set has_more=True when there are more pages."""
        mock_get_history.return_value = ([sample_transactions[0]], 5)

        response = await client.get("/api/v1/points/history?page=1&page_size=1")

        assert response.status_code == 200
        data = response.json()
        assert data["has_more"] is True


# ─── GET /api/v1/points/leaderboard Tests ─────────────────────────────────────


class TestGetLeaderboard:
    """Tests for the GET /api/v1/points/leaderboard endpoint."""

    @pytest.mark.asyncio
    @patch("app.api.v1.endpoints.points.get_leaderboard")
    async def test_returns_empty_leaderboard(self, mock_get_leaderboard, client):
        """Should return empty list when no accounts exist."""
        mock_get_leaderboard.return_value = []

        response = await client.get("/api/v1/points/leaderboard")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []

    @pytest.mark.asyncio
    @patch("app.api.v1.endpoints.points.get_leaderboard")
    async def test_returns_leaderboard_entries(self, mock_get_leaderboard, client):
        """Should return leaderboard entries ranked by total_earned."""
        entries = [
            {
                "user_id": uuid.uuid4(),
                "nickname": "Alice",
                "balance": 200,
                "total_earned": 300,
            },
            {
                "user_id": uuid.uuid4(),
                "nickname": "Bob",
                "balance": 100,
                "total_earned": 150,
            },
        ]
        mock_get_leaderboard.return_value = entries

        response = await client.get("/api/v1/points/leaderboard")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["items"][0]["nickname"] == "Alice"
        assert data["items"][0]["total_earned"] == 300
        assert data["items"][1]["nickname"] == "Bob"
        assert data["items"][1]["total_earned"] == 150

    @pytest.mark.asyncio
    @patch("app.api.v1.endpoints.points.get_leaderboard")
    async def test_leaderboard_with_null_nickname(self, mock_get_leaderboard, client):
        """Should handle entries with null nicknames."""
        entries = [
            {
                "user_id": uuid.uuid4(),
                "nickname": None,
                "balance": 50,
                "total_earned": 100,
            },
        ]
        mock_get_leaderboard.return_value = entries

        response = await client.get("/api/v1/points/leaderboard")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["nickname"] is None
        assert data["items"][0]["total_earned"] == 100
