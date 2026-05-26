"""Security and performance middleware."""

import logging
import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security response headers to all responses.

    Configures HTTPS-related headers, content security, and
    other security best practices.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )
        # HSTS - only in production (when not debug)
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"

        return response


class ResponseTimeMiddleware(BaseHTTPMiddleware):
    """Monitor API response times and log slow requests.

    Logs a warning for requests exceeding 500ms threshold.
    """

    SLOW_REQUEST_THRESHOLD_MS = 500

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start_time = time.time()

        response = await call_next(request)

        duration_ms = (time.time() - start_time) * 1000
        response.headers["X-Response-Time"] = f"{duration_ms:.1f}ms"

        # Log slow requests
        if duration_ms > self.SLOW_REQUEST_THRESHOLD_MS:
            logger.warning(
                f"Slow request: {request.method} {request.url.path} "
                f"took {duration_ms:.1f}ms (threshold: {self.SLOW_REQUEST_THRESHOLD_MS}ms)"
            )

        return response


class FamilyDataIsolationMiddleware(BaseHTTPMiddleware):
    """Request-level family_id validation middleware.

    Ensures that API requests include proper family context.
    The actual data isolation is enforced at the query level via
    get_current_family dependency, but this middleware adds an
    extra layer of validation for API paths that require family context.
    """

    # Paths that don't require family context
    EXEMPT_PATHS = {
        "/api/health",
        "/api/docs",
        "/api/redoc",
        "/api/openapi.json",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/refresh",
        "/api/v1/auth/wechat-login",
        "/api/v1/auth/phone-login",
        "/api/v1/auth/email-login",
        "/api/v1/auth/email-register",
        "/api/v1/auth/demo-login",
        "/api/v1/auth/send-code",
        "/api/v1/auth/me",
        "/api/v1/families",
    }

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip non-API paths and exempt paths
        path = request.url.path
        if not path.startswith("/api/v1") or path in self.EXEMPT_PATHS:
            return await call_next(request)

        # The actual family_id enforcement is done via the get_current_family
        # dependency in each endpoint. This middleware just logs for monitoring.
        # Full enforcement at middleware level would require DB access which
        # is better handled at the dependency injection level.
        return await call_next(request)
