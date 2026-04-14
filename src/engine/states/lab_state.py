import pygame
import math
from src.graphics import styles
from src.graphics.ui_system import PixelButton, ConfirmationDialog, FeedbackMessage, NavBar
from src.utils.localization import lang

LAB_COLOR = (100, 180, 255)   # Lab blue theme

class LabState:
    """
    Laboratory — Purchase physical and magical combat moves.
    Category navigator, move list with lock indicators, detail preview panel.
    """
    def __init__(self, manager):
        self.manager         = manager
        self._time           = 0.0
        self.feedback        = FeedbackMessage(duration=2.5)
        self.db              = manager.data_manager.load_database()
        self.categories      = ["FISICO"] + self.db.get("magic_elements", [])
        self.current_cat_idx = 0
        self.selected_move_idx = 0
        self.dialog          = None

        manager.data_manager.play_music(styles.ASSET_PATHS["music"]["lab"])

        self.btn_back = PixelButton(manager, "← HUB", (8, 8), size=(60, 22),
                                    callback=self.go_back, variant="ghost")
        self.btn_cat_prev = PixelButton(manager, "◄", (8, 72), size=(22, 22),
                                        callback=lambda: self.shift_cat(-1), variant="ghost")
        self.btn_cat_next = PixelButton(manager, "►", (styles.BASE_WIDTH-30, 72),
                                        size=(22, 22), callback=lambda: self.shift_cat(1),
                                        variant="ghost")
        self.btn_buy = PixelButton(manager, lang.get("btn_buy"),
                                   (styles.BASE_WIDTH - 115, styles.BASE_HEIGHT - styles.NAV_HEIGHT - 36),
                                   size=(105, 26), callback=self.confirm_purchase,
                                   variant="success")
        self.nav_bar = NavBar(manager, current_state="lab")

    def go_back(self):
        self.manager.change_state("menu")

    def shift_cat(self, delta):
        self.current_cat_idx = (self.current_cat_idx + delta) % len(self.categories)
        self.selected_move_idx = 0

    def _get_move_list(self):
        cat = self.categories[self.current_cat_idx]
        if cat == "FISICO":
            return self.db.get("physical_attacks", [])
        return self.db.get("magic_attacks", {}).get(cat, [])

    def confirm_purchase(self):
        move_list = self._get_move_list()
        if not move_list: return
        self.selected_move_idx = max(0, min(len(move_list)-1, self.selected_move_idx))
        move = move_list[self.selected_move_idx]
        self.dialog = ConfirmationDialog(
            self.manager,
            f"¿Comprar {move['name']} por {move['cost']}B?",
            self.try_buy, self.close_dialog
        )

    def close_dialog(self):
        self.dialog = None

    def try_buy(self):
        acc       = self.manager.data_manager.active_p1
        move_list = self._get_move_list()
        if not move_list or not acc: return
        move = move_list[self.selected_move_idx]
        fighter  = acc.fighters[0] if acc.fighters else None
        self.close_dialog()
        if not fighter:
            self.feedback.show("SIN LUCHADOR DISPONIBLE", kind="error")
            return
        res = self.manager.data_manager.buy_move(acc, fighter, move)
        if res.get("success"):
            self.manager.data_manager.play_sfx("stat")
            self.feedback.show(f"¡{move['name'].upper()} APRENDIDO!", kind="success")
        else:
            self.feedback.show(res.get("message", "ERROR"), kind="error")

    def update(self, dt, events):
        self._time += dt

        if self.dialog:
            for event in events:
                if self.dialog:
                    self.dialog.handle_event(event)
            if self.dialog:
                self.dialog.update(dt)
            return

        move_list = self._get_move_list()
        n_moves   = max(1, len(move_list))

        for event in events:
            if event.type == pygame.KEYDOWN:
                d = self.manager.data_manager
                if event.key == d.get_key("RIGHT"):  self.shift_cat(1)
                elif event.key == d.get_key("LEFT"):  self.shift_cat(-1)
                elif event.key == d.get_key("DOWN"):
                    self.selected_move_idx = (self.selected_move_idx+1) % n_moves
                elif event.key == d.get_key("UP"):
                    self.selected_move_idx = (self.selected_move_idx-1) % n_moves
                elif event.key == d.get_key("BACK"):  self.go_back()
                elif event.key == d.get_key("CONFIRM"): self.confirm_purchase()

            self.btn_back.handle_event(event)
            self.btn_cat_prev.handle_event(event)
            self.btn_cat_next.handle_event(event)
            self.btn_buy.handle_event(event)
            self.nav_bar.handle_event(event)

        self.btn_back.update(dt)
        self.btn_cat_prev.update(dt)
        self.btn_cat_next.update(dt)
        self.btn_buy.update(dt)
        self.nav_bar.update(dt)
        self.feedback.update(dt)

    def draw(self, screen):
        screen.fill(styles.COLOR_BG)
        styles.draw_scanlines(screen, alpha=14)

        # Header — lab blue theme
        styles.draw_header(screen, "LABORATORIO DE TÉCNICAS",
                           subtitle_text="COMPRA MOVIMIENTOS PARA TUS LUCHADORES",
                           title_color=LAB_COLOR,
                           border_color=LAB_COLOR)

        acc     = self.manager.data_manager.active_p1
        fighter = acc.fighters[0] if acc and acc.fighters else None

        # Brawels display
        if acc:
            bf = styles.font_caption(bold=True)
            bs = bf.render(f"💰 {acc.brawels} B", True, styles.COLOR_SECONDARY)
            screen.blit(bs, (styles.BASE_WIDTH - bs.get_width() - 8, 8))

        # ── Category Navigator ──────────────────────────────────
        cat_name  = self.categories[self.current_cat_idx]
        n_cats    = len(self.categories)
        is_phys   = (cat_name == "FISICO")
        cat_color = styles.COLOR_PRIMARY if is_phys else styles.COLOR_ENERGY_BAR

        self.btn_cat_prev.draw(screen)
        # Category pill
        cat_rect = pygame.Rect(34, 68, styles.BASE_WIDTH-64, 28)
        styles.draw_panel(screen, cat_rect, border_color=cat_color)
        cat_surf = styles.font_caption(bold=True).render(
            f"{cat_name}   ({self.current_cat_idx+1}/{n_cats})", True, cat_color)
        screen.blit(cat_surf, (cat_rect.centerx - cat_surf.get_width()//2,
                                cat_rect.centery - cat_surf.get_height()//2))
        self.btn_cat_next.draw(screen)

        # ── Move List (left column) ──────────────────────────────
        list_rect = pygame.Rect(8, 102, 220, 120)
        styles.draw_panel(screen, list_rect, border_color=styles.COLOR_BORDER)

        move_list = self._get_move_list()
        if move_list:
            self.selected_move_idx = max(0, min(len(move_list)-1, self.selected_move_idx))

        hint_font = styles.font_hint()
        max_vis = 6
        n_moves = len(move_list) if move_list else 0
        start_idx = max(0, min(self.selected_move_idx - 2, n_moves - max_vis)) if n_moves > max_vis else 0

        if move_list:
            for i in range(max_vis):
                idx = start_idx + i
                if idx >= n_moves: break
                move = move_list[idx]
                my     = 106 + i*18
                is_sel = (idx == self.selected_move_idx)
    
                req_lv  = self.manager.data_manager.get_move_tier(move["cost"])
                lv_val  = {1:1, 2:5, 3:10, 4:15}.get(req_lv, 1)
                locked  = (fighter.level < lv_val) if fighter else True
    
                if is_sel:
                    hi = pygame.Surface((218, 16), pygame.SRCALPHA)
                    hi.fill((*LAB_COLOR, 30))
                    screen.blit(hi, (9, my-1))
                    pygame.draw.polygon(screen, LAB_COLOR,
                                        [(10, my+4), (10, my+10), (15, my+7)])
    
                if locked:
                    name_color = styles.COLOR_DISABLED
                    lock_tag   = f"🔒 LV.{lv_val}"
                else:
                    name_color = LAB_COLOR if is_sel else styles.COLOR_WHITE
                    lock_tag   = f"LV.{lv_val}"
    
                mv_surf  = hint_font.render(move["name"].upper(), True, name_color)
                cost_txt = hint_font.render(f"{move['cost']}B", True,
                                             styles.COLOR_SECONDARY if not locked else styles.COLOR_DISABLED)
                screen.blit(mv_surf,  (22, my))
                screen.blit(cost_txt, (list_rect.right - cost_txt.get_width() - 4, my))
    
                if locked:
                    lock_s = hint_font.render(lock_tag, True, styles.COLOR_ERROR)
                    screen.blit(lock_s, (22, my+9))

        if not move_list:
            nd = styles.font_body().render("SIN MOVIMIENTOS DISPONIBLES", True, styles.COLOR_MUTED)
            screen.blit(nd, (list_rect.centerx - nd.get_width()//2, 148))

        # ── Detail Panel (right column) ────────────────────────
        detail_rect = pygame.Rect(234, 102, 236, 120)
        styles.draw_panel(screen, detail_rect, border_color=LAB_COLOR)

        if move_list:
            move = move_list[self.selected_move_idx]
            sec  = styles.font_caption(bold=True)
            hf   = styles.font_hint()

            screen.blit(sec.render(move['name'].upper(), True, styles.COLOR_WHITE),
                        (240, 106))
            pygame.draw.line(screen, LAB_COLOR, (240, 118), (464, 118), 1)

            # Type tag
            m_type = move.get("type", "Fisico")
            type_col = styles.COLOR_PRIMARY if m_type == "Fisico" else styles.COLOR_ENERGY_BAR
            styles.draw_tag(screen, f"[{m_type.upper()[:2]}]", (240, 122), type_col)

            # Stats
            stats_lines = [
                (f"DAÑO BASE:   {move.get('base_damage', '?')}", styles.COLOR_WHITE),
                (f"COSTO:       {move.get('cost', '?')} B",      styles.COLOR_SECONDARY),
                (f"MULT:        x{move.get('multiplier', 1.0):.1f}", styles.COLOR_INFO),
            ]
            for j, (txt, col) in enumerate(stats_lines):
                ss = hf.render(txt, True, col)
                screen.blit(ss, (240, 136 + j*14))

            # Effect
            if "effect" in move:
                eff = move["effect"]
                screen.blit(hf.render("EFECTO:", True, styles.COLOR_SUCCESS), (240, 178))
                eff_str = f"{eff.get('name','?')} • {eff.get('type','?')} " \
                          f"V:{eff.get('value','?')} D:{eff.get('duration','?')}"
                screen.blit(hf.render(eff_str, True, (180, 255, 180)), (240, 189))

            # Lock status
            req_lv = self.manager.data_manager.get_move_tier(move["cost"])
            lv_val = {1:1, 2:5, 3:10, 4:15}.get(req_lv, 1)
            if fighter and fighter.level < lv_val:
                lock_info = hf.render(f"🔒 REQUIERE NIVEL {lv_val}  (TIENES: {fighter.level})",
                                       True, styles.COLOR_ERROR)
                screen.blit(lock_info, (240, 204))
            elif fighter:
                ok = hf.render("✓ DISPONIBLE PARA COMPRAR", True, styles.COLOR_SUCCESS)
                screen.blit(ok, (240, 204))

        # Key hints
        hn_font = styles.font_hint()
        key_r = hn_font.render("← → CATEGORÍA   ↑↓ MOVIMIENTO   ENTER COMPRAR",
                                True, styles.COLOR_DISABLED)
        screen.blit(key_r, (styles.BASE_WIDTH//2 - key_r.get_width()//2,
                             styles.BASE_HEIGHT - styles.NAV_HEIGHT - 20))

        self.btn_buy.draw(screen)
        self.feedback.draw(screen, y=styles.BASE_HEIGHT - styles.NAV_HEIGHT - 38)
        self.btn_back.draw(screen)
        self.nav_bar.draw(screen)

        if self.dialog:
            self.dialog.draw(screen)
