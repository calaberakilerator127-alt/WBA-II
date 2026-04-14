import pygame
import math
from src.graphics import styles
from src.graphics.ui_system import PixelButton, FeedbackMessage
from src.utils.localization import lang

class CharacterSelectState:
    """
    Champion Market — Recruit new fighters for your roster.
    Portrait carousel with owned status, cost, and recruitment action.
    """
    def __init__(self, manager):
        self.manager      = manager
        self._time        = 0.0
        self.feedback     = FeedbackMessage(duration=2.5)
        self.acc          = manager.data_manager.active_p1
        self.recruit_cost = 500
        self.char_list    = [
            "Alexander", "Angelica", "Angie", "Ashley", "Cristina", "Cristofer",
            "Daniel", "Douglas", "Hans", "Kristen", "Leonardo", "Martin",
            "Miguel", "Oliver", "Pablo", "Tannia"
        ]
        self.selected_idx   = 0
        self.portrait_cache = {}

        self.btn_back  = PixelButton(manager, "← HUB", (8, 8), size=(60, 22),
                                     callback=lambda: manager.change_state("menu"),
                                     variant="ghost")
        self.btn_prev  = PixelButton(manager, "◄", (20, 125), size=(26, 26),
                                     callback=lambda: self.shift(-1), variant="ghost")
        self.btn_next  = PixelButton(manager, "►", (styles.BASE_WIDTH-46, 125),
                                     size=(26, 26), callback=lambda: self.shift(1),
                                     variant="ghost")
        self.btn_recruit = PixelButton(manager, "RECLUTAR (500B)",
                                       (styles.BASE_WIDTH//2 - 80, 230), size=(160, 30),
                                       callback=self.try_recruit, variant="primary")

        # Preload portraits
        for name in self.char_list:
            path = f"assets/images/characters/{name}.png"
            try:
                img = pygame.image.load(path).convert_alpha()
                self.portrait_cache[name] = pygame.transform.scale(img, (150, 150))
            except Exception:
                s = pygame.Surface((150, 150), pygame.SRCALPHA)
                pygame.draw.circle(s, styles.COLOR_PRIMARY, (75, 75), 60, 2)
                self.portrait_cache[name] = s

    def shift(self, delta):
        self.selected_idx = (self.selected_idx + delta) % len(self.char_list)
        self.manager.data_manager.play_sfx("hover")

    def try_recruit(self):
        name = self.char_list[self.selected_idx]
        if any(f.name == name for f in self.acc.fighters):
            self.feedback.show("YA ESTÁ EN TU COLECCIÓN", kind="warning")
            return
        if self.acc.brawels < self.recruit_cost:
            self.feedback.show(f"BRAWELS INSUFICIENTES (NECESITAS 500B)", kind="error")
            return
        self.acc.brawels -= self.recruit_cost
        new_f = self.manager.data_manager.create_default_fighter(name)
        new_f.sprite_path   = f"assets/images/characters/{name}.png"
        new_f.portrait_path = f"assets/images/characters/{name}.png"
        self.acc.fighters.append(new_f)
        self.manager.data_manager.save_account(self.acc)
        self.manager.data_manager.play_sfx("click")
        self.feedback.show(f"¡{name.upper()} RECLUTADO!", kind="success")

    def update(self, dt, events):
        self._time += dt
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:   self.shift(1)
                elif event.key == pygame.K_LEFT:  self.shift(-1)
                elif event.key == pygame.K_RETURN: self.try_recruit()
                elif event.key == pygame.K_ESCAPE: self.manager.change_state("menu")
            self.btn_back.handle_event(event)
            self.btn_prev.handle_event(event)
            self.btn_next.handle_event(event)
            self.btn_recruit.handle_event(event)
        self.btn_back.update(dt)
        self.btn_prev.update(dt)
        self.btn_next.update(dt)
        self.btn_recruit.update(dt)
        self.feedback.update(dt)

    def draw(self, screen):
        screen.fill(styles.COLOR_BG)
        styles.draw_scanlines(screen, alpha=14)
        styles.draw_header(screen, "MERCADO DE CAMPEONES",
                           subtitle_text="RECLUTA NUEVOS LUCHADORES PARA TU EQUIPO",
                           border_color=styles.COLOR_SECONDARY,
                           title_color=styles.COLOR_SECONDARY)

        if self.acc:
            bf = styles.font_caption(bold=True)
            bs = bf.render(f"💰 {self.acc.brawels} B", True, styles.COLOR_SECONDARY)
            screen.blit(bs, (styles.BASE_WIDTH - bs.get_width() - 8, 8))

        cx   = styles.BASE_WIDTH // 2
        name = self.char_list[self.selected_idx]
        owned= any(f.name == name for f in self.acc.fighters)

        # ── Side previews ──────────────────────────────────────
        for offset, side_x in [(-1, 45), (1, styles.BASE_WIDTH - 120)]:
            side_idx  = (self.selected_idx + offset) % len(self.char_list)
            side_name = self.char_list[side_idx]
            side_img  = self.portrait_cache.get(side_name)
            if side_img:
                small = pygame.transform.scale(side_img, (70, 70))
                small.set_alpha(60)
                screen.blit(small, (side_x, 108))

        # ── Main portrait ──────────────────────────────────────
        main_img = self.portrait_cache.get(name)
        if main_img:
            # Glow if not owned
            if not owned:
                t     = self._time
                pulse = 0.5 + 0.5 * math.sin(t * 2.5)
                glow  = pygame.Surface((162, 162), pygame.SRCALPHA)
                pygame.draw.rect(glow, (*styles.COLOR_PRIMARY, int(40 * pulse)),
                                  glow.get_rect(), border_radius=6)
                screen.blit(glow, (cx - 81, 67))

            screen.blit(main_img, (cx - 75, 70))
            frame_col = (80, 180, 80) if owned else styles.COLOR_PRIMARY
            pygame.draw.rect(screen, frame_col, (cx-75, 70, 150, 150), 2)

        # ── Name + status ──────────────────────────────────────
        fn = styles.get_font(18, is_bold=True, is_header=True)
        fs = fn.render(name.upper(), True, styles.COLOR_WHITE)
        screen.blit(fs, (cx - fs.get_width()//2, 225))

        if owned:
            tag = styles.font_caption(bold=True).render("✓ YA EN COLECCIÓN", True, styles.COLOR_SUCCESS)
            screen.blit(tag, (cx - tag.get_width()//2, 246))
        else:
            cost_str = f"COSTE: {self.recruit_cost} B"
            co = styles.font_caption().render(cost_str, True, styles.COLOR_SECONDARY)
            screen.blit(co, (cx - co.get_width()//2, 246))
            self.btn_recruit.draw(screen)

        # Counter
        ct = styles.font_hint().render(
            f"{self.selected_idx+1} / {len(self.char_list)}", True, styles.COLOR_MUTED)
        screen.blit(ct, (cx - ct.get_width()//2, styles.BASE_HEIGHT - 22))

        self.btn_prev.draw(screen)
        self.btn_next.draw(screen)
        self.btn_back.draw(screen)
        self.feedback.draw(screen, y=styles.BASE_HEIGHT - 14)
