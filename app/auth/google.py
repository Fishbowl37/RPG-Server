from google.oauth2 import id_token
from google.auth.transport import requests
import httpx

from app.config import get_settings

settings = get_settings()


class GoogleUserInfo:
    """Parsed user info from Google token."""
    def __init__(self, google_id: str, email: str, name: str | None, picture: str | None):
        self.google_id = google_id
        self.email = email
        self.name = name
        self.picture = picture


async def verify_google_token(token: str) -> GoogleUserInfo | None:
    """
    Verify a Google ID token and extract user information.
    
    For mobile apps (like Godot), the client sends an ID token obtained
    from Google Sign-In SDK. This function verifies that token.
    
    Returns GoogleUserInfo if valid, None if invalid.
    """
    try:
        # Verify the token with Google
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            settings.google_client_id
        )
        
        # Token is valid, extract user info
        return GoogleUserInfo(
            google_id=idinfo["sub"],
            email=idinfo.get("email", ""),
            name=idinfo.get("name"),
            picture=idinfo.get("picture")
        )
        
    except ValueError as e:
        # Token is invalid
        print(f"Google token verification failed: {e}")
        return None


async def verify_google_auth_code(auth_code: str) -> GoogleUserInfo | None:
    """
    Alternative: Exchange an authorization code for tokens.
    Use this if your client sends an auth code instead of ID token.
    
    Returns GoogleUserInfo if valid, None if invalid.
    """
    try:
        # Exchange auth code for tokens
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": auth_code,
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "grant_type": "authorization_code",
                    "redirect_uri": "postmessage",  # For mobile apps
                }
            )
            
            if response.status_code != 200:
                print(f"Token exchange failed: {response.text}")
                return None
            
            tokens = response.json()
            id_token_str = tokens.get("id_token")
            
            if not id_token_str:
                return None
            
            # Now verify the ID token
            return await verify_google_token(id_token_str)
            
    except Exception as e:
        print(f"Google auth code exchange failed: {e}")
        return None

