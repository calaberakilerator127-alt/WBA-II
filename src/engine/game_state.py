import pygame

class GameState:
    """Base class for all game states."""
    def __init__(self, manager):
        self.manager = manager

    def handle_events(self, events):
        pass

    def update(self, dt, events):
        pass

    def draw(self, screen):
        pass

class StateManager:
    """Manages switching between different game states."""
    def __init__(self, manager=None):
        self.states = {
            "menu": MenuState(self),
            "battle": BattleState(self)
        }
        self.current_state = self.states["menu"]

    def update(self, dt, events):
        self.current_state.update(dt, events)

    def draw(self, screen):
        self.current_state.draw(screen)

    def change_state(self, state_name):
        if state_name in self.states:
            self.current_state = self.states[state_name]

class MenuState(GameState):
    def __init__(self, manager):
        super().__init__(manager)
        self.font = pygame.font.SysFont("Arial", 64)
        self.text = self.font.render("WBA II - Retro Wrestling", True, (255, 255, 255))
        self.sub_text = pygame.font.SysFont("Arial", 32).render("Presiona ESPACIO para empezar", True, (200, 200, 200))

    def update(self, dt, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.manager.change_state("battle")

    def draw(self, screen):
        screen.blit(self.text, (screen.get_width() // 2 - self.text.get_width() // 2, 200))
        screen.blit(self.sub_text, (screen.get_width() // 2 - self.sub_text.get_width() // 2, 400))

from src.entities.fighter import Fighter

class BattleState(GameState):
    def __init__(self, manager):
        super().__init__(manager)
        # Initialize two fighters
        self.p1 = Fighter("Alexander", (300, 500), is_player_1=True)
        self.p2 = Fighter("Angelica", (900, 500), is_player_1=False)
        self.fighters = pygame.sprite.Group(self.p1, self.p2)

    def update(self, dt, events):
        keys = pygame.key.get_pressed()
        self.p1.handle_input(keys)
        # Placeholder for AI or P2 input
        # self.p2.handle_input(...) 
        
        self.fighters.update(dt)

    def draw(self, screen):
        # Draw a simple ground for now
        pygame.draw.rect(screen, (50, 50, 50), (0, 600, 1280, 120))
        self.fighters.draw(screen)

