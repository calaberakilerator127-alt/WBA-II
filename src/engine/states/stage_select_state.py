import pygame
import math
from src.graphics import styles
from src.graphics.ui_system import PixelButton
from src.utils.localization import lang

class StageSelectState:
    """
    Arena Selection — Choose the battle environment.
    Visual stage preview framing with parallax/glow.
    """
    def __init__(self, manager):
        self.manager = manager
        self._time   = 0.0

        self.stages = [
            "Callejero", "Botado", "Cavernas", "Clasico", "Cosmico", 
            "Desertico", "Estudio", "Futurista", "Galactico", "Monumental"
        ]
        self.selected_idx  = 0
        self.preview_cache = {}

        for name in self.stages:
            path = f"assets/images/scene/{name}.png"
            try:
                img = pygame.image.load(path).convert()
                self.preview_cache[name] = pygame.transform.scale(img, (styles.BASE_WIDTH - 80, 140))
            except Exception:
                pass

        # Smooth Music
        manager.data_manager.play_music(r"assets/sounds/general/Men - Seleccion de escenario.mp3")

        self.btn_back  = PixelButton(manager, "← VOLVER", (8, 8), size=(70, 22),
                                     callback=lambda: manager.change_state("menu"),
                                     variant="ghost")
        self.btn_start = PixelButton(manager, "INICIAR COMBATE",
                                     (styles.BASE_WIDTH - 130, styles.BASE_HEIGHT - 38),
                                     size=(120, 30), callback=self.start_battle,
                                     variant="primary")
        self.btn_prev  = PixelButton(manager, "◄", (12, 120), size=(22, 30),
                                     callback=lambda: self.shift(-1), variant="ghost")
        self.btn_next  = PixelButton(manager, "►", (styles.BASE_WIDTH - 34, 120),
                                     size=(22, 30), callback=lambda: self.shift(1), variant="ghost")

    def shift(self, delta):
        self.selected_idx = (self.selected_idx + delta) % len(self.stages)
        self.manager.data_manager.play_sfx("hover")

    def start_battle(self):
        self.manager.selected_stage = self.stages[self.selected_idx]
        acc = self.manager.data_manager.active_p1
        if not acc or not acc.fighters:
            self.manager.change_state("char_select")
        else:
            self.manager.change_state("battle_intro")

    def update(self, dt, events):
        self._time += dt
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:    self.shift(1)
                elif event.key == pygame.K_LEFT:   self.shift(-1)
                elif event.key == pygame.K_RETURN:
                    self.manager.data_manager.play_sfx("click")
                    self.start_battle()
                elif event.key == pygame.K_ESCAPE:
                    self.manager.change_state("menu")
            
            self.btn_back.handle_event(event)
            self.btn_start.handle_event(event)
            self.btn_prev.handle_event(event)
            self.btn_next.handle_event(event)
            
        self.btn_back.update(dt)
        self.btn_start.update(dt)
        self.btn_prev.update(dt)
        self.btn_next.update(dt)

    def draw(self, screen):
        screen.fill(styles.COLOR_BG)
        styles.draw_scanlines(screen, alpha=16)
        
        # Header
        styles.draw_header(screen, "SELECCIÓN DE ARENA", subtitle_text="ELIGE EL ESCENARIO DEL COMBATE", border_color=styles.COLOR_PRIMARY)

        # Draw current stage preview
        name = self.stages[self.selected_idx]
        img  = self.preview_cache.get(name)
        
        rect_x, rect_y = 40, 65
        rect_w, rect_h = styles.BASE_WIDTH - 80, 140
        frame_rect = pygame.Rect(rect_x, rect_y, rect_w, rect_h)

        # Pulse border
        pulse = 0.7 + 0.3 * math.sin(self._time * 2.5)
        styles.draw_glow_border(screen, frame_rect, styles.COLOR_PRIMARY, intensity=pulse*0.7)

        if img:
            screen.blit(img, (rect_x, rect_y))
        else:
            pygame.draw.rect(screen, (30, 30, 40), frame_rect)
            nd = styles.font_body().render("PREVIEW NO ENCONTRADA", True, styles.COLOR_MUTED)
            screen.blit(nd, (frame_rect.centerx - nd.get_width()//2, frame_rect.centery - nd.get_height()//2))

        # Thin border on top of image
        pygame.draw.rect(screen, styles.COLOR_PRIMARY, frame_rect, 1)

        # Stage Name Tag
        name_font = styles.get_font(22, is_bold=True, is_header=True)
        name_surf = name_font.render(name.upper(), True, styles.COLOR_WHITE)
        # Background pill for name
        tag_bg = pygame.Rect(styles.BASE_WIDTH//2 - name_surf.get_width()//2 - 15, rect_y + rect_h - 15, name_surf.get_width() + 30, 30)
        styles.draw_panel(screen, tag_bg, border_color=styles.COLOR_PRIMARY)
        screen.blit(name_surf, (tag_bg.centerx - name_surf.get_width()//2, tag_bg.centery - name_surf.get_height()//2))

        # Counter / Instructions
        counter = styles.font_hint().render(f"{self.selected_idx+1} / {len(self.stages)}", True, styles.COLOR_MUTED)
        screen.blit(counter, (styles.BASE_WIDTH//2 - counter.get_width()//2, 215))

        hint = styles.font_hint().render("← → NAVEGAR   |   ENTER PARA EMPEZAR", True, styles.COLOR_DISABLED)
        screen.blit(hint, (styles.BASE_WIDTH//2 - hint.get_width()//2, styles.BASE_HEIGHT - 25))

        self.btn_back.draw(screen)
        self.btn_start.draw(screen)
        self.btn_prev.draw(screen)
        self.btn_next.draw(screen)
