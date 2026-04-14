import pygame

class Animator:
    """Handles animations for a fighter."""
    def __init__(self, spritesheet_path):
        self.spritesheet = pygame.image.load(spritesheet_path).convert_alpha()
        self.frames = []
        # For now, assume a single frame if no data is provided
        self.frames.append(self.spritesheet)
        self.current_frame = 0
        self.animation_timer = 0
        self.animation_speed = 0.1  # Seconds per frame

    def set_frames(self, frame_coords):
        """
        frame_coords: List of (x, y, w, h)
        """
        self.frames = []
        for coord in frame_coords:
            rect = pygame.Rect(coord)
            frame = self.spritesheet.subsurface(rect)
            self.frames.append(frame)

    def update(self, dt):
        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            self.current_frame = (self.current_frame + 1) % len(self.frames)

    def get_current_frame(self):
        return self.frames[self.current_frame]

class Fighter(pygame.sprite.Sprite):
    """Base class for all fighters."""
    def __init__(self, name, position, is_player_1=True):
        super().__init__()
        self.name = name
        self.pos = pygame.Vector2(position)
        self.is_player_1 = is_player_1
        
        # Initial State
        self.state = "idle"
        self.velocity = pygame.Vector2(0, 0)
        
        # Load assets
        # Note: In a larger game, we'd use a resource manager
        char_path = f"assets/images/characters/{name}.png"
        self.animator = Animator(char_path)
        
        self.image = self.animator.get_current_frame()
        self.rect = self.image.get_rect(center=self.pos)

    def handle_input(self, keys):
        if self.is_player_1:
            if keys[pygame.K_a]:
                self.velocity.x = -5
                self.state = "walking"
            elif keys[pygame.K_d]:
                self.velocity.x = 5
                self.state = "walking"
            else:
                self.velocity.x = 0
                self.state = "idle"

    def update(self, dt):
        self.pos += self.velocity
        self.rect.center = self.pos
        self.animator.update(dt)
        self.image = self.animator.get_current_frame()
        
        # Flip image if player 2
        if not self.is_player_1:
            self.image = pygame.transform.flip(self.image, True, False)

    def draw(self, screen):
        screen.blit(self.image, self.rect)
