import pygame
import math
from src.graphics import styles
from src.graphics.ui_system import PixelButton

class PauseState:
    """
    Pause overlay — Appears over the current game state.
    Clear options, consistent layout, ESC to resume.
    """
    def __init__(self, manager):
        self.manager = manager
        self._time   = 0.0
        self._alpha  = 0.0   # Fade-in animation

        cx = styles.BASE_WIDTH  // 2
        cy = styles.BASE_HEIGHT // 2

        self.buttons = [
            PixelButton(manager, "▶  REANUDAR",       (cx-70, cy-20), size=(140, 28),
                        callback=self.resume,         variant="success"),
            PixelButton(manager, "⚙  AJUSTES",        (cx-70, cy+14), size=(140, 28),
                        callback=self.open_settings,  variant="ghost"),
            PixelButton(manager, "🚪 SALIR AL HUB",   (cx-70, cy+48), size=(140, 28),
                        callback=self.quit_to_hub,    variant="danger"),
        ]

    def resume(self):
        self.manager.overlay = None

    def open_settings(self):
        self.manager.push_state("settings")
        self.manager.overlay = None

    def quit_to_hub(self):
        self.manager.overlay = None
        self.manager.change_state("menu")

    def update(self, dt, events):
        self._time  += dt
        self._alpha  = min(1.0, self._alpha + 5.0 * dt)

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == self.manager.data_manager.get_key("BACK"):
                    self.resume()
            for btn in self.buttons:
                btn.handle_event(event)

        for btn in self.buttons:
            btn.update(dt)

    def draw(self, screen):
        # ── Translucent overlay ─────────────────────────────────
        overlay = pygame.Surface((styles.BASE_WIDTH, styles.BASE_HEIGHT), pygame.SRCALPHA)
        alpha   = int(190 * self._alpha)
        overlay.fill((0, 0, 0, alpha))
        screen.blit(overlay, (0, 0))
        styles.draw_vignette(screen, strength=60)

        # ── Central panel ────────────────────────────────────────
        panel_w, panel_h = 180, 130
        cx = styles.BASE_WIDTH  // 2
        cy = styles.BASE_HEIGHT // 2
        panel_rect = pygame.Rect(cx - panel_w//2, cy - panel_h//2 - 30, panel_w, panel_h)
        styles.draw_panel(screen, panel_rect,
                          bg_color=styles.COLOR_PANEL_BG2,
                          border_color=styles.COLOR_PRIMARY)
        styles.draw_glow_border(screen, panel_rect, styles.COLOR_PRIMARY, intensity=0.5)

        # ── Title ────────────────────────────────────────────────
        font_title = styles.get_font(20, is_bold=True, is_header=True)
        title_surf = font_title.render("PAUSA", True, styles.COLOR_WHITE)
        title_surf.set_alpha(int(255 * self._alpha))
        screen.blit(title_surf,
                    (cx - title_surf.get_width()//2, panel_rect.y + 10))

        # Horizontal separator
        pygame.draw.line(screen, styles.COLOR_BORDER,
                          (panel_rect.x + 10, panel_rect.y + 32),
                          (panel_rect.right - 10, panel_rect.y + 32), 1)

        # ── Hint ─────────────────────────────────────────────────
        hint = styles.font_hint().render("ESC = REANUDAR", True, styles.COLOR_DISABLED)
        hint.set_alpha(int(180 * self._alpha))
        screen.blit(hint, (cx - hint.get_width()//2, styles.BASE_HEIGHT - 14))

        # ── Buttons ──────────────────────────────────────────────
        for btn in self.buttons:
            btn.draw(screen)


class QuitOverlay:
    """Prompt for quitting the game."""
    def __init__(self, manager):
        self.manager = manager
        self._alpha = 0.0
        cx, cy = styles.BASE_WIDTH // 2, styles.BASE_HEIGHT // 2
        self.btn_no  = PixelButton(manager, "VOLVER", (cx - 75, cy + 12), size=(70, 24), callback=self.cancel, variant="ghost")
        self.btn_yes = PixelButton(manager, "SÍ, SALIR", (cx + 5, cy + 12), size=(70, 24), callback=self.quit_game, variant="danger")
        
    def quit_game(self):
        pygame.event.post(pygame.event.Event(pygame.QUIT))
        
    def cancel(self):
        self.manager.overlay = None

    def update(self, dt, events):
        self._alpha = min(1.0, self._alpha + 5.0 * dt)
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.cancel()
            self.btn_yes.handle_event(event)
            self.btn_no.handle_event(event)
        self.btn_yes.update(dt)
        self.btn_no.update(dt)

    def draw(self, screen):
        overlay = pygame.Surface((styles.BASE_WIDTH, styles.BASE_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(180 * self._alpha)))
        screen.blit(overlay, (0, 0))
        
        panel_w, panel_h = 220, 110
        cx, cy = styles.BASE_WIDTH // 2, styles.BASE_HEIGHT // 2
        panel_rect = pygame.Rect(cx - panel_w//2, cy - panel_h//2, panel_w, panel_h)
        styles.draw_panel(screen, panel_rect, bg_color=styles.COLOR_PANEL_BG2, border_color=styles.COLOR_ERROR)
        
        font = styles.font_body(bold=True)
        txt1 = font.render("¿SALIR AL ESCRITORIO?", True, styles.COLOR_WHITE)
        txt2 = styles.font_hint().render("PROGRESO AUTOGUARDADO", True, styles.COLOR_SUCCESS)
        screen.blit(txt1, (cx - txt1.get_width()//2, panel_rect.y + 15))
        screen.blit(txt2, (cx - txt2.get_width()//2, panel_rect.y + 35))
        
        self.btn_yes.draw(screen)
        self.btn_no.draw(screen)
