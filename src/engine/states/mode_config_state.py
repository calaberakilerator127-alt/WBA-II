import pygame
from src.graphics import styles
from src.graphics.ui_system import PixelButton
from src.utils.localization import lang

# Description text for each mode
MODE_DESCS = {
    "LUCHA":      "Un combate estándar entre dos luchadores. El primero en caer pierde.",
    "DUELO":      "Equipos de hasta 3 luchadores se enfrentan. Gana quien derrote al equipo rival.",
    "CAMPEONATO": "Torneo extenso con múltiples rondas y contrincantes progresivos.",
}

class ModeConfigState:
    """
    Battle Mode Configuration — Set rounds, team size, and ruleset.
    Visual option selectors with clear indicators and mode description.
    """
    def __init__(self, manager, mode_name="LUCHA"):
        self.manager    = manager
        self.mode_name  = getattr(manager, "current_mode", mode_name)
        self._time      = 0.0

        self.rounds        = 1
        self.team1_size    = 1
        self.is_deathmatch = False
        self.is_p2_local  = False

        cx = styles.BASE_WIDTH // 2
        bw = 60

        self.btn_back = PixelButton(manager, "← MENÚ", (8, 8), size=(68, 22),
                                    callback=self.go_back, variant="ghost")

        # Round buttons
        self.round_btns = [
            PixelButton(manager, "1 ROND", (cx-95, 100), size=(bw, 24),
                        callback=lambda: self.set_rounds(1)),
            PixelButton(manager, "3 ROND", (cx-30, 100), size=(bw, 24),
                        callback=lambda: self.set_rounds(3)),
            PixelButton(manager, "5 ROND", (cx+35, 100), size=(bw, 24),
                        callback=lambda: self.set_rounds(5)),
        ]

        # Team size buttons
        self.team_btns = [
            PixelButton(manager, "1 vs 1", (cx-95, 140), size=(bw, 24),
                        callback=lambda: self.set_t1(1),
                        tooltip_text="Un luchador por bando"),
            PixelButton(manager, "2 vs 2", (cx-30, 140), size=(bw, 24),
                        callback=lambda: self.set_t1(2),
                        tooltip_text="Dos luchadores por bando"),
            PixelButton(manager, "3 vs 3", (cx+35, 140), size=(bw, 24),
                        callback=lambda: self.set_t1(3),
                        tooltip_text="Tres luchadores por bando"),
        ]

        # Ruleset buttons
        self.rule_btns = [
            PixelButton(manager, "CLÁSICO",   (cx-90, 180), size=(82, 24),
                        callback=lambda: self.set_dm(False),
                        tooltip_text="HP se restaura entre rondas"),
            PixelButton(manager, "A MUERTE",  (cx+10, 180), size=(82, 24),
                        callback=lambda: self.set_dm(True),
                        tooltip_text="HP no se restaura entre rondas"),
        ]

        # Opponent buttons
        self.opp_btns = [
            PixelButton(manager, "📦 VS IA", (cx-90, 60), size=(82, 24),
                        callback=lambda: self.set_p2(False),
                        tooltip_text="Combatir contra la computadora"),
            PixelButton(manager, "👥 VS LOCAL", (cx+10, 60), size=(82, 24),
                        callback=lambda: self.set_p2(True),
                        tooltip_text="Combate contra un amigo en esta PC"),
        ]

        # Play button
        self.btn_play = PixelButton(manager, "⚔  ¡A LUCHAR!", (cx-80, 225),
                                    size=(160, 32), callback=self.start_battle,
                                    variant="primary")

        self.all_btns = [self.btn_back, self.btn_play,
                         *self.round_btns, *self.team_btns, *self.rule_btns, *self.opp_btns]

    def set_rounds(self, r): self.rounds = r
    def set_t1(self, s):     self.team1_size = s
    def set_dm(self, dm):    self.is_deathmatch = dm
    def set_p2(self, p2):    self.is_p2_local = p2
    def go_back(self):       self.manager.change_state("menu")

    def start_battle(self):
        self.manager.combat_config = {
            "rounds":       self.rounds,
            "team_size":    self.team1_size,
            "is_deathmatch":self.is_deathmatch,
            "mode":         self.mode_name,
            "is_p2_local":   self.is_p2_local
        }
        self.manager.selected_team = []
        self.manager.change_state("team_select")

    def update(self, dt, events):
        self._time += dt
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.go_back()
            for btn in self.all_btns:
                btn.handle_event(event)
        for btn in self.all_btns:
            btn.update(dt)

    def _is_selected(self, btn_list, index):
        """Returns True if the btn at index is the current selection."""
        return False  # Used by caller

    def draw(self, screen):
        screen.fill(styles.COLOR_BG)
        styles.draw_scanlines(screen, alpha=14)
        styles.draw_header(screen, f"CONFIGURAR: {self.mode_name}",
                           subtitle_text=MODE_DESCS.get(self.mode_name, ""),
                           border_color=styles.COLOR_PRIMARY)

        cx   = styles.BASE_WIDTH // 2
        hf   = styles.font_hint()
        sec  = styles.font_caption(bold=True)

        # ── OPONENTE ────────────────────────────────────────────
        screen.blit(sec.render("TIPO DE OPONENTE", True, styles.COLOR_MUTED), (8, 46))
        self._draw_option_row(screen, self.opp_btns, [False, True], self.is_p2_local)

        # ── RONDAS ──────────────────────────────────────────────
        screen.blit(sec.render("NÚMERO DE RONDAS", True, styles.COLOR_MUTED), (8, 86))
        self._draw_option_row(screen, self.round_btns,
                               [1, 3, 5], self.rounds)

        # ── TAMAÑO DE EQUIPO ────────────────────────────────────
        screen.blit(sec.render("TAMAÑO DEL EQUIPO", True, styles.COLOR_MUTED), (8, 126))
        self._draw_option_row(screen, self.team_btns,
                               [1, 2, 3], self.team1_size)

        # ── REGLAS ──────────────────────────────────────────────
        screen.blit(sec.render("TIPO DE COMBATE", True, styles.COLOR_MUTED), (8, 166))
        self._draw_rule_row(screen)

        # ── Summary panel ───────────────────────────────────────
        sum_rect = pygame.Rect(8, 208, styles.BASE_WIDTH - 16, 14)
        styles.draw_panel(screen, sum_rect, border_color=styles.COLOR_BORDER)
        dm_txt   = "A MUERTE" if self.is_deathmatch else "CLÁSICO"
        opp_txt  = "P2" if self.is_p2_local else "IA"
        summary  = f"MODO: {self.mode_name}  •  {opp_txt}  •  {self.rounds} ROND.  •  {self.team1_size}v{self.team1_size}  •  {dm_txt}"
        ss       = hf.render(summary, True, styles.COLOR_ACCENT)
        screen.blit(ss, (cx - ss.get_width()//2,
                          sum_rect.centery - ss.get_height()//2))

        self.btn_play.draw(screen)
        self.btn_back.draw(screen)

    def _draw_option_row(self, screen, btns, values, current):
        for btn, val in zip(btns, values):
            is_sel = (val == current)
            if is_sel:
                # Highlight selected option
                styles.draw_glow_border(screen, btn.rect, styles.COLOR_PRIMARY, intensity=0.6)
            btn.draw(screen)
            if is_sel:
                check = styles.font_hint().render("✓", True, styles.COLOR_PRIMARY)
                screen.blit(check, (btn.rect.right + 2, btn.rect.top - 1))

    def _draw_rule_row(self, screen):
        for i, btn in enumerate(self.rule_btns):
            is_sel = (i == int(self.is_deathmatch))
            if is_sel:
                styles.draw_glow_border(screen, btn.rect, styles.COLOR_PRIMARY, intensity=0.6)
            btn.draw(screen)
            if is_sel:
                check = styles.font_hint().render("✓", True, styles.COLOR_PRIMARY)
                screen.blit(check, (btn.rect.right + 2, btn.rect.top - 1))
