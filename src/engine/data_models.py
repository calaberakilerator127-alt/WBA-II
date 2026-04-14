from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class StatusEffect(BaseModel):
    name: str # e.g., "Envenenado", "Quemado", "Congelado", "Protegido"
    type: str # "dot" (damage over time), "stun", "debuff", "buff", "regen", "lifesteal", "thorns"
    value: float # Damage per turn, accuracy penalty %, resistance boost %, etc.
    duration: int # Turns remaining
    stacks: int = 1 # Current stack count (max 5)
    element: Optional[str] = None

class Move(BaseModel):
    name: str
    type: str # "Fisico" or "Magico"
    cost: int
    base_damage: int
    multiplier: float = 1.0
    recoil: float = 0.0
    penetration: float = 0.0
    element: Optional[str] = None
    effect: Optional[StatusEffect] = None # Added for specialization

class FighterStats(BaseModel):
    fuerza: int = 10
    poder: int = 10
    velocidad: int = 10
    resistencia_fisica: int = 5
    resistencias_elementales: Dict[str, float] = {}
    estamina_max: int = 100
    energia_max: int = 100
    equilibrio_max: int = 100

class FighterProfile(BaseModel):
    id: str
    name: str
    stats: FighterStats
    moves: List[Move] = []
    level: int = 1
    xp: int = 0
    hp: float = 100.0
    max_hp: float = 100.0
    sprite_path: Optional[str] = None
    portrait_path: Optional[str] = None
    avatar_path: Optional[str] = None # Profile icon path
    entrance_theme: Optional[str] = None # Unique intro music
    hype: float = 0.0
    equilibrio: float = 100.0
    estamina: float = 100.0
    energia: float = 100.0
    status_effects: List[StatusEffect] = [] # Track active effects
    stat_points: int = 0 # Points to spend on Fuerza, Poder, Velocidad
    hospital_fianza: int = 0
    is_recovering: bool = False
    usage_count: int = 0
    biography: str = "Un valiente luchador de la arena."
    elemental_affinity: str = "Neutral"

class Account(BaseModel):
    username: str
    real_name: str = ""
    password: str
    avatar_path: str = "assets/images/profile/masculino/Amsterdam.png"
    settings: Dict[str, float] = {"master_vol": 0.5, "music_vol": 0.5, "sfx_vol": 0.5, "fullscreen": 0}
    key_bindings: Dict[str, int] = {
        "UP": 1073741906, "DOWN": 1073741905, "LEFT": 1073741904, "RIGHT": 1073741903,
        "CONFIRM": 13, "BACK": 27, "TRAIN": 32, "STATS": 9
    }
    brawels: int = 500
    puntos: int = 0
    fighters: List[FighterProfile] = []
    inventory: Dict[str, int] = {}
    inventory_max: int = 10
    wins: int = 0
    losses: int = 0
    mvp_count: int = 0
    total_damage_dealt: int = 0
