"""
Simple mock server - no database required!
Run with: uvicorn app.main_mock:app --reload --port 8000

Data structures match the Godot client mocks in:
C:\Godot\RPG\scripts\api\implementations\mock\
"""
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid
import random
import time
import json
from datetime import datetime

app = FastAPI(
    title="RPG Game Server (Mock)",
    description="Mock server for testing - no DB required",
    version="1.0.0",
)


# ============ REQUEST/RESPONSE LOGGING MIDDLEWARE ============

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = f"{int(time.time() * 1000)}-{random.randint(1000, 9999)}"
        
        # Log request
        print("\n" + "=" * 60)
        print(f">>> REQUEST [{request_id}]")
        print(f"   Method: {request.method}")
        print(f"   URL: {request.url}")
        print(f"   Path: {request.url.path}")
        
        # Log headers (excluding sensitive ones)
        headers_to_log = {k: v for k, v in request.headers.items() 
                         if k.lower() not in ['cookie']}
        print(f"   Headers: {json.dumps(dict(headers_to_log), indent=2)}")
        
        # Log body for POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    try:
                        body_json = json.loads(body)
                        print(f"   Body: {json.dumps(body_json, indent=2)}")
                    except json.JSONDecodeError:
                        print(f"   Body (raw): {body.decode('utf-8', errors='ignore')[:500]}")
                    
                    # Reconstruct request body for downstream handlers
                    async def receive():
                        return {"type": "http.request", "body": body}
                    request = Request(request.scope, receive)
            except Exception as e:
                print(f"   Body: (could not read: {e})")
        
        # Process request
        start_time = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000
        
        # Capture response body
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk
        
        # Log response
        print(f"\n<<< RESPONSE [{request_id}]")
        print(f"   Status: {response.status_code}")
        print(f"   Duration: {duration_ms:.2f}ms")
        
        try:
            response_json = json.loads(response_body)
            # Truncate large responses for readability
            response_str = json.dumps(response_json, indent=2)
            if len(response_str) > 1000:
                print(f"   Body: {response_str[:1000]}...")
                print(f"   (truncated, total {len(response_str)} chars)")
            else:
                print(f"   Body: {response_str}")
        except json.JSONDecodeError:
            print(f"   Body (raw): {response_body.decode('utf-8', errors='ignore')[:500]}")
        
        print("=" * 60 + "\n")
        
        # Return response with body
        from starlette.responses import Response
        return Response(
            content=response_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type
        )


# Add logging middleware FIRST (before CORS)
app.add_middleware(LoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ AUTH HELPER ============

def verify_token(authorization: Optional[str]) -> str:
    """Verify Bearer token - mock version accepts 'mock_token_123' or any Bearer token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    return authorization.replace("Bearer ", "")


# ============ MOCK DATA (matching Godot client mocks) ============

# Valid tokens and their user mappings
MOCK_USER_CHARACTERS = {
    "mock_token_123": ["char_001", "char_002"]
}

# User data (returned by get_summary_data)
MOCK_USER_DATA = {
    "mock_token_123": {
        "id": "user_001",
        "username": "MockPlayer",
        "icon": "icon_001",
        "characters": [
            {
                "id": "char_001",
                "name": "TestWarrior",
                "character_class": 1,  # WARRIOR
                "level": 100,
                "power": 262340,
                "free_stat_points": 5
            },
            {
                "id": "char_002",
                "name": "TestMage",
                "character_class": 0,  # MAGE
                "level": 8,
                "power": 980,
                "free_stat_points": 3
            }
        ],
        "currency": {
            "gold": 500000,
            "gems": 1000
        },
        "guild_id": "guild_001"
    }
}

# Full character data
MOCK_CHARACTERS = {
    "char_001": {
        "id": "char_001",
        "name": "TestWarrior",
        "character_class": 1,  # WARRIOR
        "level": 100,
        "xp": 250,
        "power": 262340,
        "currency": {"gold": 500000, "gems": 1000},
        "free_stat_points": 5,
        "stats": {
            "attack": 0,
            "defense": 0,
            "strength": 8,
            "agility": 4,
            "energy": 2,
            "vitality": 6
        },
        "inventory": {
            "capacity": 50,
            "items": [],
            "equipped": {}
        },
        "potions": {
            "health_potion": None,
            "mana_potion": None,
            "health_slot_id": "",
            "mana_slot_id": ""
        },
        "skills": {
            "unlocked_skills": {},
            "equipped_skills": [],
            "skill_points": 5
        },
        "progression": {
            "chapter_progress": {"highest_chapter": 3, "highest_stage": 6},
            "dungeon_progress": {},
            "daily_runs": {}
        },
        "shop": {
            "last_refresh": "",
            "items": []
        }
    },
    "char_002": {
        "id": "char_002",
        "name": "TestMage",
        "character_class": 0,  # MAGE
        "level": 8,
        "xp": 180,
        "power": 980,
        "currency": {"gold": 500000, "gems": 1000},
        "free_stat_points": 3,
        "stats": {
            "attack": 8,
            "defense": 6,
            "strength": 1,
            "agility": 3,
            "energy": 12,
            "vitality": 4
        },
        "inventory": {
            "capacity": 50,
            "items": [],
            "equipped": {}
        },
        "potions": {
            "health_potion": None,
            "mana_potion": None,
            "health_slot_id": "",
            "mana_slot_id": ""
        },
        "skills": {
            "unlocked_skills": {},
            "equipped_skills": [],
            "skill_points": 5
        },
        "progression": {
            "chapter_progress": {"highest_chapter": 1, "highest_stage": 0},
            "dungeon_progress": {},
            "daily_runs": {}
        },
        "shop": {
            "last_refresh": "",
            "items": []
        }
    }
}

# Chapter progress per character
MOCK_CHAPTER_PROGRESS = {
    "char_001": {"highest_chapter": 3, "highest_stage": 6},
    "char_002": {"highest_chapter": 1, "highest_stage": 0}
}

# Session tokens for battle validation
MOCK_SESSIONS: Dict[str, Dict] = {}

# Persistent inventory storage (populated on first access)
MOCK_INVENTORIES: Dict[str, Dict] = {}

# Slot ID to slot name mapping
SLOT_ID_TO_NAME = {
    0: "weapon", 1: "helm", 2: "armor", 3: "pants", 4: "gloves", 5: "boots",
    6: "ring1", 7: "ring2", 8: "bracelet1", 9: "bracelet2", 10: "necklace", 11: "wings"
}

# Item types
ITEM_TYPE_GEAR = 0
ITEM_TYPE_CONSUMABLE = 1
ITEM_TYPE_UPGRADE_GEM = 3
ITEM_TYPE_REFINE_GEM = 4


# ============ SCHEMAS ============

class GoogleAuthRequest(BaseModel):
    id_token: str

class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str

class CharacterCreate(BaseModel):
    name: str
    character_class: int

class StageCompleteRequest(BaseModel):
    chapter: int
    stage: int
    session_token: Optional[str] = None
    battle_log: Optional[dict] = None
    game_log: Optional[dict] = None  # Accept both field names from client


class InventoryAction(BaseModel):
    action: str  # equip, unequip, discard, lock, unlock, equip_potion
    item_id: Optional[str] = None
    slot_id: Optional[int] = None
    potion_type: Optional[str] = None  # "health" or "mana"
    timestamp: Optional[int] = None


class InventoryActionsRequest(BaseModel):
    actions: List[InventoryAction]


class ActionResult(BaseModel):
    success: bool
    error: Optional[str] = None


class InventoryActionsResponse(BaseModel):
    success: bool
    results: List[ActionResult]
    failed_index: int
    inventory: dict


# ============ ENDPOINTS ============

@app.on_event("startup")
async def startup_event():
    print("\n" + "=" * 50)
    print("[SERVER] RPG Game Server (Mock) Started!")
    print("[INFO] API Docs: http://localhost:8000/docs")
    print("[INFO] Health: http://localhost:8000/health")
    print("[AUTH] Test Token: mock_token_123")
    print("[DATA] Test Characters: char_001 (Warrior), char_002 (Mage)")
    print("=" * 50 + "\n")


@app.get("/")
async def root():
    return {"status": "ok", "service": "RPG Game Server (Mock)", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy", "database": "mock", "redis": "mock"}


# ============ AUTH ============

@app.post("/auth/google")
async def google_auth(request: GoogleAuthRequest):
    """Exchange Google ID token for JWT (mock - accepts any token)"""
    # In mock mode, any token works and returns the mock user
    return {
        "success": True,
        "auth": {
            "access_token": "mock_token_123",
            "refresh_token": "mock_refresh_token_456",
            "expires_in": 3600,
            "token_type": "Bearer"
        },
        "token": "mock_token_123"
    }


# ============ USER ============

@app.get("/user/summary")
async def get_user_summary(authorization: Optional[str] = Header(None)):
    """Get user profile + character list (matches CharacterApi.get_summary_data)"""
    token = verify_token(authorization)
    
    if token not in MOCK_USER_DATA:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return {
        "success": True,
        "user": MOCK_USER_DATA[token]
    }


# ============ CHARACTER ============

@app.post("/character")
async def create_character(data: CharacterCreate, authorization: Optional[str] = Header(None)):
    """Create new character"""
    token = verify_token(authorization)
    
    # Mock mode doesn't support character creation
    return {
        "success": False,
        "error": "Character creation not supported in mock mode"
    }


@app.get("/character/{character_id}")
async def get_character(character_id: str, authorization: Optional[str] = Header(None)):
    """Get full character data (matches CharacterApi.get_character_data)"""
    token = verify_token(authorization)
    
    # Validate ownership
    if token not in MOCK_USER_CHARACTERS:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    if character_id not in MOCK_USER_CHARACTERS[token]:
        raise HTTPException(status_code=403, detail="Character not found or not owned by user")
    
    if character_id not in MOCK_CHARACTERS:
        raise HTTPException(status_code=404, detail="Character not found")
    
    return {
        "success": True,
        "character": MOCK_CHARACTERS[character_id]
    }


@app.put("/character/{character_id}")
async def save_character(character_id: str, data: dict, authorization: Optional[str] = Header(None)):
    """Save character data (matches CharacterApi.save_character_data)"""
    token = verify_token(authorization)
    
    # Validate ownership
    if token not in MOCK_USER_CHARACTERS:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    if character_id not in MOCK_USER_CHARACTERS[token]:
        raise HTTPException(status_code=403, detail="Character not found or not owned by user")
    
    # In mock mode, we pretend to save
    # In a real server, we'd update MOCK_CHARACTERS[character_id]
    return {
        "success": True,
        "character": data
    }


@app.delete("/character/{character_id}")
async def delete_character(character_id: str, authorization: Optional[str] = Header(None)):
    """Delete character"""
    token = verify_token(authorization)
    
    if token not in MOCK_USER_CHARACTERS:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    if character_id not in MOCK_USER_CHARACTERS[token]:
        raise HTTPException(status_code=403, detail="Character not found or not owned by user")
    
    return {"success": True}


# ============ INVENTORY ============

@app.get("/character/{character_id}/inventory")
async def get_inventory(character_id: str, authorization: Optional[str] = Header(None)):
    """Get inventory data (matches InventoryApi.get_inventory_data)"""
    token = verify_token(authorization)
    
    if token not in MOCK_USER_CHARACTERS:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    if character_id not in MOCK_USER_CHARACTERS[token]:
        raise HTTPException(status_code=403, detail="Character not found or not owned by user")
    
    # Return persistent inventory (creates from mock if needed)
    inventory = _get_or_create_inventory(character_id)
    
    return {
        "success": True,
        "inventory": inventory
    }


@app.put("/character/{character_id}/inventory")
async def save_inventory(character_id: str, data: dict, authorization: Optional[str] = Header(None)):
    """Save inventory data (matches InventoryApi.save_inventory_data)"""
    token = verify_token(authorization)
    
    if token not in MOCK_USER_CHARACTERS:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    if character_id not in MOCK_USER_CHARACTERS[token]:
        raise HTTPException(status_code=403, detail="Character not found or not owned by user")
    
    # Store in persistent mock storage
    MOCK_INVENTORIES[character_id] = data
    
    return {
        "success": True,
        "inventory": data
    }


@app.post("/character/{character_id}/inventory/actions")
async def execute_inventory_actions(
    character_id: str, 
    data: InventoryActionsRequest, 
    authorization: Optional[str] = Header(None)
):
    """
    Execute batched inventory actions (equip, unequip, discard, lock, unlock, equip_potion).
    Actions are processed in order. Stops on first failure.
    """
    token = verify_token(authorization)
    
    if token not in MOCK_USER_CHARACTERS:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    if character_id not in MOCK_USER_CHARACTERS[token]:
        raise HTTPException(status_code=403, detail="Character not found or not owned by user")
    
    # Get or initialize persistent inventory
    inventory = _get_or_create_inventory(character_id)
    
    results: List[ActionResult] = []
    failed_index = -1
    
    # Process each action in order
    for i, action in enumerate(data.actions):
        result = _validate_and_apply_action(inventory, action, character_id)
        results.append(result)
        
        if not result.success:
            failed_index = i
            # Return immediately on failure
            return {
                "success": False,
                "results": [{"success": r.success, "error": r.error} for r in results],
                "failed_index": failed_index,
                "inventory": inventory
            }
    
    # All actions succeeded - persist the inventory
    MOCK_INVENTORIES[character_id] = inventory
    
    return {
        "success": True,
        "results": [{"success": r.success, "error": r.error} for r in results],
        "failed_index": -1,
        "inventory": inventory
    }


# ============ PROGRESSION ============

@app.get("/character/{character_id}/progression/chapters")
async def get_chapter_progress(character_id: str, authorization: Optional[str] = Header(None)):
    """Get chapter progress (matches ProgressionApi.get_chapter_progress)"""
    token = verify_token(authorization)
    
    if token not in MOCK_USER_CHARACTERS:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    if character_id not in MOCK_USER_CHARACTERS[token]:
        raise HTTPException(status_code=403, detail="Character not found or not owned by user")
    
    progress = MOCK_CHAPTER_PROGRESS.get(character_id, {"highest_chapter": 1, "highest_stage": 0})
    
    return {
        "success": True,
        "chapters": progress
    }


@app.get("/character/{character_id}/progression/chapters/{chapter}/stages/{stage}/config")
async def get_stage_config(character_id: str, chapter: int, stage: int, authorization: Optional[str] = Header(None)):
    """Get stage config before battle (matches ProgressionApi.get_stage_config)"""
    token = verify_token(authorization)
    
    if token not in MOCK_USER_CHARACTERS:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    if character_id not in MOCK_USER_CHARACTERS[token]:
        raise HTTPException(status_code=403, detail="Character not found or not owned by user")
    
    # Generate session token
    session_token = f"session_{chapter}_{stage}_{int(time.time())}_{random.randint(1000, 9999)}"
    
    # Calculate stage properties
    is_boss = (stage % 10 == 0)
    is_miniboss = (stage % 10 == 5)
    difficulty = _calculate_difficulty(chapter, stage, is_boss, is_miniboss)
    mob_count = _calculate_mob_count(stage, is_boss, is_miniboss, chapter)
    
    # Generate mobs
    mobs = []
    for i in range(mob_count):
        is_stage_boss = is_boss and i == 0
        is_stage_miniboss = is_miniboss and i == 0
        mobs.append(_generate_mob_config(chapter, stage, difficulty, is_stage_boss, is_stage_miniboss))
    
    # Calculate rewards (server-side!)
    rewards = _calculate_chapter_rewards(chapter, stage)
    
    # Generate stage name
    if is_boss:
        stage_name = f"Chapter {chapter}-10: Final Boss"
    elif is_miniboss:
        stage_name = f"Chapter {chapter}-5: Mini Boss"
    else:
        stage_name = f"Chapter {chapter}-{stage}"
    
    config = {
        "session_token": session_token,
        "expires_at": int(time.time()) + 600,
        "chapter": chapter,
        "stage": stage,
        "stage_name": stage_name,
        "is_boss": is_boss,
        "is_miniboss": is_miniboss,
        "difficulty_multiplier": difficulty,
        "time_limit_seconds": 300,
        "mobs": mobs,
        "rewards": rewards
    }
    
    # Store session for validation
    MOCK_SESSIONS[session_token] = {
        "character_id": character_id,
        "chapter": chapter,
        "stage": stage,
        "rewards": rewards,
        "expires_at": config["expires_at"],
        "used": False
    }
    
    return {
        "success": True,
        "config": config
    }


@app.post("/character/{character_id}/progression/chapters/complete")
async def complete_stage(character_id: str, data: StageCompleteRequest, authorization: Optional[str] = Header(None)):
    """Complete a stage (matches ProgressionApi.complete_chapter_stage)"""
    token = verify_token(authorization)
    
    if token not in MOCK_USER_CHARACTERS:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    if character_id not in MOCK_USER_CHARACTERS[token]:
        raise HTTPException(status_code=403, detail="Character not found or not owned by user")
    
    chapter = data.chapter
    stage = data.stage
    
    # Get or create progress
    if character_id not in MOCK_CHAPTER_PROGRESS:
        MOCK_CHAPTER_PROGRESS[character_id] = {"highest_chapter": 1, "highest_stage": 0}
    
    progress = MOCK_CHAPTER_PROGRESS[character_id]
    
    # Check if already completed
    already_completed = False
    if chapter < progress["highest_chapter"]:
        already_completed = True
    elif chapter == progress["highest_chapter"] and stage <= progress["highest_stage"]:
        already_completed = True
    
    if already_completed:
        return {
            "success": True,
            "already_completed": True,
            "rewards": {},
            "progression": progress
        }
    
    # Update progress
    if chapter > progress["highest_chapter"] or (chapter == progress["highest_chapter"] and stage > progress["highest_stage"]):
        progress["highest_chapter"] = chapter
        progress["highest_stage"] = stage
    
    # Calculate rewards
    rewards = _calculate_chapter_rewards(chapter, stage)
    
    return {
        "success": True,
        "already_completed": False,
        "rewards": rewards,
        "progression": progress
    }


# ============ HELPER FUNCTIONS ============

def _calculate_difficulty(chapter: int, stage: int, is_boss: bool, is_miniboss: bool) -> float:
    """Progressive difficulty scaling for 20 chapters"""
    if chapter <= 5:
        chapter_mult = 1.0 + (chapter - 1) * 0.3
    elif chapter <= 12:
        chapter_mult = 2.2 + (chapter - 5) * 0.5
    else:
        chapter_mult = 5.7 + (chapter - 12) * 0.8
    
    stage_mult = 1.0 + (stage - 1) * 0.08
    base_diff = chapter_mult * stage_mult
    
    if is_boss:
        return base_diff * 3.0
    elif is_miniboss:
        return base_diff * 2.0
    return base_diff


def _calculate_mob_count(stage: int, is_boss: bool, is_miniboss: bool, chapter: int) -> int:
    if is_boss:
        return 5  # Boss + 4 elite guards
    elif is_miniboss:
        return 3  # Mini-boss + 2 adds
    else:
        base_count = 8 + min(int((stage - 1) * 1.5), 6)
        chapter_bonus = min(int((chapter - 1) / 2.0), 6)
        return base_count + chapter_bonus


def _generate_mob_config(chapter: int, stage: int, difficulty: float, is_boss: bool, is_miniboss: bool) -> dict:
    """Generate mob configuration matching Godot client structure"""
    tier = min((chapter - 1) // 4, 4)
    
    mob_pools = [
        ["goblin", "wolf", "skeleton", "zombie", "bandit"],
        ["goblin_warrior", "orc", "dire_wolf", "giant_spider"],
        ["elite_goblin", "orc_berserker", "dark_mage", "death_knight"],
        ["orc_warlord", "archmage", "minotaur", "necromancer"],
        ["dragon_whelp", "lich", "demon_lord", "void_titan"]
    ]
    
    boss_mobs = ["goblin_king", "orc_overlord", "elder_dragon", "ancient_lich", "demon_lord"]
    
    if is_boss:
        mob_id = boss_mobs[min(tier, len(boss_mobs) - 1)]
        mob_name = mob_id.replace("_", " ").title() + " (BOSS)"
    elif is_miniboss:
        pool = mob_pools[min(tier, len(mob_pools) - 1)]
        mob_id = random.choice(pool)
        mob_name = mob_id.replace("_", " ").title() + " (Elite)"
    else:
        pool = mob_pools[min(tier, len(mob_pools) - 1)]
        mob_id = random.choice(pool)
        mob_name = mob_id.replace("_", " ").title()
    
    base_health = int(100 * difficulty)
    base_damage = int(10 * difficulty * 0.5)
    base_defense = int(5 * difficulty * 0.3)
    
    if is_boss:
        base_health *= 5
        base_damage = int(base_damage * 2.0)
        base_defense = int(base_defense * 2.0)
    elif is_miniboss:
        base_health *= 3
        base_damage = int(base_damage * 1.5)
        base_defense = int(base_defense * 1.5)
    
    mob_type = "melee"
    color = [0.8, 0.2, 0.2]
    
    if "mage" in mob_id or "lich" in mob_id or "necromancer" in mob_id:
        mob_type = "caster"
        color = [0.5, 0.2, 0.8]
    elif "archer" in mob_id or "spider" in mob_id:
        mob_type = "ranged"
        color = [0.2, 0.8, 0.2]
    elif "knight" in mob_id or "warlord" in mob_id or "overlord" in mob_id:
        mob_type = "tank"
        color = [0.3, 0.3, 0.8]
    
    if is_boss:
        color = [1.0, 0.1, 0.1]
    elif is_miniboss:
        color = [1.0, 0.5, 0.0]
    
    return {
        "mob_id": mob_id,
        "mob_name": mob_name,
        "mob_type": mob_type,
        "health": base_health,
        "damage": base_damage,
        "defense": base_defense,
        "magic_resistance": int(base_defense * 0.5),
        "speed": 80.0 + random.random() * 40.0,
        "attack_speed": 1.0 + random.random() * 0.5,
        "critical_chance": 0.05 + (chapter * 0.005),
        "critical_multiplier": 1.5,
        "dodge_chance": 0.02 + (chapter * 0.002),
        "attack_range": 50.0 if mob_type == "melee" else 150.0,
        "behavior_type": "aggressive",
        "aggro_range": 100.0 + (chapter * 5.0),
        "color": color,
        "size_scale": 1.5 if is_boss else (1.2 if is_miniboss else 1.0),
        "xp_reward": int(10 * difficulty * (5 if is_boss else (3 if is_miniboss else 1))),
        "gold_reward": int(5 * difficulty * (5 if is_boss else (3 if is_miniboss else 1))),
        "drop_chance": 0.5 if is_boss else (0.3 if is_miniboss else 0.1),
        "special_abilities": []
    }


def _calculate_chapter_rewards(chapter: int, stage: int) -> dict:
    """Calculate rewards matching Godot client structure"""
    is_boss = (stage % 10 == 0)
    items = []
    
    # Every stage gets 5 random gems
    for i in range(5):
        gem_type = "upgrade" if random.randint(0, 1) == 0 else "refine"
        items.append(_generate_gem_reward(gem_type, chapter))
    
    # Boss stages get legendary gear
    if is_boss:
        items.append(_generate_legendary_gear(chapter, stage))
    
    return {
        "gold": 1500,
        "gems": 50,
        "xp": 500,
        "items": items
    }


def _generate_gem_reward(gem_type: str, chapter: int) -> dict:
    tier_index = min(chapter // 5, 3)
    tier_names = ["common", "rare", "epic", "legendary"]
    tier = tier_names[tier_index]
    
    item_type = 3 if gem_type == "upgrade" else 4  # UPGRADE_GEM = 3, REFINE_GEM = 4
    
    return {
        "item_type": item_type,
        "id": f"gem_{gem_type}_{tier}_{random.randint(1000, 9999)}",
        "name": f"{tier.capitalize()} {gem_type.capitalize()} Gem",
        "rarity": tier_index,
        "gem_type": gem_type,
        "gem_tier": tier,
        "stack_size": 1,
        "price_gold": (tier_index + 1) * 100,
        "icon_path": "",
        "locked": False
    }


def _generate_legendary_gear(chapter: int, stage: int) -> dict:
    slot = random.randint(0, 11)
    slot_names = ["Weapon", "Helm", "Armor", "Pants", "Gloves", "Boots", "Ring", "Ring", "Necklace", "Bracelet", "Bracelet", "Wings"]
    
    stat_multiplier = 1.0 + (chapter * 0.3)
    base_stat = int(25 * stat_multiplier)
    
    return {
        "item_type": 0,  # GEAR
        "id": f"legendary_{chapter}_{stage}_{random.randint(1000, 9999)}",
        "name": f"Legendary {slot_names[slot]}",
        "rarity": 3,  # LEGENDARY
        "slot": slot,
        "required_class": -1,
        "required_level": max(1, chapter * 5),
        "set_id": 0,
        "atk": base_stat * 2 if slot == 0 else 0,
        "def": base_stat * 2 if slot != 0 else 0,
        "strength": base_stat,
        "agility": int(base_stat * 0.7),
        "energy": int(base_stat * 0.7),
        "vitality": int(base_stat * 0.8),
        "slot_attack": base_stat * 3 if slot in [0, 6, 7, 11] else 0,
        "slot_defense": base_stat * 3 if slot not in [0, 6, 7] else 0,
        "slot_combat_base": base_stat * 2,
        "price_gold": base_stat * 200,
        "price_gems": base_stat * 10,
        "bonus_stats": [],
        "upgrade_level": 0,
        "icon_path": "",
        "locked": False
    }


def _generate_mock_inventory(character_id: str) -> dict:
    """Generate mock inventory with potions, gems, and gear"""
    items = []
    
    # Potions
    items.append({
        "item_type": 1,  # CONSUMABLE
        "id": "health_potion_small_001",
        "name": "Health Potion (Small)",
        "rarity": 0,
        "potion_type": "health",
        "potion_size": "small",
        "restore_amount": 50,
        "restore_percent": 5,
        "cooldown": 10.0,
        "stack_size": 10,
        "price_gold": 10
    })
    
    # Upgrade Gems
    for rarity, tier in enumerate(["common", "rare", "epic", "legendary"]):
        items.append({
            "item_type": 3,  # UPGRADE_GEM
            "id": f"upgrade_gem_{tier}_001",
            "name": f"Upgrade Gem ({tier.capitalize()})",
            "rarity": rarity,
            "gem_type": "upgrade",
            "gem_tier": tier,
            "stack_size": 99 - (rarity * 20),
            "price_gold": (rarity + 1) * 50
        })
    
    # Refine Gems
    for rarity, tier in enumerate(["common", "rare", "epic", "legendary"]):
        items.append({
            "item_type": 4,  # REFINE_GEM
            "id": f"refine_gem_{tier}_001",
            "name": f"Refine Gem ({tier.capitalize()})",
            "rarity": rarity,
            "gem_type": "refine",
            "gem_tier": tier,
            "stack_size": 50 - (rarity * 10),
            "price_gold": (rarity + 1) * 75
        })
    
    # Generate equipped items based on character
    equipped_items = _generate_equipped_items(character_id)
    
    return {
        "capacity": 50,
        "items": items,
        "equipped_items": equipped_items
    }


def _generate_equipped_items(character_id: str) -> dict:
    """Generate equipped items for a character"""
    
    # Base empty equipped slots
    empty_equipped = {
        "weapon": {},
        "helm": {},
        "armor": {},
        "pants": {},
        "gloves": {},
        "boots": {},
        "ring1": {},
        "ring2": {},
        "bracelet1": {},
        "bracelet2": {},
        "necklace": {},
        "wings": {}
    }
    
    if character_id == "char_001":  # TestWarrior - fully equipped legendary
        return {
            "weapon": _create_gear_item("legendary_weapon_001", "Sword of the Eternal Guard", 0, 1, 100, 3, 835, 0, 145, 25, 22, 20, 24, 13),
            "helm": _create_gear_item("legendary_helm_001", "Eternal Crown of the Dragon King", 1, 1, 100, 3, 0, 486, 72, 24, 21, 20, 25, 13),
            "armor": _create_gear_item("legendary_armor_001", "Eternal Dragonscale Chestplate", 2, 1, 100, 3, 0, 489, 75, 25, 23, 21, 25, 13),
            "pants": _create_gear_item("legendary_pants_001", "Eternal Dragonscale Greaves", 3, 1, 100, 3, 0, 484, 70, 24, 25, 20, 23, 13),
            "gloves": _create_gear_item("legendary_gloves_001", "Eternal Dragonscale Gauntlets", 4, 1, 100, 3, 0, 482, 68, 25, 24, 20, 23, 13),
            "boots": _create_gear_item("legendary_boots_001", "Eternal Dragonscale Sabatons", 5, 1, 100, 3, 0, 486, 72, 23, 25, 21, 24, 13),
            "ring1": _create_gear_item("legendary_ring1_001", "Ring of Eternal Might", 6, 1, 100, 3, 440, 0, 72, 25, 22, 20, 24, 13),
            "ring2": _create_gear_item("legendary_ring2_001", "Ring of Eternal Power", 7, 1, 100, 3, 443, 0, 75, 24, 23, 21, 25, 13),
            "bracelet1": _create_gear_item("legendary_bracelet1_001", "Bracelet of the Titan", 8, 1, 100, 3, 0, 438, 70, 24, 21, 20, 25, 13),
            "bracelet2": _create_gear_item("legendary_bracelet2_001", "Bracelet of the Warlord", 9, 1, 100, 3, 0, 440, 72, 25, 23, 21, 24, 13),
            "necklace": _create_gear_item("legendary_necklace_001", "Pendant of the Dragon's Heart", 10, 1, 100, 3, 0, 488, 74, 24, 22, 23, 25, 13),
            "wings": _create_gear_item("legendary_wings_001", "Wings of the Eternal Warlord", 11, 1, 100, 3, 440, 438, 70072, 25, 24, 21, 25, 13),
        }
    elif character_id == "char_002":  # TestMage - partially equipped
        return {
            "weapon": {},
            "helm": {},
            "armor": _create_gear_item("mage_robe_001", "Arcane Robe", 2, 0, 10, 1, 0, 10, 8, 0, 0, 4, 3, 1),
            "pants": {},
            "gloves": {},
            "boots": _create_gear_item("mage_boots_001", "Boots of the Archmage", 5, 0, 15, 3, 0, 35, 15, 0, 5, 6, 5, 5),
            "ring1": _create_gear_item("mage_ring_001", "Ring of Wisdom", 6, 0, 12, 2, 19, 0, 10, 0, 4, 5, 0, 3),
            "ring2": {},
            "bracelet1": {},
            "bracelet2": {},
            "necklace": {},
            "wings": {}
        }
    
    return empty_equipped


def _create_gear_item(item_id: str, name: str, slot: int, required_class: int, required_level: int, 
                      rarity: int, slot_attack: int, slot_defense: int, slot_combat_base: int,
                      strength: int, agility: int, energy: int, vitality: int, upgrade_level: int) -> dict:
    """Helper to create a gear item"""
    return {
        "item_type": 0,  # GEAR
        "id": item_id,
        "name": name,
        "rarity": rarity,
        "icon_path": "",
        "locked": False,
        "slot": slot,
        "required_class": required_class,
        "required_level": required_level,
        "set_id": 0,
        "atk": 0,
        "def": 0,
        "strength": strength,
        "agility": agility,
        "energy": energy,
        "vitality": vitality,
        "slot_attack": slot_attack,
        "slot_defense": slot_defense,
        "slot_combat_base": slot_combat_base,
        "price_gold": required_level * 100,
        "price_gems": required_level * 5,
        "bonus_stats": [],
        "upgrade_level": upgrade_level
    }


# ============ INVENTORY ACTION HELPERS ============

def _get_or_create_inventory(character_id: str) -> dict:
    """Get persistent inventory or create from mock data"""
    if character_id not in MOCK_INVENTORIES:
        MOCK_INVENTORIES[character_id] = _generate_mock_inventory(character_id)
    return MOCK_INVENTORIES[character_id]


def _find_item_in_inventory(inventory: dict, item_id: str) -> Optional[dict]:
    """Find an item in the inventory items list by ID"""
    for item in inventory.get("items", []):
        if item.get("id") == item_id:
            return item
    return None


def _find_item_in_equipped(inventory: dict, item_id: str) -> Optional[tuple]:
    """Find an item in equipped slots. Returns (slot_name, item) or None"""
    equipped = inventory.get("equipped_items", {})
    for slot_name, item in equipped.items():
        if item and item.get("id") == item_id:
            return (slot_name, item)
    return None


def _remove_item_from_inventory(inventory: dict, item_id: str) -> Optional[dict]:
    """Remove an item from inventory items list. Returns the removed item or None"""
    items = inventory.get("items", [])
    for i, item in enumerate(items):
        if item.get("id") == item_id:
            return items.pop(i)
    return None


def _validate_and_apply_action(inventory: dict, action: InventoryAction, character_id: str) -> ActionResult:
    """Validate and apply a single inventory action"""
    action_type = action.action.lower()
    
    if action_type == "equip":
        return _action_equip(inventory, action, character_id)
    elif action_type == "unequip":
        return _action_unequip(inventory, action)
    elif action_type == "discard":
        return _action_discard(inventory, action)
    elif action_type == "lock":
        return _action_lock(inventory, action, True)
    elif action_type == "unlock":
        return _action_lock(inventory, action, False)
    elif action_type == "equip_potion":
        return _action_equip_potion(inventory, action, character_id)
    else:
        return ActionResult(success=False, error=f"Unknown action type: {action_type}")


def _action_equip(inventory: dict, action: InventoryAction, character_id: str) -> ActionResult:
    """Equip an item from inventory to an equipment slot"""
    # Validate required fields
    if not action.item_id:
        return ActionResult(success=False, error="item_id is required for equip action")
    if action.slot_id is None:
        return ActionResult(success=False, error="slot_id is required for equip action")
    
    # Validate slot_id range
    if action.slot_id not in SLOT_ID_TO_NAME:
        return ActionResult(success=False, error=f"Invalid slot_id: {action.slot_id}")
    
    # Find item in inventory
    item = _find_item_in_inventory(inventory, action.item_id)
    if not item:
        return ActionResult(success=False, error="Item not found in inventory")
    
    # Validate item is gear type (not potion/gem)
    item_type = item.get("item_type", -1)
    if item_type != ITEM_TYPE_GEAR:
        return ActionResult(success=False, error="Item is not equippable gear")
    
    # Validate item's slot matches requested slot_id
    item_slot = item.get("slot", -1)
    # Handle rings and bracelets which can go in either slot
    valid_slots = [action.slot_id]
    if action.slot_id in [6, 7]:  # ring1, ring2
        valid_slots = [6, 7]
    elif action.slot_id in [8, 9]:  # bracelet1, bracelet2
        valid_slots = [8, 9]
    
    if item_slot not in valid_slots:
        return ActionResult(success=False, error=f"Item slot ({item_slot}) does not match requested slot ({action.slot_id})")
    
    slot_name = SLOT_ID_TO_NAME[action.slot_id]
    equipped_items = inventory.setdefault("equipped_items", {})
    
    # If slot is occupied, move current item to inventory
    current_equipped = equipped_items.get(slot_name)
    if current_equipped and current_equipped.get("id"):
        inventory["items"].append(current_equipped)
    
    # Remove item from inventory and equip it
    _remove_item_from_inventory(inventory, action.item_id)
    equipped_items[slot_name] = item
    
    return ActionResult(success=True)


def _action_unequip(inventory: dict, action: InventoryAction) -> ActionResult:
    """Unequip an item from equipment slot to inventory"""
    # Validate required fields
    if action.slot_id is None:
        return ActionResult(success=False, error="slot_id is required for unequip action")
    
    # Validate slot_id range
    if action.slot_id not in SLOT_ID_TO_NAME:
        return ActionResult(success=False, error=f"Invalid slot_id: {action.slot_id}")
    
    slot_name = SLOT_ID_TO_NAME[action.slot_id]
    equipped_items = inventory.get("equipped_items", {})
    
    # Check if slot has an item
    current_item = equipped_items.get(slot_name)
    if not current_item or not current_item.get("id"):
        return ActionResult(success=False, error=f"No item equipped in slot {slot_name}")
    
    # Check inventory capacity
    items = inventory.get("items", [])
    capacity = inventory.get("capacity", 50)
    if len(items) >= capacity:
        return ActionResult(success=False, error="Inventory is full")
    
    # Move item to inventory
    inventory["items"].append(current_item)
    equipped_items[slot_name] = {}
    
    return ActionResult(success=True)


def _action_discard(inventory: dict, action: InventoryAction) -> ActionResult:
    """Discard an item from inventory permanently"""
    # Validate required fields
    if not action.item_id:
        return ActionResult(success=False, error="item_id is required for discard action")
    
    # Find item in inventory
    item = _find_item_in_inventory(inventory, action.item_id)
    if not item:
        return ActionResult(success=False, error="Item not found in inventory")
    
    # Check if item is locked
    if item.get("locked", False):
        return ActionResult(success=False, error="Cannot discard locked item")
    
    # Remove item
    _remove_item_from_inventory(inventory, action.item_id)
    
    return ActionResult(success=True)


def _action_lock(inventory: dict, action: InventoryAction, lock_value: bool) -> ActionResult:
    """Lock or unlock an item (in inventory or equipped)"""
    # Validate required fields
    if not action.item_id:
        return ActionResult(success=False, error=f"item_id is required for {'lock' if lock_value else 'unlock'} action")
    
    # Try to find in inventory first
    item = _find_item_in_inventory(inventory, action.item_id)
    if item:
        item["locked"] = lock_value
        return ActionResult(success=True)
    
    # Try to find in equipped items
    equipped_result = _find_item_in_equipped(inventory, action.item_id)
    if equipped_result:
        slot_name, item = equipped_result
        item["locked"] = lock_value
        return ActionResult(success=True)
    
    return ActionResult(success=False, error="Item not found")


def _action_equip_potion(inventory: dict, action: InventoryAction, character_id: str) -> ActionResult:
    """Equip a potion to health or mana slot"""
    # Validate required fields
    if not action.item_id:
        return ActionResult(success=False, error="item_id is required for equip_potion action")
    if not action.potion_type:
        return ActionResult(success=False, error="potion_type is required for equip_potion action")
    if action.potion_type not in ["health", "mana"]:
        return ActionResult(success=False, error="potion_type must be 'health' or 'mana'")
    
    # Find item in inventory
    item = _find_item_in_inventory(inventory, action.item_id)
    if not item:
        return ActionResult(success=False, error="Item not found in inventory")
    
    # Validate item is consumable type
    item_type = item.get("item_type", -1)
    if item_type != ITEM_TYPE_CONSUMABLE:
        return ActionResult(success=False, error="Item is not a consumable")
    
    # Update potions in inventory
    potions = inventory.setdefault("potions", {
        "health_potion": None,
        "mana_potion": None,
        "health_slot_id": "",
        "mana_slot_id": ""
    })
    
    if action.potion_type == "health":
        potions["health_potion"] = item
        potions["health_slot_id"] = action.item_id
    else:
        potions["mana_potion"] = item
        potions["mana_slot_id"] = action.item_id
    
    # Also update character data if available
    if character_id in MOCK_CHARACTERS:
        MOCK_CHARACTERS[character_id]["potions"] = potions
    
    return ActionResult(success=True)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
