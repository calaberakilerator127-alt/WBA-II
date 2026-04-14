import pygame
import math
from src.graphics import styles
from src.utils.localization import lang

class BattleIntroState:
    """
    Pre-combat introduction — Dramatic presenter sequence.
    Animated name reveals, phase timer bar, skip hint.
    """
    def __init__(self, manager):
        self.manager = manager
        self._time   = 0.0

        team1 = getattr(manager, "selected_team", None)
        acc1 = manager.data_manager.active_p1
        self.f1 = team1[0] if team1 else acc1.fighters[0]

        team2 = getattr(manager, "selected_team_p2", None)
        acc2 = getattr(manager.data_manager, "active_p2", None)
        if team2:
            self.f2 = team2[0]
        elif acc2 and acc2.fighters:
            self.f2 = acc2.fighters[0]
        else:
            self.f2 = manager.data_manager.create_default_fighter("RIVAL 1")

        # Presenter image
        self.presenter_img = None
        pres_path = styles.ASSET_PATHS["images"].get("presenter")
        if pres_path:
            try:
                img = pygame.image.load(pres_path).convert_alpha()
                self.presenter_img = pygame.transform.scale(img, (180, 180))
            except Exception:
                pass

        # Phase sequence
        self.phases        = ["START", "P1_INTRO", "P2_INTRO", "READY"]
        self.curr_phase    = 0
        self.phase_timer   = 0.0
        self.phase_dur     = 3.2    # Seconds per phase
        self._name_alpha   = 0.0   # Fade-in for fighter names
        self._flash_alpha  = 0.0   # White flash on phase change

        self._start_current_phase()

    def _start_current_phase(self):
        self.phase_timer  = 0.0
        self._name_alpha  = 0.0
        self._flash_alpha = 255.0
        phase = self.phases[self.curr_phase]
        if phase == "P1_INTRO" and self.f1.entrance_theme:
            self.manager.data_manager.play_music(self.f1.entrance_theme, loop=False)
        elif phase == "P2_INTRO" and self.f2.entrance_theme:
            self.manager.data_manager.play_music(self.f2.entrance_theme, loop=False)
        elif phase == "READY":
            self.manager.change_state("battle")

    def _next_phase(self):
        self.curr_phase += 1
        if self.curr_phase < len(self.phases):
            self._start_current_phase()
        else:
            self.manager.change_state("battle")

    def update(self, dt, events):
        self._time       += dt
        self.phase_timer += dt

        # Fade animations
        self._name_alpha  = min(255.0, self._name_alpha  + 280.0 * dt)
        self._flash_alpha = max(0.0,   self._flash_alpha - 400.0 * dt)

        if self.phase_timer >= self.phase_dur:
            self._next_phase()

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
                    self.manager.change_state("battle")

    def draw(self, screen):
        screen.fill(styles.COLOR_BG)

        # ── Animated background ─────────────────────────────────
        styles.draw_scanlines(screen, alpha=20, spacing=3)

        # Diagonal scan lines for drama
        t = self._time
        for i in range(6):
            x  = int((t * 60 + i * 80) % (styles.BASE_WIDTH + 80)) - 80
            dy = styles.BASE_HEIGHT
            line_s = pygame.Surface((2, dy), pygame.SRCALPHA)
            line_s.fill((255, 255, 255, 8))
            screen.blit(line_s, (x, 0))

        styles.draw_vignette(screen, strength=90)

        # ── Presenter (bottom-right) ──────────────────────────
        if self.presenter_img:
            py = styles.BASE_HEIGHT - 180
            screen.blit(self.presenter_img, (styles.BASE_WIDTH - 185, py))

        phase = self.phases[self.curr_phase]

        # ── Timer bar (top) ───────────────────────────────────
        progress = 1.0 - min(1.0, self.phase_timer / self.phase_dur)
        timer_rect = pygame.Rect(0, 0, styles.BASE_WIDTH, 3)
        pygame.draw.rect(screen, styles.COLOR_BORDER, timer_rect)
        if progress > 0:
            pygame.draw.rect(screen, styles.COLOR_PRIMARY,
                             pygame.Rect(0, 0, int(styles.BASE_WIDTH * progress), 3))

        # ── Central banner ────────────────────────────────────
        banner_h  = 72
        banner_y  = styles.BASE_HEIGHT // 2 - banner_h // 2
        banner_bg = pygame.Surface((styles.BASE_WIDTH, banner_h), pygame.SRCALPHA)
        banner_bg.fill((0, 0, 0, 180))
        screen.blit(banner_bg, (0, banner_y))
        pygame.draw.line(screen, styles.COLOR_PRIMARY,
                          (0, banner_y), (styles.BASE_WIDTH, banner_y), 2)
        pygame.draw.line(screen, styles.COLOR_PRIMARY,
                          (0, banner_y + banner_h),
                          (styles.BASE_WIDTH, banner_y + banner_h), 2)

        # ── Phase content ─────────────────────────────────────
        fnt_big = styles.get_font(22, is_bold=True, is_header=True)
        fnt_mid = styles.font_body(bold=True)
        fnt_sm  = styles.font_caption()
        name_alpha = int(self._name_alpha)

        if phase == "START":
            lbl = fnt_mid.render("¡DAMAS Y CABALLEROS, BIENVENIDOS A LA ARENA!", True,
                                  styles.COLOR_WHITE)
            lbl.set_alpha(name_alpha)
            screen.blit(lbl, (styles.BASE_WIDTH//2 - lbl.get_width()//2,
                               banner_y + banner_h//2 - lbl.get_height()//2))

        elif phase in ("P1_INTRO", "P2_INTRO"):
            is_p1    = (phase == "P1_INTRO")
            fighter  = self.f1 if is_p1 else self.f2
            pre_lbl  = "PRESENTANDO AL ASPIRANTE..." if is_p1 else "Y SU RIVAL EN EL RING..."
            col      = styles.COLOR_ACCENT if is_p1 else styles.COLOR_PRIMARY

            pre_surf = fnt_sm.render(pre_lbl, True, styles.COLOR_MUTED)
            pre_surf.set_alpha(name_alpha)
            screen.blit(pre_surf, (50, banner_y + 8))

            # Fighter name with outline
            name_surf = fnt_big.render(fighter.name.upper(), True, col)
            name_surf.set_alpha(name_alpha)
            screen.blit(name_surf, (50, banner_y + 24))

            # Level / affinity badge
            badge_txt = f"NIVEL {fighter.level}  •  {fighter.elemental_affinity.upper()}"
            badge_s   = fnt_sm.render(badge_txt, True, styles.COLOR_MUTED)
            badge_s.set_alpha(name_alpha)
            screen.blit(badge_s, (50, banner_y + banner_h - badge_s.get_height() - 6))

        # ── VS divider (always visible) ───────────────────────
        vs_surf = styles.get_font(14, is_bold=True, is_header=True).render(
            f"{self.f1.name.upper()}  VS  {self.f2.name.upper()}",
            True, styles.COLOR_SECONDARY)
        screen.blit(vs_surf, (styles.BASE_WIDTH//2 - vs_surf.get_width()//2, 20))

        # ── Skip hint ─────────────────────────────────────────
        hint = styles.font_hint().render(
            "[ ESPACIO / ENTER ] SALTAR INTRO", True, styles.COLOR_DISABLED)
        screen.blit(hint, (styles.BASE_WIDTH//2 - hint.get_width()//2,
                            styles.BASE_HEIGHT - 14))

        # ── Flash overlay on phase change ─────────────────────
        if self._flash_alpha > 0:
            flash = pygame.Surface((styles.BASE_WIDTH, styles.BASE_HEIGHT), pygame.SRCALPHA)
            flash.fill((255, 255, 255, int(self._flash_alpha)))
            screen.blit(flash, (0, 0))
