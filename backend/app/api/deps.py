from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.student import Student

security_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: AsyncSession = Depends(get_db)
) -> Student:
    """
    FastAPI dependency extracting and validating JWT token from Authorization header.
    Returns the authenticated Student ORM model instance.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Missing Authorization header.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    subject = decode_access_token(token)
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    stmt = select(Student)
    if subject.isdigit():
        stmt = stmt.where(Student.id == int(subject))
    else:
        stmt = stmt.where(Student.email == subject)

    # A database failure must surface as an outage, never as a successful login.
    # See docs/adr/0004 -- no silent fallbacks.
    try:
        result = await db.execute(stmt)
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is temporarily unavailable.",
        ) from exc

    student = result.scalars().first()
    if student is None:
        # Token is validly signed but its subject has no account (e.g. deleted user).
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return student


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: AsyncSession = Depends(get_db)
) -> Optional[Student]:
    """
    Optional current user dependency returning Student if authenticated or None if unauthenticated.
    """
    if not credentials or not credentials.credentials:
        return None

    try:
        return await get_current_user(credentials=credentials, db=db)
    except HTTPException:
        return None
