import pygame
import math
from src.graphics import styles

class PredictionHUD:
    """
    Real-time combat prediction panel shown when selecting a move.
    Displays estimated damage, accuracy, move type, and cost indicators.
    """
    def __init__(self, manager, pos=None):
        self.manager = manager
        if pos is None:
            pos = (styles.BASE_WIDTH // 2 - 85, styles.BASE_HEIGHT - 88)
        self.rect  = pygame.Rect(pos, (170, 52))
        self._time = 0.0

    def update(self, dt):
        self._time += dt

    def draw(self, screen, fighter, move):
        if not move:
            return

        # ── Panel ──────────────────────────────────────────────
        styles.draw_panel(screen, self.rect,
                          bg_color=styles.COLOR_PANEL_BG2,
                          border_color=styles.COLOR_ACCENT)

        # Pulsing accent border when a move is selected
        pulse = 0.6 + 0.4 * math.sin(self._time * 4.0)
        styles.draw_glow_border(screen, self.rect, styles.COLOR_ACCENT,
                                intensity=pulse * 0.4)

        # ── Move type tag ──────────────────────────────────────
        is_phys  = (move.type == "Fisico")
        type_col = styles.COLOR_PRIMARY if is_phys else styles.COLOR_ENERGY_BAR
        type_lbl = "FÍSICO" if is_phys else "MÁGICO"
        styles.draw_tag(screen, type_lbl,
                        (self.rect.x + 4, self.rect.y + 4), type_col)

        # ── Prediction values ──────────────────────────────────
        stat_val = fighter.stats.fuerza if is_phys else fighter.stats.poder
        damage   = int((move.base_damage + stat_val) * move.multiplier)
        accuracy = 90

        hf = styles.font_hint()

        # Damage
        dmg_lbl = hf.render("DMG ESTIMADO:", True, styles.COLOR_MUTED)
        dmg_val = styles.font_caption(bold=True).render(str(damage), True, styles.COLOR_PRIMARY)
        screen.blit(dmg_lbl, (self.rect.x + 4, self.rect.y + 16))
        screen.blit(dmg_val, (self.rect.x + 95, self.rect.y + 15))

        # Accuracy
        acc_lbl = hf.render("PRECISIÓN:", True, styles.COLOR_MUTED)
        acc_val = hf.render(f"{accuracy}%", True, styles.COLOR_SUCCESS)
        screen.blit(acc_lbl, (self.rect.x + 4, self.rect.y + 30))
        screen.blit(acc_val, (self.rect.x + 95, self.rect.y + 30))

        # Move name at bottom
        mv_surf = hf.render(move.name.upper(), True, type_col)
        screen.blit(mv_surf, (self.rect.right - mv_surf.get_width() - 4,
                               self.rect.y + 4))
