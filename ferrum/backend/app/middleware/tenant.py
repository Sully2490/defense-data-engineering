"""Tenant isolation middleware for multi-tenancy."""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.security import decode_token


class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware to extract org_id from JWT and set it in request state."""

    async def dispatch(self, request: Request, call_next):
        """Process request and extract tenant context.

        Args:
            request: FastAPI request
            call_next: Next middleware/endpoint

        Returns:
            Response from next handler
        """
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                payload = decode_token(token)
                # Set org_id in request state for use in RLS
                request.state.org_id = payload.get("org_id")
                request.state.user_id = payload.get("sub")
            except Exception:
                # Invalid token - let auth dependency handle it
                pass

        response = await call_next(request)
        return response
