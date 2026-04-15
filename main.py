import sys
import os
import pygame
from src.engine.game_state import StateManager

# ── Portable path fix (PyInstaller .exe support) ─────────────────────────────
# When running as a frozen exe, sys._MEIPASS points to the extracted bundle
# (read-only assets). We add it to sys.path so imports work, but keep cwd
# pointing to the folder NEXT TO the .exe so data/ saves are persistent.
if getattr(sys, 'frozen', False):
    bundle_dir = sys._MEIPASS
    exe_dir    = os.path.dirname(sys.executable)
    sys.path.insert(0, bundle_dir)
    os.chdir(exe_dir)          # saves go next to the .exe, not in temp
from src.graphics import styles

# Configuration
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
FPS = 60

def main():
    # Initialize Pygame
    pygame.init()
    
    # Set up the physical window
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("War Brawl Arena II - Retro Edition")
    
    # Set up the base virtual surface (Pixel Perfect)
    base_surf = pygame.Surface((styles.BASE_WIDTH, styles.BASE_HEIGHT))
    
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
        # Scale mouse events for the base surface
        scaled_events = []
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            
            # Adjust mouse position for logic
            if hasattr(event, "pos"):
                # Simple linear scaling
                nx = int(event.pos[0] * (styles.BASE_WIDTH / WINDOW_WIDTH))
                ny = int(event.pos[1] * (styles.BASE_HEIGHT / WINDOW_HEIGHT))
                # Create a new event object with adjusted pos for internal UI logic
                if event.type == pygame.MOUSEMOTION:
                    scaled_events.append(pygame.event.Event(pygame.MOUSEMOTION, {"pos": (nx, ny), "rel": event.rel, "buttons": event.buttons}))
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    scaled_events.append(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": (nx, ny), "button": event.button}))
                elif event.type == pygame.MOUSEBUTTONUP:
                    scaled_events.append(pygame.event.Event(pygame.MOUSEBUTTONUP, {"pos": (nx, ny), "button": event.button}))
            else:
                scaled_events.append(event)
        
        # 3. Update Current State (using scaled events for UI)
        state_manager.update(dt, scaled_events)
        
        # 4. Render to Base Surface
        base_surf.fill(styles.COLOR_BG)
        state_manager.draw(base_surf)
        
        # 5. Scale and Flip display
        # Use NEAREST NEIGHBOR (default behavior of scale if not smoothscale) for Pixel Perfect look
        scaled_surf = pygame.transform.scale(base_surf, (WINDOW_WIDTH, WINDOW_HEIGHT))
        screen.blit(scaled_surf, (0, 0))
        pygame.display.flip()
        
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
