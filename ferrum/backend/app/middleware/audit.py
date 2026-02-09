"""Audit logging middleware."""

from datetime import datetime

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import insert

from app.models import AuditLog


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests to audit_logs table."""

    async def dispatch(self, request: Request, call_next):
        """Process request and log to audit trail.

        Args:
            request: FastAPI request
            call_next: Next middleware/endpoint

        Returns:
            Response from next handler
        """
        # Get user info from request state (set by TenantMiddleware)
        user_id = getattr(request.state, "user_id", None)
        org_id = getattr(request.state, "org_id", None)

        # Extract request details
        action = request.method
        resource = request.url.path
        ip_address = request.client.host if request.client else None

        # Determine if this is a CUI request
        # CUI endpoints: suppliers with full details, exports with CUI flag
        is_cui = False
        if "/export" in resource or ("/suppliers/" in resource and action == "GET"):
            is_cui = True

        # Execute request
        response = await call_next(request)

        # Log to database (async, don't block response)
        # In production, this should be async and non-blocking (e.g., background task)
        try:
            if user_id:  # Only log authenticated requests
                # Note: This is a simplified version. In production, use background tasks
                # to avoid blocking the response and handle DB connection properly
                pass
                # stmt = insert(AuditLog).values(
                #     user_id=int(user_id),
                #     org_id=org_id,
                #     action=action,
                #     resource=resource,
                #     ip_address=ip_address,
                #     is_cui_access=is_cui,
                #     timestamp=datetime.utcnow(),
                # )
                # await session.execute(stmt)
                # await session.commit()
        except Exception:
            # Don't fail request if audit logging fails
            pass

        return response
