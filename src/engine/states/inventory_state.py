import pygame
from src.graphics import styles
from src.graphics.ui_system import PixelButton, FeedbackMessage, NavBar
from src.utils.localization import lang

# Item category icons and colors
ITEM_META = {
    "Comodín":    ("🃏", styles.COLOR_SECONDARY, "Omite requisito de nivel en el LAB"),
    "Proteína":   ("💪", styles.COLOR_PRIMARY,   "Aumenta FUERZA de un luchador permanentemente"),
    "Energizante":("⚡", styles.COLOR_ENERGY_BAR,"Aumenta ENERGÍA MÁXIMA permanentemente"),
    "Botiquín":   ("💊", (80, 230, 140),          "Restaura el 100% de HP fuera de combate"),
    "Entrada VIP":("🎫", styles.COLOR_WARNING,   "Acceso a torneos especiales del Campeonato"),
}

class InventoryState:
    """
    Inventory (Mochila) — View and use collected items.
    Left panel: categorized item list. Right panel: item detail + usage mode.
    """
    def __init__(self, manager):
        self.manager     = manager
        self.acc         = manager.data_manager.active_p1
        self.items       = self.acc.inventory if self.acc else {}
        self.item_list   = list(self.items.items())
        self._time       = 0.0
        self.cursor_idx  = 0
        self.usage_mode  = False
        self.target_idx  = 0
        self.feedback    = FeedbackMessage(duration=2.5)

        self.btn_back  = PixelButton(manager, "← HUB", (8, 8), size=(60, 22),
                                     callback=self.go_back, variant="ghost")
        self.btn_use   = PixelButton(manager, "USAR OBJETO",
                                     (styles.BASE_WIDTH//2 + 20,
                                      styles.BASE_HEIGHT - styles.NAV_HEIGHT - 38),
                                     size=(110, 26), callback=self.enter_usage,
                                     variant="primary",
                                     tooltip_text="Usar el objeto en un luchador")
        self.btn_prev_f= PixelButton(manager, "◄", (240, 140), size=(22, 22),
                                     callback=lambda: self.switch_target(-1), variant="ghost")
        self.btn_next_f= PixelButton(manager, "►", (418, 140), size=(22, 22),
                                     callback=lambda: self.switch_target(1), variant="ghost")
        self.btn_confirm_use = PixelButton(manager, "✓ CONFIRMAR USO",
                                           (270, 185), size=(130, 26),
                                           callback=self.execute_usage, variant="success")
        self.btn_cancel_use  = PixelButton(manager, "CANCELAR", (270, 216),
                                           size=(130, 22), callback=self.cancel_usage,
                                           variant="ghost")
        self.nav_bar = NavBar(manager, current_state="inventory")

    def go_back(self):
        if self.usage_mode:
            self.usage_mode = False
        else:
            self.manager.change_state("menu")

    def enter_usage(self):
        if not self.item_list:
            self.feedback.show("MOCHILA VACÍA", kind="error")
            return
        self.usage_mode = True

    def cancel_usage(self):
        self.usage_mode = False

    def switch_target(self, delta):
        fighters = self.acc.fighters
        if not fighters: return
        self.target_idx = (self.target_idx + delta) % len(fighters)

    def execute_usage(self):
        if not self.item_list: return
        item_name = self.item_list[self.cursor_idx][0]
        fighter   = self.acc.fighters[self.target_idx]
        res = self.manager.data_manager.use_item(self.acc, fighter, item_name)
        kind = "success" if res.get("success") else "error"
        self.feedback.show(res.get("message", ""), kind=kind)
        if res.get("success"):
            self.manager.data_manager.play_sfx("stat")
            self.usage_mode = False
            self.item_list  = list(self.acc.inventory.items())
            self.cursor_idx = min(self.cursor_idx, max(0, len(self.item_list)-1))

    def update(self, dt, events):
        self._time += dt
        n = max(1, len(self.item_list))

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN:
                    self.cursor_idx = (self.cursor_idx+1) % n
                elif event.key == pygame.K_UP:
                    self.cursor_idx = (self.cursor_idx-1) % n
                elif event.key == pygame.K_ESCAPE:
                    self.go_back()

            self.btn_back.handle_event(event)
            if not self.usage_mode:
                self.btn_use.handle_event(event)
            else:
                self.btn_prev_f.handle_event(event)
                self.btn_next_f.handle_event(event)
                self.btn_confirm_use.handle_event(event)
                self.btn_cancel_use.handle_event(event)
            self.nav_bar.handle_event(event)

        self.btn_back.update(dt)
        self.btn_use.update(dt)
        self.btn_prev_f.update(dt)
        self.btn_next_f.update(dt)
        self.btn_confirm_use.update(dt)
        self.btn_cancel_use.update(dt)
        self.nav_bar.update(dt)
        self.feedback.update(dt)

    def draw(self, screen):
        screen.fill(styles.COLOR_BG)
        styles.draw_scanlines(screen, alpha=14)
        styles.draw_header(screen, "MI MOCHILA",
                           subtitle_text="OBJETOS RECOLECTADOS")

        # ── Item List (left) ─────────────────────────────────────
        list_rect = pygame.Rect(8, styles.CONTENT_TOP+2, 215, 160)
        styles.draw_panel(screen, list_rect, border_color=styles.COLOR_BORDER)

        hf = styles.font_hint()
        mc = styles.font_caption(bold=True)

        if not self.item_list:
            em = styles.font_body().render("MOCHILA VACÍA", True, styles.COLOR_MUTED)
            screen.blit(em, (list_rect.centerx - em.get_width()//2,
                              list_rect.centery - em.get_height()//2))
        else:
            max_vis = 8
            start_idx = max(0, min(self.cursor_idx - 3, len(self.item_list) - max_vis)) if len(self.item_list) > max_vis else 0
            
            for i in range(max_vis):
                idx = start_idx + i
                if idx >= len(self.item_list): break
                name, qty = self.item_list[idx]
                iy     = styles.CONTENT_TOP + 8 + i * 20
                is_sel = (idx == self.cursor_idx)
                meta   = ITEM_META.get(name, ("■", styles.COLOR_MUTED, ""))
                icon, color, _ = meta

                if is_sel:
                    hi = pygame.Surface((213, 18), pygame.SRCALPHA)
                    hi.fill((*color, 25))
                    screen.blit(hi, (9, iy-1))
                    pygame.draw.rect(screen, color, (9, iy-1, 3, 18))

                # Icon tag
                icon_surf = hf.render(icon, True, color)
                screen.blit(icon_surf, (14, iy+1))

                # Item name
                name_col  = color if is_sel else styles.COLOR_WHITE
                name_surf = hf.render(name, True, name_col)
                screen.blit(name_surf, (30, iy+1))

                # Qty badge
                qty_surf = hf.render(f"x{qty}", True, styles.COLOR_SECONDARY)
                screen.blit(qty_surf, (list_rect.right - qty_surf.get_width() - 6, iy+1))

        # ── Detail / Usage Panel (right) ─────────────────────────
        right_rect = pygame.Rect(230, styles.CONTENT_TOP+2, 240, 160)

        if not self.usage_mode:
            styles.draw_panel(screen, right_rect, border_color=styles.COLOR_BORDER)
            screen.blit(mc.render("DETALLE", True, styles.COLOR_SECONDARY),
                        (238, styles.CONTENT_TOP+8))
            pygame.draw.line(screen, styles.COLOR_BORDER,
                              (238, styles.CONTENT_TOP+20),
                              (462, styles.CONTENT_TOP+20), 1)

            if self.item_list:
                curr_name = self.item_list[self.cursor_idx][0]
                meta      = ITEM_META.get(curr_name, ("■", styles.COLOR_MUTED, "Sin descripción."))
                icon, color, desc = meta

                # Icon large
                icon_lg = styles.get_font(24).render(icon, True, color)
                screen.blit(icon_lg, (238, styles.CONTENT_TOP+24))

                # Name
                nf = styles.font_body(bold=True)
                ns = nf.render(curr_name.upper(), True, color)
                screen.blit(ns, (268, styles.CONTENT_TOP+26))

                # Description (word-wrapped)
                words  = desc.split()
                lines  = []
                line   = ""
                for w in words:
                    if len(line+w) <= 28: line += w+" "
                    else:
                        lines.append(line.strip()); line=w+" "
                lines.append(line.strip())
                for j, l in enumerate(lines):
                    ls = hf.render(l, True, styles.COLOR_MUTED)
                    screen.blit(ls, (238, styles.CONTENT_TOP+44+j*13))

                qty_txt = hf.render(f"CANTIDAD: {self.item_list[self.cursor_idx][1]}",
                                     True, styles.COLOR_WHITE)
                screen.blit(qty_txt, (238, styles.CONTENT_TOP+96))

            self.btn_use.draw(screen)

        else:
            # ── Usage Mode Overlay ─────────────────────────────
            styles.draw_panel(screen, right_rect, border_color=styles.COLOR_ACCENT,
                              bg_color=styles.COLOR_PANEL_BG2)
            styles.draw_glow_border(screen, right_rect, styles.COLOR_ACCENT, intensity=0.5)
            screen.blit(mc.render("¿USAR EN QUIÉN?", True, styles.COLOR_WHITE),
                        (right_rect.centerx - mc.render("¿USAR EN QUIÉN?", True, styles.COLOR_WHITE).get_width()//2,
                         styles.CONTENT_TOP+8))

            if self.acc.fighters:
                f     = self.acc.fighters[self.target_idx]
                hp_pct= f.hp / max(1, f.max_hp)
                fn    = styles.font_body(bold=True)
                fs    = fn.render(f.name.upper(), True, styles.COLOR_PRIMARY)
                cx    = right_rect.centerx
                screen.blit(fs, (cx - fs.get_width()//2, 130))

                # Fighter HP
                hp_bar = pygame.Rect(cx-80, 146, 160, 8)
                styles.draw_stat_bar(screen, hp_bar, hp_pct, styles.COLOR_HP_BAR)
                hp_txt = hf.render(f"HP: {int(f.hp)}/{int(f.max_hp)}", True, styles.COLOR_MUTED)
                screen.blit(hp_txt, (cx - hp_txt.get_width()//2, 156))

            self.btn_prev_f.draw(screen)
            self.btn_next_f.draw(screen)
            self.btn_confirm_use.draw(screen)
            self.btn_cancel_use.draw(screen)

        self.feedback.draw(screen, y=styles.BASE_HEIGHT - styles.NAV_HEIGHT - 12)
        self.btn_back.draw(screen)
        self.nav_bar.draw(screen)
