import sys
import pygame
from src.engine.game_state import StateManager

# Configuration
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

def main():
    # Initialize Pygame
    pygame.init()
    
    # Set up the display
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("War Brawl Arena II")
    
    # Clock for controlling the frame rate
    clock = pygame.time.Clock()
    
    # Initialize the State Manager
    state_manager = StateManager()
    
    # Main game loop
    running = True
    while running:
        # 1. Delta Time
        dt = clock.tick(FPS) / 1000.0  # seconds
        
        # 2. Event Handling
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            
        # 3. Update Current State
        state_manager.update(dt, events)
        
        # 4. Render Current State
        screen.fill((0, 0, 0))  # Clear screen
        state_manager.draw(screen)
        
        # 5. Flip display
        pygame.display.flip()
        
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
