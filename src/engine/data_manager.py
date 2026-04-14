import pygame
import os
import json
from typing import List, Dict, Optional
from src.engine.data_models import Account, FighterProfile

class SoundManager:
    """Manages preloading and playing of game SFX."""
    def __init__(self):
        self.sounds = {}
        self.load_common_sfx()

    def load_common_sfx(self):
        sfx_map = {
            "hover": "assets/sounds/sfx/hover.wav",
            "click": "assets/sounds/sfx/click.wav",
            "stat": "assets/sounds/sfx/cash.wav"
        }
        for name, path in sfx_map.items():
            if os.path.exists(path):
                self.sounds[name] = pygame.mixer.Sound(path)

    def play(self, name):
        if name in self.sounds:
            self.sounds[name].play()

class MusicManager:
    """Handles smooth background music transitions."""
    def __init__(self):
        self.current_track = None
        self.fade_time = 1000 # ms

    def play(self, path, loop=-1):
        if self.current_track == path:
            return
        
        if os.path.exists(path):
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.fadeout(self.fade_time)
                # We could use a timer to wait for fadeout, 
                # but pygame.mixer.music.load often interrupts immediately.
                # A better approach is to load after fade.
                pygame.time.delay(100) # Small delay for the fade to start
            
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(loop, fade_ms=self.fade_time)
            self.current_track = path

class DataManager:
    """Handles JSON persistence for accounts and game data."""
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.accounts_file = os.path.join(data_dir, "accounts.json")
        self.fighters_file = os.path.join(data_dir, "fighters_db.json")
        
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            
        self.active_p1 = None
        self.active_p2 = None
        self.sfx = SoundManager()
        self.music = MusicManager()

    def play_sfx(self, name):
        self.sfx.play(name)

    def play_music(self, path):
        self.music.play(path)

    def get_key(self, action: str, player=1) -> int:
        """Returns the bound key integer for a specific action."""
        if player == 1:
            defaults = {
                "UP": 1073741906, "DOWN": 1073741905, "LEFT": 1073741904, "RIGHT": 1073741903,
                "CONFIRM": 13, "BACK": 27, "TRAIN": 32, "STATS": 9
            }
            if self.active_p1 and action in self.active_p1.key_bindings:
                return self.active_p1.key_bindings[action]
            return defaults.get(action, 0)
        else:
            defaults = {
                "UP": 119, "DOWN": 115, "LEFT": 97, "RIGHT": 100, # W A S D
                "CONFIRM": 1073742049, "BACK": 122, "TRAIN": 120, "STATS": 99 # LSHIFT, Z, X, C
            }
            if self.active_p2 and action in self.active_p2.key_bindings:
                return self.active_p2.key_bindings[action]
            return defaults.get(action, 0)

        # print(f"Auto-saved: {account.username}")

    def save_active_account(self, is_p1=True):
        acc = self.active_p1 if is_p1 else self.active_p2
        if acc:
            self.save_account(acc)

    def save_account(self, account: Account):
        accounts = self.load_all_accounts()
        accounts[account.username] = account.dict()
        with open(self.accounts_file, "w", encoding="utf-8") as f:
            json.dump(accounts, f, indent=4)

    def load_all_accounts(self) -> dict:
        if os.path.exists(self.accounts_file):
            with open(self.accounts_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def login(self, username, password, is_p1=True):
        accounts = self.load_all_accounts()
        if username in accounts:
            acc_data = accounts[username]
            if acc_data["password"] == password:
                acc = Account(**acc_data)
                if is_p1:
                    self.active_p1 = acc
                else:
                    self.active_p2 = acc
                return acc
        return None

    def register(self, username, password):
        accounts = self.load_all_accounts()
        if username in accounts:
            return None # Already exists
        new_acc = Account(username=username, password=password)
        self.save_account(new_acc)
        return new_acc
    def distribute_rewards(self, stats_p1: dict, stats_p2: dict):
        """
        Distributes Brawels and XP based on performance.
        stats format: {"damage": int, "avg_hype": float, "winner": bool}
        """
        def calculate_brawels(s):
            base = 50 if s["winner"] else 20
            performance = (s["damage"] // 10) + int(s["avg_hype"] * 50)
            return base + performance

        if self.active_p1:
            gain = calculate_brawels(stats_p1)
            self.active_p1.brawels += gain
            self.active_p1.total_damage_dealt += stats_p1["damage"]
            if stats_p1["winner"]: self.active_p1.wins += 1
            else: self.active_p1.losses += 1
            self.save_active_account(is_p1=True)

        if self.active_p2:
            gain = calculate_brawels(stats_p2)
            self.active_p2.brawels += gain
            self.active_p2.total_damage_dealt += stats_p2["damage"] # Fixed typo
            if stats_p2["winner"]: self.active_p2.wins += 1
            else: self.active_p2.losses += 1
            self.save_active_account(is_p1=False)

    def create_default_fighter(self, name="Alexander"):
        from src.engine.data_models import FighterProfile, FighterStats, Move
        # A set of free starter moves
        starter_moves = [
            Move(name="Golpe Rápido", type="Fisico", cost=5, base_damage=15, multiplier=1.0),
            Move(name="Chispa Mágica", type="Magico", cost=10, base_damage=20, multiplier=1.1, element="Luz")
        ]
        
        # Check for entrance theme
        theme_path = f"assets/sounds/general/{name} - Tickets.mp3"
        theme = theme_path if os.path.exists(theme_path) else None
        
        return FighterProfile(
            id=str(os.urandom(4).hex()),
            name=name,
            stats=FighterStats(),
            moves=starter_moves,
            entrance_theme=theme
        )

    def load_database(self) -> dict:
        """Loads the full attacks and items database."""
        path = r"data/database.json"
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def get_move_tier(self, move_cost: int) -> int:
        """Heuristic to determine move tier based on cost."""
        if move_cost <= 20: return 1   # Req Level 1
        if move_cost <= 40: return 2   # Req Level 5
        if move_cost <= 75: return 3   # Req Level 10
        return 4                        # Req Level 15

    def buy_move(self, account, fighter, move_data) -> dict:
        """
        Processes a move purchase.
        Returns {"success": bool, "message": str, "needs_replace": bool}
        """
        from src.engine.data_models import Move
        # 1. Check money
        if account.brawels < move_data["cost"]:
            return {"success": False, "message": "Brawels insuficientes"}
        
        # 2. Check level
        tier = self.get_move_tier(move_data["cost"])
        req_lv = {1: 1, 2: 5, 3: 10, 4: 15}[tier]
        if fighter.level < req_lv:
            return {"success": False, "message": f"Nivel insuficiente (Req Lv.{req_lv})"}
        
        # 3. Check duplicate
        if any(m.name == move_data["name"] for m in fighter.moves):
            return {"success": False, "message": "Ya tienes este movimiento"}
        
        # 4. Finalize purchase
        account.brawels -= move_data["cost"]
        new_move = Move(**move_data)
        fighter.moves.append(new_move)
        self.save_account(account)
        return {"success": True, "message": f"¡{new_move.name} comprado con éxito!"}
    def add_xp(self, account, fighter, amount: int) -> bool:
        """Adds XP to a fighter and handles level-ups. Returns True if leveled up."""
        fighter.xp += amount
        leveled_up = False
        
        # Linear progression: Lv1 -> 50, Lv2 -> 100, etc.
        req_xp = fighter.level * 50
        while fighter.xp >= req_xp:
            fighter.xp -= req_xp
            fighter.level += 1
            fighter.stat_points += 5
            leveled_up = True
            # Max recovery on level up
            fighter.hp = fighter.max_hp
            fighter.estamina = fighter.stats.estamina_max
            fighter.energia = fighter.stats.energia_max
            req_xp = fighter.level * 50
            
        self.save_account(account)
        return leveled_up

    def assign_stat(self, account, fighter, stat_name: str) -> bool:
        """Spends 1 stat point to increase a base stat by 1."""
        if fighter.stat_points <= 0: return False
        
        if stat_name == "fuerza": fighter.stats.fuerza += 1
        elif stat_name == "poder": fighter.stats.poder += 1
        elif stat_name == "velocidad": fighter.stats.velocidad += 1
        else: return False
        
        fighter.stat_points -= 1
        self.save_account(account)
        return True

    def use_item(self, account, fighter, item_name: str) -> dict:
        """
        Consumes an item from inventory and applies its effect to a fighter.
        Returns {"success": bool, "message": str}
        """
        if item_name not in account.inventory or account.inventory[item_name] <= 0:
            return {"success": False, "message": "No tienes este objeto"}
            
        # Define Effects (Matching database.json types)
        applied = False
        msg = ""
        
        if "Proteína" in item_name:
            fighter.stats.fuerza += 5
            applied = True
            msg = "¡Fuerza aumentada +5!"
        elif "Energizante" in item_name:
            fighter.stats.energia_max += 25
            fighter.energia = fighter.stats.energia_max
            applied = True
            msg = "¡Energía Máx aumentada +25!"
        elif "Botiquín" in item_name:
            fighter.hp = fighter.max_hp
            applied = True
            msg = "¡Vida restaurada al 100%!"
        
        if applied:
            account.inventory[item_name] -= 1
            if account.inventory[item_name] <= 0:
                del account.inventory[item_name]
            self.save_account(account)
            return {"success": True, "message": f"{item_name} usado. {msg}"}
        
        return {"success": False, "message": "Este objeto no se puede usar así"}

    def update_regen(self, dt: float):
        """Passive recovery of stamina and energy while in menus."""
        if not self.active_p1: return
        
        # Regen 1 unit per 2 seconds
        regen_val = 0.5 * dt
        for f in self.active_p1.fighters:
            if f.estamina < f.stats.estamina_max:
                f.estamina = min(f.stats.estamina_max, f.estamina + regen_val)
            if f.energia < f.stats.energia_max:
                f.energia = min(f.stats.energia_max, f.energia + regen_val)
