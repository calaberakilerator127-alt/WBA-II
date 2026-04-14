import pygame
from src.graphics import styles
import random

class ParallaxLayer:
    """A single layer of a parallax background."""
    def __init__(self, image_path, speed_factor, scroll_type="horizontal"):
        self.image = pygame.image.load(image_path).convert_alpha()
        self.speed_factor = speed_factor
        self.scroll_type = scroll_type
        self.offset = 0
        
        # Scaling to base resolution
        self.image = pygame.transform.scale(self.image, (styles.BASE_WIDTH, styles.BASE_HEIGHT))

    def update(self, dt, camera_pos):
        # The layer moves proportional to the camera but at its own factor
        self.offset = (camera_pos * self.speed_factor) % styles.BASE_WIDTH

    def draw(self, surface):
        # Draw twice to create seamless loop
        surface.blit(self.image, (-self.offset, 0))
        surface.blit(self.image, (styles.BASE_WIDTH - self.offset, 0))

class Stage:
    """Combines multiple parallax layers and environmental hazards."""
    def __init__(self, name, layer_paths=None):
        self.name = name
        if layer_paths is None:
            # Fallback for single image stages
            layer_paths = [f"assets/images/scene/{name}.png"]
            
        self.layers = [
            ParallaxLayer(path, (i + 1) * 0.2) 
            for i, path in enumerate(layer_paths)
        ]
        self.hazards = []
        self.hazard_timer = 0
        
    def spawn_hazard(self):
        """Randomly triggers an environmental effect."""
        hazards = ["lightning"] # "puddle", "wind" can be added later
        self.last_hazard = random.choice(hazards)
        return self.last_hazard

    def check_hazard_trigger(self):
        """Returns the triggered hazard to the state manager."""
        if hasattr(self, "pending_hazard"):
            h = self.pending_hazard
            del self.pending_hazard
            return h
        return None

    def update(self, dt, camera_pos):
        for layer in self.layers:
            layer.update(dt, camera_pos)
            
        self.hazard_timer += dt
        if self.hazard_timer > 8.0: # Every 8 seconds
            if random.random() < 0.25: # 25% chance
                self.pending_hazard = self.spawn_hazard()
            self.hazard_timer = 0

    def draw(self, surface):
        for layer in self.layers:
            layer.draw(surface)
