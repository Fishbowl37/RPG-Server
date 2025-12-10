from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone

from app.database import get_db
from app.models import User
from app.schemas.auth import GoogleAuthRequest, TokenResponse
from app.auth.google import verify_google_token
from app.auth.jwt import create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/google", response_model=TokenResponse)
async def google_auth(
    request: GoogleAuthRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate with Google OAuth.
    
    The client sends the Google ID token obtained from Google Sign-In.
    The server verifies it and returns a JWT for subsequent requests.
    """
    # Verify Google token
    google_user = await verify_google_token(request.id_token)
    
    if google_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token"
        )
    
    # Check if user exists
    result = await db.execute(
        select(User).where(User.google_id == google_user.google_id)
    )
    user = result.scalar_one_or_none()
    is_new_user = False
    
    if user is None:
        # Create new user
        user = User(
            google_id=google_user.google_id,
            email=google_user.email,
            display_name=google_user.name,
            avatar_url=google_user.picture,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        is_new_user = True
    else:
        # Update last login
        user.last_login = datetime.now(timezone.utc)
        user.display_name = google_user.name or user.display_name
        user.avatar_url = google_user.picture or user.avatar_url
        await db.commit()
    
    # Create JWT token
    access_token, expires_in = create_access_token(user.id)
    
    return TokenResponse(
        access_token=access_token,
        expires_in=expires_in,
        user_id=user.id,
        is_new_user=is_new_user
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    db: AsyncSession = Depends(get_db),
    # Note: For refresh, you'd typically use a different token mechanism
    # This is a simplified version that just issues a new token
):
    """
    Refresh the JWT token.
    
    In a production app, you'd use refresh tokens stored in Redis.
    This is a simplified implementation.
    """
    # This endpoint would need the current user from an existing valid token
    # For now, this is a placeholder - you'd implement refresh token logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Refresh token endpoint not yet implemented"
    )

