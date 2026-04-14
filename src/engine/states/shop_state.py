import pygame
from src.graphics import styles
from src.graphics.ui_system import PixelButton, ConfirmationDialog, FeedbackMessage, NavBar
from src.utils.localization import lang

# Icons for shop categories
CAT_ICONS = {"PROTEÍNAS": "💪", "ENERGIZANTES": "⚡", "MEJORAS": "🔧"}

class ShopState:
    """
    Arena Shop — Browse and purchase proteins, energizers, and team upgrades.
    Tab navigation, item list, detail panel, Brawels always visible.
    """
    def __init__(self, manager):
        self.manager    = manager
        self._time      = 0.0
        self.feedback   = FeedbackMessage(duration=2.5)
        self.db         = manager.data_manager.load_database()
        self.cat_map    = {
            "PROTEÍNAS":   self.db.get("proteins", []),
            "ENERGIZANTES": self.db.get("energizers", []),
            "MEJORAS":     self.db.get("team_upgrades", []),
        }
        self.categories       = list(self.cat_map.keys())
        self.current_cat_idx  = 0
        self.selected_item_idx= 0
        self.acc              = manager.data_manager.active_p1
        self.dialog           = None

        self.btn_back = PixelButton(manager, "← HUB", (8, 8), size=(60, 22),
                                    callback=lambda: manager.change_state("menu"),
                                    variant="ghost")
        self.btn_cat_prev = PixelButton(manager, "◄", (8, 66), size=(22, 28),
                                        callback=lambda: self.shift_cat(-1), variant="ghost")
        self.btn_cat_next = PixelButton(manager, "►", (styles.BASE_WIDTH-30, 66),
                                        size=(22, 28), callback=lambda: self.shift_cat(1),
                                        variant="ghost")
        self.btn_buy = PixelButton(manager, "COMPRAR",
                                   (styles.BASE_WIDTH-115,
                                    styles.BASE_HEIGHT - styles.NAV_HEIGHT - 36),
                                   size=(105, 26), callback=self.confirm_purchase,
                                   variant="success")
        self.nav_bar = NavBar(manager, current_state="shop")

    def shift_cat(self, delta):
        self.current_cat_idx  = (self.current_cat_idx + delta) % len(self.categories)
        self.selected_item_idx = 0

    def confirm_purchase(self):
        items = self.cat_map[self.categories[self.current_cat_idx]]
        if not items: return
        item = items[self.selected_item_idx]
        cost = item.get("points_cost", item.get("cost", 300))
        self.dialog = ConfirmationDialog(
            self.manager,
            f"¿Comprar {item['name']} por {cost} B?",
            lambda: self.buy_item(item, cost),
            self.close_dialog
        )

    def buy_item(self, item, cost):
        if self.acc.brawels < cost:
            self.feedback.show("BRAWELS INSUFICIENTES", kind="error")
        else:
            self.acc.brawels -= cost
            name = item["name"]
            self.acc.inventory[name] = self.acc.inventory.get(name, 0) + 1
            self.manager.data_manager.save_account(self.acc)
            self.manager.data_manager.play_sfx("stat")
            self.feedback.show(f"¡{name.upper()} ADQUIRIDO!", kind="success")
        self.close_dialog()

    def close_dialog(self):
        self.dialog = None

    def update(self, dt, events):
        self._time += dt
        if self.dialog:
            for event in events:
                if self.dialog:
                    self.dialog.handle_event(event)
            if self.dialog:
                self.dialog.update(dt)
            return

        items  = self.cat_map[self.categories[self.current_cat_idx]]
        n_items= max(1, len(items))

        for event in events:
            d = self.manager.data_manager
            if event.type == pygame.KEYDOWN:
                if event.key == d.get_key("RIGHT"):  self.shift_cat(1)
                elif event.key == d.get_key("LEFT"):  self.shift_cat(-1)
                elif event.key == d.get_key("DOWN"):
                    self.selected_item_idx = (self.selected_item_idx+1) % n_items
                elif event.key == d.get_key("UP"):
                    self.selected_item_idx = (self.selected_item_idx-1) % n_items
                elif event.key == d.get_key("BACK"):
                    self.manager.change_state("menu")
                elif event.key == d.get_key("CONFIRM"):
                    self.confirm_purchase()

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
        styles.draw_header(screen, "TIENDA DE LA ARENA",
                           subtitle_text="GASTA TUS BRAWELS EN VENTAJAS PARA EL COMBATE",
                           border_color=styles.COLOR_SECONDARY,
                           title_color=styles.COLOR_SECONDARY)

        # ── Brawels balance ─────────────────────────────────────
        if self.acc:
            bc = styles.font_caption(bold=True)
            bs = bc.render(f"💰 {self.acc.brawels} BRAWELS", True, styles.COLOR_SECONDARY)
            screen.blit(bs, (styles.BASE_WIDTH - bs.get_width() - 8, 8))

        # ── Category Tabs ────────────────────────────────────────
        cat_name = self.categories[self.current_cat_idx]
        cat_icon = CAT_ICONS.get(cat_name, "■")

        self.btn_cat_prev.draw(screen)
        cat_rect = pygame.Rect(34, 64, styles.BASE_WIDTH-64, 30)
        styles.draw_panel(screen, cat_rect, border_color=styles.COLOR_SECONDARY)
        label  = f"{cat_icon}  {cat_name}  ({self.current_cat_idx+1}/{len(self.categories)})"
        cat_sf = styles.font_caption(bold=True).render(label, True, styles.COLOR_SECONDARY)
        screen.blit(cat_sf, (cat_rect.centerx - cat_sf.get_width()//2,
                              cat_rect.centery - cat_sf.get_height()//2))
        self.btn_cat_next.draw(screen)

        # ── Item list (left) ─────────────────────────────────────
        items = self.cat_map[cat_name]
        if items:
            self.selected_item_idx = max(0, min(len(items)-1, self.selected_item_idx))
        list_rect = pygame.Rect(8, 100, 215, 120)
        styles.draw_panel(screen, list_rect, border_color=styles.COLOR_BORDER)

        hf = styles.font_hint()
        max_vis = 6
        n_items = len(items) if items else 0
        start_idx = max(0, min(self.selected_item_idx - 2, n_items - max_vis)) if n_items > max_vis else 0

        if items:
            for i in range(max_vis):
                idx = start_idx + i
                if idx >= n_items: break
                item = items[idx]
                iy     = 106 + i*18
                is_sel = (idx == self.selected_item_idx)
                cost   = item.get("points_cost", item.get("cost", 300))
                can_buy= (self.acc.brawels >= cost) if self.acc else False
    
                if is_sel:
                    hi = pygame.Surface((213, 16), pygame.SRCALPHA)
                    hi.fill((*styles.COLOR_SECONDARY, 25))
                    screen.blit(hi, (9, iy-1))
                    pygame.draw.rect(screen, styles.COLOR_SECONDARY, (9, iy-1, 3, 16))
    
                name_col = styles.COLOR_SECONDARY if is_sel else styles.COLOR_WHITE
                name_s   = hf.render(item["name"], True, name_col)
                screen.blit(name_s, (16, iy))
    
                cost_col = styles.COLOR_SUCCESS if can_buy else styles.COLOR_ERROR
                cost_s   = hf.render(f"{cost}B", True, cost_col)
                screen.blit(cost_s, (list_rect.right - cost_s.get_width() - 5, iy))

        if not items:
            ns = styles.font_body().render("SIN ÍTEMS", True, styles.COLOR_MUTED)
            screen.blit(ns, (list_rect.centerx - ns.get_width()//2, 148))

        # ── Detail panel (right) ─────────────────────────────────
        detail_rect = pygame.Rect(230, 100, 240, 120)
        styles.draw_panel(screen, detail_rect, border_color=styles.COLOR_SECONDARY)

        if items:
            item = items[self.selected_item_idx]
            sc   = styles.font_caption(bold=True)
            screen.blit(sc.render(item["name"].upper(), True, styles.COLOR_WHITE),
                        (238, 106))
            pygame.draw.line(screen, styles.COLOR_SECONDARY, (238,118),(462,118),1)

            cost = item.get("points_cost", item.get("cost", 300))
            screen.blit(hf.render(f"PRECIO: {cost} B", True, styles.COLOR_SECONDARY),
                        (238, 122))

            if "bonus" in item:
                bonus_str = "  ".join([f"+{v} {k.upper()}" for k, v in item["bonus"].items()])
                screen.blit(hf.render("EFECTO:", True, styles.COLOR_MUTED), (238, 136))
                screen.blit(hf.render(bonus_str, True, styles.COLOR_SUCCESS), (238, 148))
                screen.blit(hf.render("DURACIÓN: 1 COMBATE", True, styles.COLOR_DISABLED),
                            (238, 160))
            elif "effect" in item:
                screen.blit(hf.render("MEJORA:", True, styles.COLOR_MUTED), (238, 136))
                screen.blit(hf.render(str(item["effect"]), True, (255, 200, 100)), (238, 148))

            # Afford indicator
            can_buy = (self.acc.brawels >= cost) if self.acc else False
            if can_buy:
                ok = hf.render("✓ PUEDES COMPRARLO", True, styles.COLOR_SUCCESS)
            else:
                ok = hf.render(f"✗ NECESITAS {cost - self.acc.brawels} B MÁS",
                                True, styles.COLOR_ERROR)
            screen.blit(ok, (238, 186))

        # Key hints
        hn = styles.font_hint()
        kh = hn.render("← → CATEGORÍA   ↑↓ ÍTEM   ENTER COMPRAR",
                        True, styles.COLOR_DISABLED)
        screen.blit(kh, (styles.BASE_WIDTH//2 - kh.get_width()//2,
                         styles.BASE_HEIGHT - styles.NAV_HEIGHT - 20))

        self.btn_buy.draw(screen)
        self.feedback.draw(screen, y=styles.BASE_HEIGHT - styles.NAV_HEIGHT - 38)
        self.btn_back.draw(screen)
        self.nav_bar.draw(screen)

        if self.dialog:
            self.dialog.draw(screen)
