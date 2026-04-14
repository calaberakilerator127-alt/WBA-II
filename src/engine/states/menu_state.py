import pygame
import math
from src.graphics import styles
from src.graphics.ui_system import PixelButton, NavBar
from src.utils.localization import lang

class MenuState:
    """
    Main Hub — The nerve center of War Brawl Arena II.
    Structured into: title zone, action cards, and bottom NavBar.
    """
    def __init__(self, manager):
        self.manager = manager
        self._time   = 0.0

        self.manager.data_manager.play_music(styles.ASSET_PATHS["music"]["hub"])

        cx   = styles.BASE_WIDTH  // 2
        bw   = 148
        bh   = 26
        bx   = cx - bw // 2

        # ── Primary Combat Actions ────────────────────────────────
        self.btn_actions = [
            PixelButton(manager, "⚔  LUCHA CLÁSICA",  (bx, 96),  size=(bw, bh),
                        callback=lambda: self.start_config("LUCHA"),   variant="primary"),
            PixelButton(manager, "👥 DUELO DE EQUIPOS",(bx, 126), size=(bw, bh),
                        callback=lambda: self.start_config("DUELO"),   variant="primary"),
            PixelButton(manager, "🏆 CAMPEONATO",      (bx, 156), size=(bw, bh),
                        callback=lambda: self.start_config("CAMPEONATO"), variant="secondary"),
        ]

        # ── Exit ─────────────────────────────────────────────────
        self.btn_exit = PixelButton(manager, "SALIR AL ESCRITORIO", (bx, 190),
                                    size=(bw, 20), callback=self._quit,
                                    variant="ghost", font_size=8)

        # ── Navigation bar at bottom ──────────────────────────────
        self.nav_bar = NavBar(manager, current_state="menu")

    def start_config(self, mode):
        self.manager.current_mode = mode
        self.manager.change_state("mode_config")

    def _quit(self):
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    def update(self, dt, events):
        self._time += dt
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == self.manager.data_manager.get_key("BACK"):
                    self.manager.change_state("login")
            for btn in self.btn_actions:
                btn.handle_event(event)
            self.btn_exit.handle_event(event)
            self.nav_bar.handle_event(event)

        for btn in self.btn_actions:
            btn.update(dt)
        self.btn_exit.update(dt)
        self.nav_bar.update(dt)

    def draw(self, screen):
        # ── Background ──────────────────────────────────────────
        screen.fill(styles.COLOR_BG)

        # Animated background grid lines (subtle)
        grid_offset = int(self._time * 10) % 30
        for y in range(-30, styles.BASE_HEIGHT, 30):
            alpha = 8
            line_s = pygame.Surface((styles.BASE_WIDTH, 1), pygame.SRCALPHA)
            line_s.fill((255, 255, 255, alpha))
            screen.blit(line_s, (0, y + grid_offset))

        styles.draw_scanlines(screen, alpha=16, spacing=3)
        styles.draw_vignette(screen, strength=70)

        # ── Top Banner ──────────────────────────────────────────
        # Background gradient band
        band_surf = pygame.Surface((styles.BASE_WIDTH, 78), pygame.SRCALPHA)
        for row in range(78):
            alpha = max(0, 180 - row * 2)
            pygame.draw.line(band_surf, (10, 10, 20, alpha), (0, row), (styles.BASE_WIDTH, row))
        screen.blit(band_surf, (0, 0))

        # Corner accent lines (decorative)
        pygame.draw.line(screen, styles.COLOR_PRIMARY, (0, 0), (40, 0), 3)
        pygame.draw.line(screen, styles.COLOR_PRIMARY, (0, 0), (0, 20), 3)
        pygame.draw.line(screen, styles.COLOR_PRIMARY,
                          (styles.BASE_WIDTH, 0), (styles.BASE_WIDTH-40, 0), 3)
        pygame.draw.line(screen, styles.COLOR_PRIMARY,
                          (styles.BASE_WIDTH, 0), (styles.BASE_WIDTH, 20), 3)

        # Title with animated glow pulse
        font_logo = styles.get_font(24, is_bold=True, is_header=True)
        t = self._time
        pulse = 0.7 + 0.3 * math.sin(t * 1.8)
        r = int(styles.COLOR_PRIMARY[0] * pulse)
        g = int(styles.COLOR_PRIMARY[1] * pulse)
        b = int(styles.COLOR_PRIMARY[2] * pulse)
        logo_color = (min(255,r), min(255,g), min(255,b))

        logo_surf = font_logo.render("WAR BRAWL ARENA II", True, logo_color)
        lx = styles.BASE_WIDTH // 2 - logo_surf.get_width() // 2
        styles.draw_text_outline(screen, "WAR BRAWL ARENA II", font_logo,
                                  logo_color, (lx, 12),
                                  outline_color=(80, 0, 20), outline_width=1)

        sub_surf = styles.font_hint().render("THE NEXT GENERATION", True, styles.COLOR_SECONDARY)
        screen.blit(sub_surf, (styles.BASE_WIDTH//2 - sub_surf.get_width()//2, 42))

        # Separator
        pygame.draw.line(screen, styles.COLOR_PRIMARY, (0, 58), (styles.BASE_WIDTH, 58), 2)
        pygame.draw.line(screen, styles.COLOR_BORDER,  (0, 59), (styles.BASE_WIDTH, 59), 1)

        # ── Mode label ──────────────────────────────────────────
        mode_surf = styles.font_hint().render("SELECCIONA UN MODO DE COMBATE",
                                               True, styles.COLOR_MUTED)
        screen.blit(mode_surf, (styles.BASE_WIDTH//2 - mode_surf.get_width()//2, 74))

        # ── Buttons ─────────────────────────────────────────────
        for btn in self.btn_actions:
            btn.draw(screen)

        # Tip below buttons
        tip = styles.font_hint().render("← NAV  •  USAR BARRA INFERIOR PARA NAVEGAR →",
                                         True, styles.COLOR_DISABLED)
        screen.blit(tip, (styles.BASE_WIDTH//2 - tip.get_width()//2, 178))

        self.btn_exit.draw(screen)

        # ── Account Info Card ────────────────────────────────────
        acc = self.manager.data_manager.active_p1
        if acc:
            card_rect = pygame.Rect(8, 62, 140, 22)
            styles.draw_panel(screen, card_rect,
                              bg_color=styles.COLOR_PANEL_BG,
                              border_color=styles.COLOR_BORDER)
            acc_font = styles.font_hint()
            wr = (acc.wins / (acc.wins + acc.losses) * 100) if (acc.wins + acc.losses) > 0 else 0.0
            info = acc_font.render(
                f"▸ {acc.username.upper()[:12]}  {acc.wins}W/{acc.losses}L",
                True, styles.COLOR_ACCENT)
            screen.blit(info, (12, 67))

            brawels_rect = pygame.Rect(styles.BASE_WIDTH - 90, 62, 82, 22)
            styles.draw_panel(screen, brawels_rect,
                              bg_color=styles.COLOR_PANEL_BG,
                              border_color=styles.COLOR_BORDER)
            bwf = acc_font.render(f"💰 {acc.brawels}B", True, styles.COLOR_SECONDARY)
            screen.blit(bwf, (styles.BASE_WIDTH - 86, 67))

        # ── Nav Bar ─────────────────────────────────────────────
        self.nav_bar.draw(screen)
