import pygame
import time
from src.engine.data_manager import DataManager

# State Imports (Imported here to be accessible to the dynamic loader)
from src.engine.states.login_state import LoginState
from src.engine.states.registration_state import RegistrationState
from src.engine.states.menu_state import MenuState
from src.engine.states.battle_state import BattleState
from src.engine.states.gym_state import GymState
from src.engine.states.hospital_state import HospitalState
from src.engine.states.lab_state import LabState
from src.engine.states.adjustments_state import AdjustmentsState
from src.engine.states.stage_select_state import StageSelectState
from src.engine.states.mode_config_state import ModeConfigState
from src.engine.states.profile_state import ProfileState
from src.engine.states.battle_intro_state import BattleIntroState
from src.engine.states.team_select_state import TeamSelectState
from src.engine.states.inventory_state import InventoryState
from src.engine.states.roster_state import RosterState
from src.engine.states.char_select_state import CharacterSelectState
from src.engine.states.shop_state import ShopState
from src.engine.states.pause_state import PauseState
from src.engine.states.p2_access_state import P2AccessState

class GameState:
    """Base interface for all game states."""
    def __init__(self, manager):
        self.manager = manager
    def update(self, dt, events): pass
    def draw(self, screen): pass

class StateManager:
    """Handles the lifecycle and transitions of game states with Lazy Loading."""
    def __init__(self):
        self.data_manager = DataManager()
        self.selected_stage = "Callejero"
        self.current_mode = "LUCHA"
        self.combat_config = {
            "rounds": 1,
            "team_size": 1,
            "is_deathmatch": False,
            "mode": "LUCHA"
        }
        self.selected_team = []
        self.selected_team_p2 = []
        self.selected_fighter_idx = 0
        
        # State Map (Maps name to Class for Lazy Loading)
        self.state_classes = {
            "login": LoginState,
            "register": RegistrationState,
            "settings": AdjustmentsState,
            "menu": MenuState,
            "stage_select": StageSelectState,
            "char_select": CharacterSelectState,
            "battle": BattleState,
            "battle_intro": BattleIntroState,
            "gym": GymState,
            "hospital": HospitalState,
            "lab": LabState,
            "mode_config": ModeConfigState,
            "profile": ProfileState,
            "team_select": TeamSelectState,
            "inventory": InventoryState,
            "roster": RosterState,
            "market": CharacterSelectState,
            "shop": ShopState,
            "p2_access": P2AccessState
        }
        
        # Currently active state
        self.current_state_name = "login"
        self.current_state = self.state_classes["login"](self)
        
        # Transition properties
        self.transitioning = False
        self.fade_alpha = 0
        self.fade_speed = 300
        self.next_state_name = None
        
        # Overlay for Pausing
        self.overlay = None
        
        # State Stack for persistent navigation
        self.state_stack = [] 
        self.is_popping = False

    def change_state(self, state_name):
        """Triggers a smooth fade-out before switching states."""
        if state_name not in self.state_classes:
            print(f"Error: State '{state_name}' not found.")
            return
            
        if self.transitioning: return
        self.next_state_name = state_name
        self.is_popping = False
        self.transitioning = True

    def push_state(self, state_name):
        """Saves current state and pushes a new one onto the stack."""
        if self.transitioning: return
        self.state_stack.append((self.current_state_name, self.current_state))
        self.change_state(state_name)

    def pop_state(self):
        """Returns to the previous state on the stack."""
        if not self.state_stack or self.transitioning: return
        self.is_popping = True
        self.transitioning = True

    def actual_change_state(self, state_name):
        """Performs the actual lazy-loading of the state."""
        print(f"[StateManager] Loading state: {state_name}")
        state_class = self.state_classes[state_name]
        self.current_state = state_class(self)
        self.current_state_name = state_name

    def update(self, dt, events):
        # Handle Fade Transition Logic
        if self.transitioning:
            self.fade_alpha += self.fade_speed * dt
            if self.fade_alpha >= 255:
                self.fade_alpha = 255
                if self.is_popping:
                    name, inst = self.state_stack.pop()
                    self.current_state_name = name
                    self.current_state = inst
                else:
                    self.actual_change_state(self.next_state_name)
                self.transitioning = False
        else:
            if self.fade_alpha > 0:
                self.fade_alpha -= self.fade_speed * dt
                if self.fade_alpha < 0: self.fade_alpha = 0

        # Handle Pause Overlay
        if self.overlay:
            self.overlay.update(dt, events)
            return # Block updates to background state

        # Passive Regen
        self.data_manager.update_regen(dt)

        # Global Pause Trigger (If not on login/register)
        if self.current_state_name not in ["login", "register"]:
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == self.data_manager.get_key("BACK"):
                        self.overlay = PauseState(self)
                        return

        # Update current state with safety check
        if self.current_state:
            self.current_state.update(dt, events)

    def draw(self, screen):
        if self.current_state:
            self.current_state.draw(screen)
            
        if self.overlay:
            self.overlay.draw(screen)
            
        if self.fade_alpha > 0:
            fade_surf = pygame.Surface((480, 270), pygame.SRCALPHA)
            fade_surf.fill((0, 0, 0, int(self.fade_alpha)))
            screen.blit(fade_surf, (0, 0))
