import pygame
import math
from src.graphics import styles
from src.graphics.ui_system import PixelButton, StatBar, FeedbackMessage
from src.utils.localization import lang

class ProfileState:
    """
    Fighter Profile — Detailed view with stat allocation.
    Left: portrait + account stats.  Right: attributes + XP bar.
    """
    def __init__(self, manager):
        self.manager   = manager
        self._time     = 0.0
        self.feedback  = FeedbackMessage(duration=2.5)

        self.btn_back = PixelButton(manager, "← COLECCIÓN", (8, 8), size=(88, 22),
                                    callback=self.go_back, variant="ghost")
        self.load_fighter_data()

    def load_fighter_data(self):
        acc = self.manager.data_manager.active_p1
        idx = getattr(self.manager, "selected_fighter_idx", 0)
        self.fighter = acc.fighters[idx] if acc and len(acc.fighters) > idx else None
        self.acc     = acc
        self.portrait = None

        if self.fighter and self.fighter.portrait_path:
            try:
                img = pygame.image.load(self.fighter.portrait_path).convert_alpha()
                self.portrait = pygame.transform.scale(img, (110, 110))
            except Exception:
                pass

        # Build stat bars
        self.stat_bars = []
        if self.fighter:
            st = self.fighter.stats
            cap = 50   # Reference max for visual bar
            bar_data = [
                ("FUERZA",    st.fuerza,              cap,  styles.COLOR_PRIMARY),
                ("PODER",     st.poder,               cap,  styles.COLOR_INFO),
                ("VELOCIDAD", st.velocidad,            cap,  styles.COLOR_SUCCESS),
                ("RESISTENCIA",st.resistencia_fisica,  cap,  styles.COLOR_WARNING),
            ]
            for i, (label, val, mx, col) in enumerate(bar_data):
                bar_y = styles.CONTENT_TOP + 40 + i*20
                bar = StatBar(self.manager, (185, bar_y), (200, 14),
                              label=label, value=val, max_value=mx, color=col)
                self.stat_bars.append(bar)

        # Stat allocation buttons
        self.stat_btns = []
        if self.fighter and self.fighter.stat_points > 0:
            for i, stat in enumerate(["fuerza", "poder", "velocidad"]):
                bar_y = styles.CONTENT_TOP + 40 + i*20
                btn = PixelButton(self.manager, "+",
                                   (392, bar_y), size=(18, 14),
                                   callback=lambda s=stat: self.spend_point(s),
                                   variant="success", font_size=10,
                                   tooltip_text=f"Gastar punto en {stat.upper()}")
                self.stat_btns.append(btn)

    def spend_point(self, stat_name):
        acc = self.manager.data_manager.active_p1
        if self.manager.data_manager.assign_stat(acc, self.fighter, stat_name):
            self.manager.data_manager.play_sfx("stat")
            self.feedback.show(f"¡{stat_name.upper()} AUMENTADO!", kind="success")
            self.load_fighter_data()
        else:
            self.feedback.show("SIN PUNTOS DISPONIBLES", kind="error")

    def go_back(self):
        self.manager.change_state("roster")

    def update(self, dt, events):
        self._time += dt
        for event in events:
            if event.type == pygame.KEYDOWN and \
               event.key == self.manager.data_manager.get_key("BACK"):
                self.go_back()
            self.btn_back.handle_event(event)
            for btn in self.stat_btns:
                btn.handle_event(event)

        self.btn_back.update(dt)
        for bar in self.stat_bars:
            bar.update(dt)
        for btn in self.stat_btns:
            btn.update(dt)
        self.feedback.update(dt)

    # ── Drawing ──────────────────────────────────────────────────────

    def draw(self, screen):
        screen.fill(styles.COLOR_BG)
        styles.draw_scanlines(screen, alpha=14)

        if not self.fighter:
            screen.blit(styles.font_body().render("SIN DATOS", True, styles.COLOR_ERROR),
                        (styles.BASE_WIDTH//2 - 30, 120))
            self.btn_back.draw(screen)
            return

        f = self.fighter

        # ── Header ────────────────────────────────────────────
        styles.draw_header(screen, f.name.upper(),
                           subtitle_text=f"NIVEL {f.level}  •  {f.elemental_affinity.upper()}",
                           border_color=styles.COLOR_PRIMARY)

        # ── LEFT PANEL — Portrait + Account ───────────────────
        left_rect = pygame.Rect(10, styles.CONTENT_TOP, 150, 190)
        styles.draw_panel(screen, left_rect, border_color=styles.COLOR_BORDER)

        if self.portrait:
            screen.blit(self.portrait, (25, styles.CONTENT_TOP + 8))
            pygame.draw.rect(screen, styles.COLOR_BORDER,
                              (25, styles.CONTENT_TOP+8, 110, 110), 1)
        else:
            ph = pygame.Surface((110, 110), pygame.SRCALPHA)
            pygame.draw.rect(ph, (45, 45, 65, 200), ph.get_rect(), border_radius=3)
            pygame.draw.circle(ph, (80, 80, 105), (55, 35), 18)
            pygame.draw.rect(ph, (80, 80, 105), pygame.Rect(32, 56, 46, 44))
            screen.blit(ph, (25, styles.CONTENT_TOP + 8))

        # Elemental affinity badge
        aff_color = {
            "fuego": (255, 100, 30), "agua": (60, 160, 255),
            "tierra": (180, 140, 60), "rayo": (255, 230, 0),
            "viento": (150, 255, 180), "sombra": (160, 80, 255),
        }.get(f.elemental_affinity.lower(), styles.COLOR_ACCENT)
        aff_surf = styles.font_hint().render(
            f.elemental_affinity.upper(), True, aff_color)
        aff_bar  = pygame.Rect(25, styles.CONTENT_TOP + 122, 110, 12)
        pygame.draw.rect(screen, (*aff_color, 40),
                          aff_bar, border_radius=2)
        pygame.draw.rect(screen, aff_color, aff_bar, 1, border_radius=2)
        screen.blit(aff_surf,
                    (aff_bar.centerx - aff_surf.get_width()//2,
                     aff_bar.centery - aff_surf.get_height()//2))

        # Fighter XP Bar (Moved from Right Panel)
        xp_y = styles.CONTENT_TOP + 144
        xp_txt = styles.font_hint().render(f"XP: {f.xp}/{f.level*50}", True, styles.COLOR_WHITE)
        screen.blit(xp_txt, (left_rect.centerx - xp_txt.get_width()//2, xp_y))
        
        xp_pct  = f.xp / max(1, f.level * 50)
        xp_rect = pygame.Rect(left_rect.centerx - 55, xp_y + 12, 110, 8)
        styles.draw_stat_bar(screen, xp_rect, xp_pct, styles.COLOR_XP_BAR)
        
        lvl_hint = styles.get_font(8).render(f"SIGUIENTE: {max(0, f.level*50-f.xp)} XP", True, styles.COLOR_MUTED)
        screen.blit(lvl_hint, (left_rect.centerx - lvl_hint.get_width()//2, xp_y + 24))

        # ── RIGHT PANEL — Stats ────────────────────────────────
        right_rect = pygame.Rect(170, styles.CONTENT_TOP, 290, 190)
        styles.draw_panel(screen, right_rect, border_color=styles.COLOR_BORDER)

        # Section: ATRIBUTOS
        sec_font = styles.font_caption(bold=True)
        screen.blit(sec_font.render("ATRIBUTOS Y DESARROLLO", True, styles.COLOR_SECONDARY),
                    (178, styles.CONTENT_TOP + 6))
        pygame.draw.line(screen, styles.COLOR_BORDER,
                          (178, styles.CONTENT_TOP + 18),
                          (452, styles.CONTENT_TOP + 18), 1)

        # Puntos Disponibles
        if f.stat_points > 0:
            pts_surf  = sec_font.render(f"PUNTOS DE MEJORA: {f.stat_points}", True, styles.COLOR_SUCCESS)
            screen.blit(pts_surf, (178, styles.CONTENT_TOP + 22))
        else:
            nd = styles.font_hint().render("Gana combates para obtener puntos", True, styles.COLOR_DISABLED)
            screen.blit(nd, (178, styles.CONTENT_TOP + 22))

        # Draw Stat Bars
        for bar in self.stat_bars:
            bar.draw(screen)

        # Draw Stats Buttons
        if f.stat_points > 0:
            for btn in self.stat_btns:
                btn.draw(screen)

        # Section: MOVIMIENTOS
        mv_y = styles.CONTENT_TOP + 130
        screen.blit(sec_font.render("MOVIMIENTOS DE COMBATE", True, styles.COLOR_PRIMARY),
                    (178, mv_y))
        pygame.draw.line(screen, styles.COLOR_BORDER, (178, mv_y+12), (452, mv_y+12), 1)
        
        if f.moves:
            for j, mv in enumerate(f.moves[:4]):
                tag_col = styles.COLOR_PRIMARY if mv.type == "Fisico" else styles.COLOR_INFO
                tag     = "[F]" if mv.type == "Fisico" else "[M]"
                tx      = 178 + (130 * (j % 2))
                ty      = mv_y + 18 + (16 * (j // 2))
                tx     += styles.draw_tag(screen, tag, (tx, ty), tag_col) + 4
                ms      = styles.font_hint().render(mv.name, True, styles.COLOR_WHITE)
                screen.blit(ms, (tx, ty))
        else:
            screen.blit(styles.font_hint().render("Sin movimientos aprendidos", True, styles.COLOR_DISABLED), (178, mv_y+16))

        self.feedback.draw(screen, y=styles.BASE_HEIGHT - 18)
        self.btn_back.draw(screen)
