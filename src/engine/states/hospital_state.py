import pygame
from src.graphics import styles
from src.graphics.ui_system import PixelButton, FeedbackMessage, NavBar
from src.utils.localization import lang

HEAL_COLOR = (80, 230, 140)   # Hospital green theme

class HospitalState:
    """
    Recovery Clinic — Heal fighters for Brawels.
    Fighter selector with HP bar. Cost prominently displayed.
    """
    def __init__(self, manager):
        self.manager    = manager
        self._time      = 0.0
        self.feedback   = FeedbackMessage(duration=2.5)

        self.acc        = manager.data_manager.active_p1
        self.roster     = self.acc.fighters if self.acc else []
        self.fighter_idx= 0

        manager.data_manager.play_music(styles.ASSET_PATHS["music"]["hosp"])

        self.btn_back   = PixelButton(manager, "← HUB", (8, 8), size=(60, 22),
                                      callback=self.go_back, variant="ghost")
        self.btn_prev_f = PixelButton(manager, "◄",
                                      (styles.BASE_WIDTH//2 - 80, 105), size=(24, 24),
                                      callback=lambda: self.switch_f(-1), variant="ghost")
        self.btn_next_f = PixelButton(manager, "►",
                                      (styles.BASE_WIDTH//2 + 56, 105), size=(24, 24),
                                      callback=lambda: self.switch_f(1), variant="ghost")
        self.btn_heal   = PixelButton(manager, "CURAR (100 B)",
                                      (styles.BASE_WIDTH//2 - 70, 178), size=(140, 32),
                                      callback=self.heal, variant="success")
        self.nav_bar    = NavBar(manager, current_state="hospital")

    def switch_f(self, delta):
        if not self.roster: return
        self.fighter_idx = (self.fighter_idx + delta) % len(self.roster)
        self.feedback.show("", kind="info")

    def go_back(self):
        self.manager.change_state("menu")

    def heal(self):
        if not self.roster: return
        f    = self.roster[self.fighter_idx]
        cost = 100
        if self.acc.brawels >= cost:
            self.acc.brawels -= cost
            f.hp       = f.max_hp
            f.estamina = f.stats.estamina_max
            f.energia  = f.stats.energia_max
            self.manager.data_manager.save_account(self.acc)
            self.manager.data_manager.play_sfx("stat")
            self.feedback.show(f"¡{f.name.upper()} RECUPERADO AL 100%!", kind="success")
        else:
            self.feedback.show("BRAWELS INSUFICIENTES", kind="error")

    def update(self, dt, events):
        self._time += dt
        for event in events:
            d = self.manager.data_manager
            if event.type == pygame.KEYDOWN:
                if event.key == d.get_key("BACK"):    self.go_back()
                elif event.key == d.get_key("LEFT"):  self.switch_f(-1)
                elif event.key == d.get_key("RIGHT"): self.switch_f(1)
                elif event.key == d.get_key("CONFIRM"): self.heal()

            self.btn_back.handle_event(event)
            self.btn_heal.handle_event(event)
            self.btn_prev_f.handle_event(event)
            self.btn_next_f.handle_event(event)
            self.nav_bar.handle_event(event)

        self.btn_back.update(dt)
        self.btn_heal.update(dt)
        self.btn_prev_f.update(dt)
        self.btn_next_f.update(dt)
        self.nav_bar.update(dt)
        self.feedback.update(dt)

    def draw(self, screen):
        screen.fill(styles.COLOR_BG)
        styles.draw_scanlines(screen, alpha=14)

        # Header — hospital green theme
        styles.draw_header(screen, "CLÍNICA DE RECUPERACIÓN",
                           subtitle_text="RESTAURA LA SALUD DE TUS LUCHADORES",
                           title_color=HEAL_COLOR,
                           border_color=HEAL_COLOR)

        if not self.roster:
            screen.blit(styles.font_body().render("SIN LUCHADORES", True, styles.COLOR_ERROR),
                        (styles.BASE_WIDTH//2-60, 120))
            self.btn_back.draw(screen)
            return

        fighter = self.roster[self.fighter_idx]
        cx      = styles.BASE_WIDTH // 2

        # ── Fighter Selector ────────────────────────────────────
        sel_rect = pygame.Rect(cx - 54, 103, 108, 28)
        styles.draw_panel(screen, sel_rect, border_color=HEAL_COLOR)
        fn   = styles.font_body(bold=True)
        fs   = fn.render(fighter.name.upper()[:14], True, styles.COLOR_WHITE)
        screen.blit(fs, (cx - fs.get_width()//2, sel_rect.centery - fs.get_height()//2))
        self.btn_prev_f.draw(screen)
        self.btn_next_f.draw(screen)

        hint_nav = styles.font_hint().render("◄ ► CAMBIAR LUCHADOR", True, styles.COLOR_MUTED)
        screen.blit(hint_nav, (cx - hint_nav.get_width()//2, 134))

        # ── Central Status Panel ─────────────────────────────────
        panel_rect = pygame.Rect(cx - 120, 144, 240, 26)
        styles.draw_panel(screen, panel_rect, border_color=styles.COLOR_BORDER)

        hp_pct = fighter.hp / max(1, fighter.max_hp)
        color  = HEAL_COLOR if hp_pct > 0.5 else (
                 styles.COLOR_WARNING if hp_pct > 0.25 else styles.COLOR_ERROR)

        # HP label
        hp_lbl = styles.font_caption(bold=True).render(
            f"HP: {int(fighter.hp)} / {int(fighter.max_hp)}", True, styles.COLOR_WHITE)
        screen.blit(hp_lbl, (cx - hp_lbl.get_width()//2, 148))

        # HP bar
        bar_rect = pygame.Rect(cx - 110, 160, 220, 8)
        styles.draw_segmented_bar(screen, bar_rect, hp_pct, color, segments=14)

        # Status indicator
        if hp_pct >= 1.0:
            status_txt = "● ESTADO: PERFECTO"
            status_col = HEAL_COLOR
        elif hp_pct > 0.5:
            status_txt = "● ESTADO: LEVEMENTE HERIDO"
            status_col = styles.COLOR_WARNING
        else:
            status_txt = "● ESTADO: CRÍTICO"
            status_col = styles.COLOR_ERROR

        st_surf = styles.font_hint().render(status_txt, True, status_col)
        screen.blit(st_surf, (cx - st_surf.get_width()//2, 172))

        # ── Heal Button + Cost ───────────────────────────────────
        self.btn_heal.rect.y = 186
        self.btn_heal.draw(screen)

        # Cost comparison
        can_afford = self.acc.brawels >= 100
        cost_color = styles.COLOR_SUCCESS if can_afford else styles.COLOR_ERROR
        cost_txt   = styles.font_hint().render(
            f"BRAWELS DISPONIBLES: {self.acc.brawels}  (COSTO: 100)",
            True, cost_color)
        screen.blit(cost_txt, (cx - cost_txt.get_width()//2, 224))

        # Disable heal if full health
        if hp_pct >= 1.0:
            full_txt = styles.font_hint().render("✓ YA ESTÁ CURADO", True, HEAL_COLOR)
            screen.blit(full_txt, (cx - full_txt.get_width()//2, 222))

        self.feedback.draw(screen, y=styles.BASE_HEIGHT - styles.NAV_HEIGHT - 12)
        self.btn_back.draw(screen)
        self.nav_bar.draw(screen)
