# RPG Game Server

Backend server for a mobile RPG game built with Godot 4. Built with FastAPI, PostgreSQL, and Redis.

## Features

- 🔐 **Google OAuth Authentication** - Secure sign-in with JWT tokens
- 🎮 **Character Management** - Create up to 3 characters per account
- ⚔️ **Anti-Cheat System** - Server-authoritative battle validation
- 📊 **Progression Tracking** - 20 chapters with 10 stages each
- 💰 **Reward System** - Server-calculated rewards (no client manipulation)

## Tech Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 16 + SQLAlchemy (async)
- **Cache**: Redis 7
- **Auth**: Google OAuth 2.0 + JWT
- **Migrations**: Alembic

## Quick Start

### 1. Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Google Cloud project with OAuth credentials

### 2. Clone and Setup

```bash
cd C:\Godot\RPG-Server

# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy example env file
copy .env.example .env

# Edit .env with your settings
```

**Required settings:**
```env
DATABASE_URL=postgresql+asyncpg://rpg_user:rpg_password@localhost:5432/rpg_game
REDIS_URL=redis://localhost:6379
JWT_SECRET_KEY=your-super-secret-key-change-this
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

### 4. Start Services

```bash
# Start PostgreSQL and Redis
docker-compose up -d

# Wait for services to be ready
docker-compose ps
```

### 5. Run Server

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Server will be available at `http://localhost:8000`

## API Documentation

Once running, access the interactive API docs:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/google` | Exchange Google ID token for JWT |

### User
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/user/summary` | Get user profile + character list |

### Character
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/character` | Create new character |
| GET | `/character/{id}` | Full load - get complete character data |
| PUT | `/character/{id}` | Full save - update character data |
| DELETE | `/character/{id}` | Delete character |

### Progression (Anti-Cheat Critical)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/character/{id}/progression/chapters` | Get chapter unlock status |
| GET | `/character/{id}/progression/chapters/{ch}/stages/{st}/config` | **Get stage config** (required before battle) |
| POST | `/character/{id}/progression/chapters/complete` | **Complete stage** (validates battle) |

## Anti-Cheat Flow

### 1. Before Battle
Client **MUST** call `/progression/chapters/{ch}/stages/{st}/config`:

```json
// Response
{
  "session_token": "uuid",
  "expires_at": 1702234567,
  "mobs": [...],
  "rewards": {...}
}
```

Server:
- Generates unique session token
- Pre-calculates mob stats based on difficulty
- Pre-calculates rewards (not modifiable by client!)
- Sets 10-minute expiration

### 2. During Battle
Client uses the mob config to spawn enemies with correct stats.

### 3. After Battle
Client calls `/progression/chapters/complete` with:

```json
{
  "session_token": "uuid-from-config",
  "chapter": 5,
  "stage": 3,
  "battle_log": {
    "stats": {
      "total_damage_dealt": 15000,
      "mobs_killed": 8,
      "duration_ms": 120000
    },
    "mob_kills": [...]
  }
}
```

Server validates:
- ✅ Session token exists and not expired
- ✅ Session not already used (prevents replay)
- ✅ Chapter/stage match session
- ✅ Kill count matches expected mobs
- ✅ Damage dealt is plausible
- ✅ Battle duration is reasonable

If valid, server applies **pre-calculated rewards** from session.

## Database Schema

```sql
-- Users
users (id, google_id, email, display_name, avatar_url, created_at, last_login)

-- Characters (max 3 per user)
characters (id, user_id, name, class, level, xp, gold, gems, stats_json, 
            inventory_json, equipped_json, progression_json, ...)

-- Battle Sessions (anti-cheat)
battle_sessions (session_token PK, character_id, chapter, stage, 
                 mob_config_json, rewards_json, created_at, expires_at, 
                 is_used, used_at)
```

## Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Project Structure

```
RPG-Server/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Settings
│   ├── database.py          # DB connection
│   ├── auth/
│   │   ├── jwt.py           # JWT handling
│   │   └── google.py        # Google OAuth
│   ├── models/
│   │   ├── user.py          # User model
│   │   ├── character.py     # Character model
│   │   └── battle_session.py # Battle session model
│   ├── schemas/
│   │   ├── auth.py          # Auth schemas
│   │   ├── user.py          # User schemas
│   │   ├── character.py     # Character schemas
│   │   ├── items.py         # Item schemas
│   │   └── progression.py   # Progression schemas
│   ├── routers/
│   │   ├── auth.py          # Auth endpoints
│   │   ├── user.py          # User endpoints
│   │   ├── character.py     # Character endpoints
│   │   └── progression.py   # Progression endpoints
│   └── services/
│       ├── stage_generator.py   # Mob/stage generation
│       ├── battle_validator.py  # Battle log validation
│       └── rewards.py           # Reward calculations
├── alembic/                 # Database migrations
├── docker-compose.yml       # PostgreSQL + Redis
├── requirements.txt
├── .env.example
└── README.md
```

## Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable the Google+ API
4. Go to **Credentials** → **Create Credentials** → **OAuth Client ID**
5. Choose **Web application** (for testing) or **Android/iOS** for mobile
6. Add authorized origins/redirect URIs
7. Copy the Client ID and Client Secret to your `.env`

For Godot mobile apps, the client will:
1. Use Google Sign-In SDK to get an ID token
2. Send that ID token to `/auth/google`
3. Receive a JWT for subsequent API calls

## Production Deployment

### Environment Variables

```env
DEBUG=false
DATABASE_URL=postgresql+asyncpg://user:pass@db-host:5432/rpg_game
REDIS_URL=redis://redis-host:6379
JWT_SECRET_KEY=<generate-secure-key>
CORS_ORIGINS=["https://yourdomain.com"]
```

### Security Checklist

- [ ] Change `JWT_SECRET_KEY` to a secure random value
- [ ] Enable HTTPS only
- [ ] Configure proper CORS origins
- [ ] Set up rate limiting (use Redis)
- [ ] Enable database connection pooling
- [ ] Set up monitoring and logging
- [ ] Regular security audits of battle validation

## Development

### Run Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

### Code Style

```bash
# Install formatters
pip install black isort

# Format code
black app/
isort app/
```

## License

MIT

