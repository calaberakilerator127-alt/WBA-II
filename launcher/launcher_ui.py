"""
War Brawl Arena II — Launcher UI
Pygame splash window shown during update check/download.
"""
import pygame
import math
import sys
import os

# ── Colors matching game's Dark Nitro palette ─────────────────
C_BG        = ( 14,  14,  22)
C_PRIMARY   = (255,  30,  80)
C_ACCENT    = (  0, 210, 255)
C_SUCCESS   = ( 80, 230, 120)
C_SECONDARY = (255, 204,   0)
C_MUTED     = (140, 140, 160)
C_DISABLED  = ( 70,  70,  90)
C_PANEL     = ( 28,  28,  42)
C_BORDER    = ( 55,  55,  75)
C_WHITE     = (240, 240, 248)

W, H = 480, 270

def get_font(size, bold=True):
    for name in ("Bahnschrift", "Agency FB", "Arial"):
        try:
            f = pygame.font.SysFont(name, size, bold)
            if f: return f
        except Exception:
            pass
    return pygame.font.Font(None, size)


class LauncherWindow:
    """
    Self-contained Pygame window for the launcher.
    Call step() each frame to drive the animation, then render().
    """
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("War Brawl Arena II — Launcher")

        # Try to set the game icon
        _ico = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "assets", "Icon.ico")
        if os.path.exists(_ico):
            try:
                pygame.display.set_icon(pygame.image.load(_ico))
            except Exception:
                pass

        self.screen = pygame.display.set_mode((W, H))
        self.clock  = pygame.time.Clock()
        self._t     = 0.0

        # State
        self.status_text  = "INICIANDO..."
        self.sub_text     = ""
        self.progress     = 0.0   # 0.0 – 1.0
        self.show_skip    = False
        self.skip_hovered = False
        self.skip_clicked = False
        self.done         = False  # window should close

        # Skip button rect
        self.skip_rect = pygame.Rect(W//2 - 55, H - 36, 110, 22)

        # Font cache
        self.f_logo  = get_font(22, bold=True)
        self.f_sub   = get_font(9,  bold=False)
        self.f_body  = get_font(11, bold=True)
        self.f_hint  = get_font(8,  bold=False)

    # ── Public API ──────────────────────────────────────────────

    def set_status(self, text, sub=""):
        self.status_text = text
        self.sub_text    = sub

    def set_progress(self, pct):
        self.progress = max(0.0, min(1.0, pct))

    def show_skip_button(self, visible=True):
        self.show_skip = visible

    def pump(self):
        """Process events; returns True if window still alive, False if closed/skipped."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.skip_clicked = True
                return False
            if event.type == pygame.MOUSEMOTION:
                self.skip_hovered = self.skip_rect.collidepoint(event.pos)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.skip_rect.collidepoint(event.pos) and self.show_skip:
                    self.skip_clicked = True
                    return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE and self.show_skip:
                    self.skip_clicked = True
                    return False
        return True

    def render(self):
        self._t += self.clock.tick(60) / 1000.0
        s = self.screen
        s.fill(C_BG)

        self._draw_grid(s)
        self._draw_scanlines(s)
        self._draw_vignette(s)
        self._draw_logo(s)
        self._draw_separator(s)
        self._draw_status(s)
        self._draw_progress_bar(s)
        if self.show_skip:
            self._draw_skip_btn(s)

        pygame.display.flip()

    def close(self):
        pygame.quit()

    # ── Private draw helpers ─────────────────────────────────────

    def _draw_grid(self, s):
        off = int(self._t * 8) % 24
        for y in range(-24, H, 24):
            surf = pygame.Surface((W, 1), pygame.SRCALPHA)
            surf.fill((255, 255, 255, 6))
            s.blit(surf, (0, y + off))

    def _draw_scanlines(self, s):
        ln = pygame.Surface((W, 1), pygame.SRCALPHA)
        ln.fill((0, 0, 0, 14))
        for y in range(0, H, 3):
            s.blit(ln, (0, y))

    def _draw_vignette(self, s):
        v = pygame.Surface((W, H), pygame.SRCALPHA)
        cx, cy = W//2, H//2
        for r in range(max(cx, cy)+20, 0, -8):
            a = max(0, int(70 * (1 - r / (max(cx, cy)+20))))
            pygame.draw.circle(v, (0, 0, 0, a), (cx, cy), r)
        s.blit(v, (0, 0))

    def _draw_logo(self, s):
        # Pulsing glow
        pulse = 0.75 + 0.25 * math.sin(self._t * 2.0)
        r = int(C_PRIMARY[0] * pulse)
        g = int(C_PRIMARY[1] * pulse)
        b = int(C_PRIMARY[2] * pulse)
        col = (min(255,r), min(255,g), min(255,b))

        logo = self.f_logo.render("WAR BRAWL ARENA II", True, col)
        s.blit(logo, (W//2 - logo.get_width()//2, 30))

        sub = self.f_sub.render("THE NEXT GENERATION", True, C_SECONDARY)
        s.blit(sub, (W//2 - sub.get_width()//2, 56))

        # Version badge
        try:
            import json, os
            vf = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "version.json")
            ver = json.load(open(vf))["version"]
        except Exception:
            ver = "?"
        v_surf = self.f_hint.render(f"v{ver}", True, C_MUTED)
        s.blit(v_surf, (W - v_surf.get_width() - 6, 6))

    def _draw_separator(self, s):
        pygame.draw.line(s, C_PRIMARY, (0, 74), (W, 74), 2)
        pygame.draw.line(s, C_BORDER,  (0, 75), (W, 75), 1)

    def _draw_status(self, s):
        txt = self.f_body.render(self.status_text, True, C_WHITE)
        s.blit(txt, (W//2 - txt.get_width()//2, 100))
        if self.sub_text:
            sub = self.f_hint.render(self.sub_text, True, C_MUTED)
            s.blit(sub, (W//2 - sub.get_width()//2, 118))

    def _draw_progress_bar(self, s):
        bar_rect = pygame.Rect(40, 145, W - 80, 14)

        # Background
        pygame.draw.rect(s, C_PANEL,  bar_rect, border_radius=3)
        pygame.draw.rect(s, C_BORDER, bar_rect, 1, border_radius=3)

        if self.progress > 0:
            # Segmented fill (retro look)
            segs    = 20
            seg_w   = max(1, (bar_rect.width // segs) - 2)
            gap     = 2
            filled  = int(segs * self.progress)
            for i in range(filled):
                sx = bar_rect.x + 1 + i * (seg_w + gap)
                sr = pygame.Rect(sx, bar_rect.y + 1, seg_w, bar_rect.height - 2)
                pygame.draw.rect(s, C_ACCENT, sr)
                # Highlight
                pygame.draw.line(s, (min(255, C_ACCENT[0]+80), min(255, C_ACCENT[1]+80), 255),
                                 sr.topleft, (sr.right - 1, sr.top), 1)

        # Percentage label
        pct_txt = self.f_hint.render(f"{int(self.progress*100)}%", True, C_MUTED)
        s.blit(pct_txt, (W//2 - pct_txt.get_width()//2, bar_rect.bottom + 4))

    def _draw_skip_btn(self, s):
        col  = C_ACCENT if self.skip_hovered else C_BORDER
        bcol = (0, 80, 100) if self.skip_hovered else C_PANEL
        pygame.draw.rect(s, bcol, self.skip_rect, border_radius=3)
        pygame.draw.rect(s, col,  self.skip_rect, 1, border_radius=3)
        lbl = self.f_hint.render("SALTAR ACTUALIZACIÓN  [ESC]", True,
                                  C_WHITE if self.skip_hovered else C_MUTED)
        s.blit(lbl, (self.skip_rect.centerx - lbl.get_width()//2,
                     self.skip_rect.centery - lbl.get_height()//2))
