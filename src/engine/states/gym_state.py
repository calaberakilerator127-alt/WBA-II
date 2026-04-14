import pygame
import math
from src.graphics import styles
from src.graphics.ui_system import PixelButton, ProgressBar, FeedbackMessage, NavBar
from src.utils.localization import lang

class GymState:
    """
    Training Institute — Physical and Magical exercise selection.
    Clear mode tabs, exercise list, animated progress bar, resource display.
    """
    def __init__(self, manager):
        self.manager  = manager
        self._time    = 0.0
        self.feedback = FeedbackMessage(duration=2.5)

        self.acc    = manager.data_manager.active_p1
        self.roster = self.acc.fighters if self.acc else []
        self.fighter_idx      = 0
        self.view_mode        = 0     # 0=Fisico, 1=Magico
        self.training_progress= 0.0
        self.selected_ex_idx  = 0

        manager.data_manager.play_music(styles.ASSET_PATHS["music"]["gym"])

        # Buttons
        self.btn_back  = PixelButton(manager, "← HUB", (8, 8), size=(60, 22),
                                     callback=lambda: manager.change_state("menu"),
                                     variant="ghost")
        self.btn_prev_f = PixelButton(manager, "<", (8, styles.CONTENT_TOP+2),
                                      size=(22, 22), callback=lambda: self.switch_f(-1),
                                      variant="ghost")
        self.btn_next_f = PixelButton(manager, ">", (130, styles.CONTENT_TOP+2),
                                      size=(22, 22), callback=lambda: self.switch_f(1),
                                      variant="ghost")
        self.btn_phys = PixelButton(manager, "FÍSICO", (8, styles.CONTENT_TOP+32),
                                    size=(75, 22), callback=lambda: self.set_mode(0))
        self.btn_mag  = PixelButton(manager, "MÁGICO", (88, styles.CONTENT_TOP+32),
                                    size=(75, 22), callback=lambda: self.set_mode(1))
        self.nav_bar  = NavBar(manager, current_state="gym")

        self.progress_bar = ProgressBar(manager, (10, 185), size=(230, 12),
                                         color=styles.COLOR_PRIMARY)

        # Load exercises
        db = manager.data_manager.load_database()
        self.phys_exercises = db.get("physical_exercises", [])
        self.mag_exercises  = db.get("magical_trainings", [])

    def switch_f(self, delta):
        if not self.roster: return
        self.fighter_idx = (self.fighter_idx + delta) % len(self.roster)
        self.training_progress = 0.0
        self.feedback.show("", kind="info")

    def set_mode(self, mode):
        if self.view_mode == mode: return
        self.view_mode = mode
        self.training_progress = 0.0
        self.selected_ex_idx = 0
        self.progress_bar.color = styles.COLOR_PRIMARY if mode==0 else styles.COLOR_ENERGY_BAR

    def train(self, fighter):
        if not fighter: return
        ex_list  = self.phys_exercises if self.view_mode==0 else self.mag_exercises
        if not ex_list or self.selected_ex_idx >= len(ex_list): return
        ex       = ex_list[self.selected_ex_idx]
        cost     = ex.get("stamina_cost", 10) if self.view_mode==0 else ex.get("energy_cost", 10)
        resource = fighter.estamina if self.view_mode==0 else fighter.energia
        res_name = "ESTAMINA" if self.view_mode==0 else "ENERGÍA"

        if resource >= cost:
            self.training_progress = min(1.0, self.training_progress + 0.25)
            self.progress_bar.set_percent(self.training_progress)
            if self.training_progress >= 1.0:
                self.training_progress = 0.0
                if self.view_mode==0: fighter.estamina -= cost
                else:                 fighter.energia  -= cost
                stat_target = ex.get("stat", "fuerza")
                gain        = ex.get("gain", 1)
                if stat_target == "fuerza":    fighter.stats.fuerza    += gain
                elif stat_target == "poder":   fighter.stats.poder     += gain
                elif stat_target == "velocidad": fighter.stats.velocidad += gain
                leveled = self.manager.data_manager.add_xp(self.acc, fighter, 20)
                if leveled:
                    self.feedback.show(f"¡LEVEL UP! +{stat_target.upper()} +{gain}", kind="success")
                else:
                    self.feedback.show(f"+{gain} {stat_target.upper()}!", kind="success")
                self.manager.data_manager.play_sfx("stat")
        else:
            self.feedback.show(f"¡{res_name} INSUFICIENTE!", kind="error")

    def update(self, dt, events):
        self._time += dt
        fighter = self.roster[self.fighter_idx] if self.roster else None

        for event in events:
            if event.type == pygame.KEYDOWN:
                d = self.manager.data_manager
                if event.key == d.get_key("TRAIN"):
                    self.train(fighter)
                elif event.key == d.get_key("BACK"):
                    self.manager.change_state("menu")
                elif event.key == d.get_key("UP"):
                    ex_list = self.phys_exercises if self.view_mode==0 else self.mag_exercises
                    self.selected_ex_idx = (self.selected_ex_idx-1) % max(1,len(ex_list))
                elif event.key == d.get_key("DOWN"):
                    ex_list = self.phys_exercises if self.view_mode==0 else self.mag_exercises
                    self.selected_ex_idx = (self.selected_ex_idx+1) % max(1,len(ex_list))

            self.btn_back.handle_event(event)
            self.btn_prev_f.handle_event(event)
            self.btn_next_f.handle_event(event)
            self.btn_phys.handle_event(event)
            self.btn_mag.handle_event(event)
            self.nav_bar.handle_event(event)

        self.btn_back.update(dt)
        self.btn_prev_f.update(dt)
        self.btn_next_f.update(dt)
        self.btn_phys.update(dt)
        self.btn_mag.update(dt)
        self.progress_bar.update(dt)
        self.nav_bar.update(dt)
        self.feedback.update(dt)

    def draw(self, screen):
        screen.fill(styles.COLOR_BG)
        styles.draw_scanlines(screen, alpha=14)

        # Header
        styles.draw_header(screen, "INSTITUTO DE ENTRENAMIENTO",
                           subtitle_text="FORTALECE A TUS LUCHADORES",
                           border_color=styles.COLOR_PRIMARY)

        fighter = self.roster[self.fighter_idx] if self.roster else None
        if not fighter:
            screen.blit(styles.font_body().render("SIN LUCHADORES", True, styles.COLOR_ERROR),
                        (styles.BASE_WIDTH//2-60, 120))
            self.btn_back.draw(screen)
            return

        # ── Fighter selector ────────────────────────────────────
        f_sel_rect = pygame.Rect(34, styles.CONTENT_TOP+2, 93, 22)
        styles.draw_panel(screen, f_sel_rect, border_color=styles.COLOR_BORDER)
        f_font = styles.font_caption(bold=True)
        f_surf = f_font.render(fighter.name.upper()[:12], True, styles.COLOR_WHITE)
        screen.blit(f_surf, (f_sel_rect.centerx - f_surf.get_width()//2,
                              f_sel_rect.centery - f_surf.get_height()//2))
        self.btn_prev_f.draw(screen)
        self.btn_next_f.draw(screen)

        # ── Mode Tabs ──────────────────────────────────────────
        # Draw underline on active tab
        for i, btn in enumerate([self.btn_phys, self.btn_mag]):
            is_active = (i == self.view_mode)
            btn.variant = "primary" if is_active else "ghost"
            var = PixelButton.VARIANTS[btn.variant]
            btn.color_normal = var[1]
            btn.color_hover  = var[0]
            btn.draw(screen)
            if is_active:
                pygame.draw.line(screen, styles.COLOR_PRIMARY,
                                  (btn.rect.x, btn.rect.bottom),
                                  (btn.rect.right, btn.rect.bottom), 2)

        col_tab = styles.COLOR_PRIMARY if self.view_mode==0 else styles.COLOR_ENERGY_BAR

        # ── Left Panel — Exercise List ─────────────────────────
        left_rect  = pygame.Rect(8, styles.CONTENT_TOP+62, 240, 105)
        styles.draw_panel(screen, left_rect, border_color=styles.COLOR_BORDER)
        ex_list    = self.phys_exercises if self.view_mode==0 else self.mag_exercises
        sec_font   = styles.font_caption(bold=True)
        hint_font  = styles.font_hint()
        machine_name = "BANCO DE FUERZA" if self.view_mode==0 else "NODO DE MEDITACIÓN"
        screen.blit(sec_font.render(machine_name, True, styles.COLOR_SECONDARY),
                    (12, styles.CONTENT_TOP+66))
        pygame.draw.line(screen, styles.COLOR_BORDER,
                          (12, styles.CONTENT_TOP+78),
                          (242, styles.CONTENT_TOP+78), 1)

        current_y = styles.CONTENT_TOP + 82
        max_vis = 4
        n_ex = len(ex_list) if ex_list else 0
        start_idx = max(0, min(self.selected_ex_idx - 1, n_ex - max_vis)) if n_ex > max_vis else 0

        for i in range(max_vis):
            idx = start_idx + i
            if idx >= n_ex: break
            is_sel     = (idx == self.selected_ex_idx)
            ex = ex_list[idx]
            base_color = col_tab if is_sel else styles.COLOR_WHITE
            
            if is_sel:
                hi = pygame.Surface((230, 24), pygame.SRCALPHA)
                hi.fill((*col_tab, 30))
                screen.blit(hi, (10, current_y-2))
                pygame.draw.polygon(screen, col_tab,
                                    [(12, current_y+3), (12, current_y+9), (17, current_y+6)])

            stat = ex.get("stat", "?").upper()
            gain = ex.get("gain", 1)
            cost_key = "stamina_cost" if self.view_mode==0 else "energy_cost"
            cost = ex.get(cost_key, 10)
            name_str = ex.get("name", "?").upper()
            
            ex_surf = hint_font.render(name_str, True, base_color)
            screen.blit(ex_surf, (22, current_y))

            if is_sel:
                detail = hint_font.render(f"+{gain} {stat}  •  COSTO: {cost}",
                                           True, styles.COLOR_MUTED)
                screen.blit(detail, (22, current_y+11))
                current_y += 26
            else:
                current_y += 16

        # ── Training Progress Bar ─────────────────────────────
        prog_y = left_rect.bottom + 16
        screen.blit(sec_font.render("PROGRESO", True, styles.COLOR_MUTED), (10, prog_y-12))
        self.progress_bar.rect.y = prog_y
        self.progress_bar.draw(screen)
        pct_surf = hint_font.render(f"{int(self.training_progress*100)}%",
                                     True, styles.COLOR_WHITE)
        screen.blit(pct_surf, (245, prog_y))

        # ── Right Panel — Fighter Stats ────────────────────────
        right_rect = pygame.Rect(256, styles.CONTENT_TOP+2, 215, 160)
        styles.draw_panel(screen, right_rect, border_color=styles.COLOR_BORDER)

        screen.blit(sec_font.render("ESTADÍSTICAS", True, styles.COLOR_SECONDARY),
                    (262, styles.CONTENT_TOP+8))
        pygame.draw.line(screen, styles.COLOR_BORDER,
                          (262, styles.CONTENT_TOP+20),
                          (464, styles.CONTENT_TOP+20), 1)

        st       = fighter.stats
        res_val  = fighter.estamina if self.view_mode==0 else fighter.energia
        res_max  = st.estamina_max  if self.view_mode==0 else st.energia_max
        res_col  = styles.COLOR_STAMINA_BAR if self.view_mode==0 else styles.COLOR_ENERGY_BAR
        res_name = "ESTAMINA" if self.view_mode==0 else "ENERGÍA"

        stat_data = [
            ("FUERZA",   st.fuerza,           50, styles.COLOR_PRIMARY),
            ("PODER",    st.poder,             50, styles.COLOR_INFO),
            ("VELOCIDAD",st.velocidad,          50, styles.COLOR_SUCCESS),
            (res_name,   int(res_val), int(res_max), res_col),
        ]
        for i, (lbl, val, mx, col) in enumerate(stat_data):
            sy = styles.CONTENT_TOP + 26 + i*20
            lbl_s = hint_font.render(lbl, True, styles.COLOR_MUTED)
            screen.blit(lbl_s, (262, sy))
            bar_r = pygame.Rect(330, sy+2, 100, 8)
            styles.draw_stat_bar(screen, bar_r, val/max(1,mx), col)
            val_s = hint_font.render(str(val), True, col)
            screen.blit(val_s, (435, sy))

        # Level + XP
        lv_surf = sec_font.render(f"NIVEL {fighter.level}", True, styles.COLOR_ACCENT)
        screen.blit(lv_surf, (262, styles.CONTENT_TOP+112))
        xp_pct  = fighter.xp / max(1, fighter.level*50)
        xp_bar  = pygame.Rect(334, styles.CONTENT_TOP+114, 120, 8)
        styles.draw_stat_bar(screen, xp_bar, xp_pct, styles.COLOR_XP_BAR)
        xp_lbl  = hint_font.render(f"XP {fighter.xp}/{fighter.level*50}",
                                    True, styles.COLOR_MUTED)
        screen.blit(xp_lbl, (262, styles.CONTENT_TOP+126))

        # Instruction
        key_name = pygame.key.name(self.manager.data_manager.get_key("TRAIN")).upper()
        if key_name == "SPACE": key_name = "ESPACIO"
        instr = hint_font.render(
            f"↑↓ ELEGIR  •  [{key_name}] ENTRENAR",
            True, styles.COLOR_DISABLED)
        screen.blit(instr, (262, right_rect.bottom + 6))

        self.feedback.draw(screen, y=styles.BASE_HEIGHT - styles.NAV_HEIGHT - 12)
        self.btn_back.draw(screen)
        self.nav_bar.draw(screen)
