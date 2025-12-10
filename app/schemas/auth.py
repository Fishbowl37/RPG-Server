from pydantic import BaseModel


class GoogleAuthRequest(BaseModel):
    """Request body for Google OAuth authentication."""
    id_token: str  # Google ID token from client


class TokenResponse(BaseModel):
    """Response containing JWT token."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user_id: str
    is_new_user: bool = False

