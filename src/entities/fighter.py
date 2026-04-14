import pygame

class Animator:
    """Handles character animations and spritesheet slicing."""
    def __init__(self, spritesheet_path, team_color=(255, 0, 255)):
        try:
            self.spritesheet = pygame.image.load(spritesheet_path).convert_alpha()
        except FileNotFoundError:
            # Styled Silhouette Placeholder
            self.spritesheet = pygame.Surface((96, 96), pygame.SRCALPHA)
            # Draw rounded body
            pygame.draw.ellipse(self.spritesheet, (30, 30, 30), (20, 10, 56, 76))
            # Draw head
            pygame.draw.circle(self.spritesheet, (30, 30, 30), (48, 25), 18)
            # Team Outline Glow
            pygame.draw.ellipse(self.spritesheet, team_color, (20, 10, 56, 76), 2)
            pygame.draw.circle(self.spritesheet, team_color, (48, 25), 18, 2)
            
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
    """Base class for all fighters, integrated with FighterProfile."""
    def __init__(self, profile, position, is_player_1=True):
        super().__init__()
        self.profile = profile # FighterProfile instance
        self.name = profile.name
        self.pos = pygame.Vector2(position)
        self.is_player_1 = is_player_1
        
        # Current Combat Stats
        self.hp = profile.hp
        self.max_hp = profile.max_hp
        self.estamina = profile.estamina
        self.energia = profile.energia
        self.hype = profile.hype
        self.equilibrio = profile.equilibrio
        
        # State & Movement
        self.state = "idle"
        self.velocity = pygame.Vector2(0, 0)
        
        # Team Color (Blue for P1, Red for Rivals)
        from src.graphics import styles
        self.team_color = styles.COLOR_ACCENT if is_player_1 else styles.COLOR_PRIMARY
        
        # Load assets
        char_path = profile.sprite_path if hasattr(profile, 'sprite_path') and profile.sprite_path else f"assets/images/characters/{self.name}.png"
        self.animator = Animator(char_path, self.team_color)
        
        self.image = self.animator.get_current_frame()
        self.rect = self.image.get_rect(center=self.pos)

    def handle_input(self, keys):
        # In Turn-Based, movement input might be limited or for dodging
        if self.is_player_1:
            if keys[pygame.K_a]:
                self.velocity.x = -2
                self.state = "walking"
            elif keys[pygame.K_d]:
                self.velocity.x = 2
                self.state = "walking"
            else:
                self.velocity.x = 0
                self.state = "idle"

    def update(self, dt):
        self.pos += self.velocity
        self.rect.center = self.pos
        self.animator.update(dt)
        self.image = self.animator.get_current_frame()
        
        if not self.is_player_1:
            self.image = pygame.transform.flip(self.image, True, False)

    def draw(self, screen):
        # Draw Shadow
        shadow_rect = pygame.Rect(0, 0, 60, 10)
        shadow_rect.center = (self.pos.x, self.rect.bottom - 5)
        shadow_surf = pygame.Surface((60, 10), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 80), (0, 0, 60, 10))
        screen.blit(shadow_surf, shadow_rect)
        
        screen.blit(self.image, self.rect)
