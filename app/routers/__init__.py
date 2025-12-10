from app.routers.auth import router as auth_router
from app.routers.user import router as user_router
from app.routers.character import router as character_router
from app.routers.progression import router as progression_router

__all__ = [
    "auth_router",
    "user_router", 
    "character_router",
    "progression_router",
]

