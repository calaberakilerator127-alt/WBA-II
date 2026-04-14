import pygame
from src.graphics import styles
from src.graphics.ui_system import PixelButton, NavBar, CardWidget
from src.utils.localization import lang

class RosterState:
    """
    Fighter Roster — Grid view of the player's full collection.
    Each card shows portrait, name, level, affinity, and HP status.
    """
    def __init__(self, manager):
        self.manager    = manager
        self.acc        = manager.data_manager.active_p1
        self.roster     = self.acc.fighters if self.acc else []
        self._time      = 0.0
        self.cursor_idx = 0

        self.btn_back = PixelButton(manager, "← VOLVER", (8, 8), size=(70, 22),
                                    callback=lambda: manager.change_state("menu"),
                                    variant="ghost")
        self.nav_bar  = NavBar(manager, current_state="roster")

        # Build card widgets
        self.cols     = 4
        self.card_w   = 100
        self.card_h   = 68
        self.pad      = 8
        self.start_x  = 14
        self.start_y  = styles.CONTENT_TOP + 4
        self._cards   = []
        self._build_cards()

    def _build_cards(self):
        self._cards = []
        for i, fighter in enumerate(self.roster):
            row  = i // self.cols
            col  = i % self.cols
            x    = self.start_x + col * (self.card_w + self.pad)
            y    = self.start_y + row * (self.card_h + self.pad)
            card = CardWidget(
                self.manager, (x, y), (self.card_w, self.card_h),
                label=fighter.name,
                sublabel=f"LV.{fighter.level}",
                color_accent=styles.COLOR_ACCENT,
                on_click=lambda idx=i: self.select_fighter(idx)
            )
            card.set_hp(fighter.hp / max(1, fighter.max_hp))

            # Try to load portrait
            if fighter.portrait_path:
                try:
                    img = pygame.image.load(fighter.portrait_path).convert_alpha()
                    card.set_image(img)
                except Exception:
                    pass
            self._cards.append(card)

    def select_fighter(self, idx):
        if idx < len(self.roster):
            self.manager.selected_fighter_idx = idx
            self.manager.change_state("profile")

    def update(self, dt, events):
        self._time += dt
        n = max(1, len(self.roster))

        for event in events:
            if event.type == pygame.KEYDOWN:
                k = event.key
                if k == pygame.K_RIGHT:
                    self.cursor_idx = (self.cursor_idx + 1) % n
                elif k == pygame.K_LEFT:
                    self.cursor_idx = (self.cursor_idx - 1) % n
                elif k == pygame.K_DOWN:
                    self.cursor_idx = min(n-1, self.cursor_idx + self.cols)
                elif k == pygame.K_UP:
                    self.cursor_idx = max(0, self.cursor_idx - self.cols)
                elif k == pygame.K_RETURN:
                    self.select_fighter(self.cursor_idx)
                elif k == pygame.K_ESCAPE:
                    self.manager.change_state("menu")

            self.btn_back.handle_event(event)
            self.nav_bar.handle_event(event)
            for card in self._cards:
                card.handle_event(event)

        self.btn_back.update(dt)
        self.nav_bar.update(dt)
        for card in self._cards:
            card.update(dt)

    def draw(self, screen):
        screen.fill(styles.COLOR_BG)
        styles.draw_scanlines(screen, alpha=14)

        # Header
        styles.draw_header(screen, "MI COLECCIÓN", subtitle_text="SELECCIONA UN LUCHADOR")

        # Account stats row under header
        if self.acc:
            sf = styles.font_hint()
            wr = (self.acc.wins/(self.acc.wins+self.acc.losses)*100) \
                 if (self.acc.wins + self.acc.losses) > 0 else 0
            stat_str = f"VICTORIAS: {self.acc.wins}  •  DERROTAS: {self.acc.losses}  •  BRAWELS: {self.acc.brawels}"
            ss = sf.render(stat_str, True, styles.COLOR_MUTED)
            screen.blit(ss, (styles.BASE_WIDTH//2 - ss.get_width()//2, styles.CONTENT_TOP - 8))

        # Fighter cards
        for i, card in enumerate(self._cards):
            # Override is_hovered for keyboard cursor
            card.is_hovered = (i == self.cursor_idx)
            card.draw(screen)

        # Keyboard hint
        if self.roster:
            hint = styles.font_hint().render(
                "FLECHAS PARA NAVEGAR  •  ENTER PARA VER PERFIL", True, styles.COLOR_DISABLED)
            screen.blit(hint, (styles.BASE_WIDTH//2 - hint.get_width()//2,
                                styles.BASE_HEIGHT - styles.NAV_HEIGHT - 14))

        if not self.roster:
            empty = styles.font_body().render("NO HAY LUCHADORES EN TU COLECCIÓN",
                                               True, styles.COLOR_MUTED)
            screen.blit(empty, (styles.BASE_WIDTH//2 - empty.get_width()//2, 120))

        self.btn_back.draw(screen)
        self.nav_bar.draw(screen)
