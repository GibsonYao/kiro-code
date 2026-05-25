"""Tests for the reviews API endpoints."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.v1.endpoints.reviews import router
from app.models.family import FamilyMember, FamilyRole
from app.models.review import Review, ReviewStatus, ReviewTargetType
from app.models.user import User


# ─── Test App Setup ────────────────────────────────────────────────────────────


def create_test_app() -> FastAPI:
    """Create a minimal FastAPI app with the reviews router for testing."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/reviews")
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
    user = User(id=user_id, nickname="TestUser")
    return user


@pytest.fixture
def mock_membership(family_id, user_id):
    member = FamilyMember(
        id=uuid.uuid4(),
        family_id=family_id,
        user_id=user_id,
        role=FamilyRole.admin,
        nickname_in_family="Admin",
    )
    return member


@pytest.fixture
def sample_review(family_id, user_id):
    """Create a sample pending review."""
    from datetime import datetime, timezone

    return Review(
        id=uuid.uuid4(),
        family_id=family_id,
        target_type=ReviewTargetType.task,
        target_id=uuid.uuid4(),
        reviewer_id=user_id,
        submitter_id=uuid.uuid4(),
        status=ReviewStatus.pending,
        comment=None,
        evidence_text="I did it",
        evidence_photos=None,
        evidence_qrcode=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


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


# ─── GET /api/v1/reviews/pending Tests ────────────────────────────────────────


class TestListPendingReviews:
    """Tests for the GET /api/v1/reviews/pending endpoint."""

    @pytest.mark.asyncio
    @patch("app.api.v1.endpoints.reviews.get_pending_reviews")
    async def test_returns_empty_list_when_no_pending_reviews(
        self, mock_get_pending, client
    ):
        """Should return empty list when there are no pending reviews."""
        mock_get_pending.return_value = ([], 0)

        response = await client.get("/api/v1/reviews/pending")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert data["has_more"] is False

    @pytest.mark.asyncio
    @patch("app.api.v1.endpoints.reviews.get_pending_reviews")
    async def test_returns_pending_reviews(
        self, mock_get_pending, client, sample_review
    ):
        """Should return pending reviews for the current user."""
        mock_get_pending.return_value = ([sample_review], 1)

        response = await client.get("/api/v1/reviews/pending")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == str(sample_review.id)
        assert data["items"][0]["status"] == "pending"
        assert data["total"] == 1
        assert data["has_more"] is False

    @pytest.mark.asyncio
    @patch("app.api.v1.endpoints.reviews.get_pending_reviews")
    async def test_pagination_parameters(self, mock_get_pending, client):
        """Should pass pagination parameters to the service."""
        mock_get_pending.return_value = ([], 0)

        response = await client.get("/api/v1/reviews/pending?page=2&page_size=10")

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 10

    @pytest.mark.asyncio
    @patch("app.api.v1.endpoints.reviews.get_pending_reviews")
    async def test_has_more_when_more_pages(self, mock_get_pending, client, sample_review):
        """Should set has_more=True when there are more pages."""
        mock_get_pending.return_value = ([sample_review], 5)

        response = await client.get("/api/v1/reviews/pending?page=1&page_size=1")

        assert response.status_code == 200
        data = response.json()
        assert data["has_more"] is True


# ─── POST /api/v1/reviews/{id}/approve Tests ──────────────────────────────────


class TestApproveReview:
    """Tests for the POST /api/v1/reviews/{id}/approve endpoint."""

    @pytest.mark.asyncio
    @patch("app.api.v1.endpoints.reviews.approve_review")
    @patch("app.api.v1.endpoints.reviews.get_review_by_id")
    async def test_approve_review_success(
        self, mock_get_review, mock_approve, client, sample_review
    ):
        """Should approve a pending review when called by the reviewer."""
        mock_get_review.return_value = sample_review

        approved_review = Review(
            id=sample_review.id,
            family_id=sample_review.family_id,
            target_type=sample_review.target_type,
            target_id=sample_review.target_id,
            reviewer_id=sample_review.reviewer_id,
            submitter_id=sample_review.submitter_id,
            status=ReviewStatus.approved,
            comment="Good job!",
            evidence_text=sample_review.evidence_text,
            evidence_photos=sample_review.evidence_photos,
            evidence_qrcode=sample_review.evidence_qrcode,
            created_at=sample_review.created_at,
            updated_at=sample_review.updated_at,
        )
        mock_approve.return_value = approved_review

        response = await client.post(
            f"/api/v1/reviews/{sample_review.id}/approve",
            json={"comment": "Good job!"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"
        assert data["comment"] == "Good job!"

    @pytest.mark.asyncio
    @patch("app.api.v1.endpoints.reviews.get_review_by_id")
    async def test_approve_review_not_found(self, mock_get_review, client):
        """Should return 404 when review doesn't exist."""
        mock_get_review.return_value = None

        response = await client.post(
            f"/api/v1/reviews/{uuid.uuid4()}/approve",
            json={"comment": None},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    @patch("app.api.v1.endpoints.reviews.get_review_by_id")
    async def test_approve_review_not_reviewer(
        self, mock_get_review, client, sample_review
    ):
        """Should return 403 when current user is not the assigned reviewer."""
        # Set reviewer_id to a different user
        sample_review.reviewer_id = uuid.uuid4()
        mock_get_review.return_value = sample_review

        response = await client.post(
            f"/api/v1/reviews/{sample_review.id}/approve",
            json={"comment": None},
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    @patch("app.api.v1.endpoints.reviews.get_review_by_id")
    async def test_approve_review_already_approved(
        self, mock_get_review, client, sample_review
    ):
        """Should return 400 when review is not in pending status."""
        sample_review.status = ReviewStatus.approved
        mock_get_review.return_value = sample_review

        response = await client.post(
            f"/api/v1/reviews/{sample_review.id}/approve",
            json={"comment": None},
        )

        assert response.status_code == 400


# ─── POST /api/v1/reviews/{id}/reject Tests ───────────────────────────────────


class TestRejectReview:
    """Tests for the POST /api/v1/reviews/{id}/reject endpoint."""

    @pytest.mark.asyncio
    @patch("app.api.v1.endpoints.reviews.reject_review")
    @patch("app.api.v1.endpoints.reviews.get_review_by_id")
    async def test_reject_review_success(
        self, mock_get_review, mock_reject, client, sample_review
    ):
        """Should reject a pending review when called by the reviewer."""
        mock_get_review.return_value = sample_review

        rejected_review = Review(
            id=sample_review.id,
            family_id=sample_review.family_id,
            target_type=sample_review.target_type,
            target_id=sample_review.target_id,
            reviewer_id=sample_review.reviewer_id,
            submitter_id=sample_review.submitter_id,
            status=ReviewStatus.rejected,
            comment="Needs more work",
            evidence_text=sample_review.evidence_text,
            evidence_photos=sample_review.evidence_photos,
            evidence_qrcode=sample_review.evidence_qrcode,
            created_at=sample_review.created_at,
            updated_at=sample_review.updated_at,
        )
        mock_reject.return_value = rejected_review

        response = await client.post(
            f"/api/v1/reviews/{sample_review.id}/reject",
            json={"comment": "Needs more work"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "rejected"
        assert data["comment"] == "Needs more work"

    @pytest.mark.asyncio
    @patch("app.api.v1.endpoints.reviews.get_review_by_id")
    async def test_reject_review_not_found(self, mock_get_review, client):
        """Should return 404 when review doesn't exist."""
        mock_get_review.return_value = None

        response = await client.post(
            f"/api/v1/reviews/{uuid.uuid4()}/reject",
            json={"comment": "Bad"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    @patch("app.api.v1.endpoints.reviews.get_review_by_id")
    async def test_reject_review_not_reviewer(
        self, mock_get_review, client, sample_review
    ):
        """Should return 403 when current user is not the assigned reviewer."""
        sample_review.reviewer_id = uuid.uuid4()
        mock_get_review.return_value = sample_review

        response = await client.post(
            f"/api/v1/reviews/{sample_review.id}/reject",
            json={"comment": "Bad"},
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    @patch("app.api.v1.endpoints.reviews.get_review_by_id")
    async def test_reject_review_already_rejected(
        self, mock_get_review, client, sample_review
    ):
        """Should return 400 when review is not in pending status."""
        sample_review.status = ReviewStatus.rejected
        mock_get_review.return_value = sample_review

        response = await client.post(
            f"/api/v1/reviews/{sample_review.id}/reject",
            json={"comment": "Bad"},
        )

        assert response.status_code == 400
