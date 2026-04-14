import pygame
import math
from src.graphics import styles
from src.graphics.ui_system import PixelButton, TextInput, FeedbackMessage
from src.utils.localization import lang

class LoginState:
    """
    Login screen — First impression of the game.
    Dramatic dark background, glowing logo, animated slide-in form.
    """
    def __init__(self, manager):
        self.manager   = manager
        self.target_player = getattr(manager, "target_player", 1)
        self._time     = 0.0
        self._slide_y  = 60.0   # Slide-in animation offset (starts below)
        self.feedback  = FeedbackMessage(duration=3.0)

        # Inputs
        cx = styles.BASE_WIDTH // 2
        self.user_input = TextInput(manager, (cx - 90, 110), size=(180, 26), placeholder="Usuario")
        self.pass_input = TextInput(manager, (cx - 90, 148), size=(180, 26),
                                    placeholder="Contraseña", is_password=True)

        # Buttons
        self.btn_login    = PixelButton(manager, "INICIAR SESIÓN", (cx - 90, 188),
                                        size=(180, 28), callback=self.try_login,
                                        variant="primary")
        self.btn_register = PixelButton(manager, "CREAR CUENTA", (cx - 90, 222),
                                        size=(180, 26), callback=lambda: manager.change_state("register"),
                                        variant="ghost")
        self.btn_settings = PixelButton(manager, lang.get("menu_settings"), (cx - 50, 252),
                                        size=(100, 20), callback=lambda: manager.change_state("settings"),
                                        variant="ghost", font_size=8)

        self.manager.data_manager.play_music(styles.ASSET_PATHS["music"]["login"])

    def try_login(self):
        is_p1 = (self.target_player == 1)
        acc = self.manager.data_manager.login(self.user_input.text, self.pass_input.text, is_p1=is_p1)
        if acc:
            if is_p1:
                self.manager.change_state("menu")
            else:
                self.manager.change_state("team_select")
        else:
            self.feedback.show("USUARIO O CONTRASEÑA INCORRECTOS", kind="error")

    def update(self, dt, events):
        self._time   += dt
        self._slide_y = max(0.0, self._slide_y - 120.0 * dt)   # Slide in

        for event in events:
            self.user_input.handle_event(event)
            self.pass_input.handle_event(event)
            self.btn_login.handle_event(event)
            self.btn_register.handle_event(event)
            self.btn_settings.handle_event(event)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                self.try_login()

        self.user_input.update(dt)
        self.pass_input.update(dt)
        self.btn_login.update(dt)
        self.btn_register.update(dt)
        self.btn_settings.update(dt)
        self.feedback.update(dt)

    def draw(self, screen):
        # ── Background ──────────────────────────────────────────────
        screen.fill(styles.COLOR_BG)
        styles.draw_scanlines(screen, alpha=22, spacing=3)

        # Animated background glow rings
        for r in range(3):
            radius = 60 + r * 35 + int(8 * math.sin(self._time * 1.2 + r))
            alpha  = 30 - r * 8
            glow_surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*styles.COLOR_PRIMARY, alpha),
                                (radius, radius), radius)
            cx = styles.BASE_WIDTH // 2
            screen.blit(glow_surf, (cx - radius, 45 - radius))

        styles.draw_vignette(screen, strength=90)

        # ── Logo / Title ─────────────────────────────────────────────
        title_text = "WAR BRAWL ARENA II" if self.target_player == 1 else "IDENTIFICACIÓN P2"
        font_logo = styles.get_font(26, is_bold=True, is_header=True)
        logo_surf = font_logo.render(title_text, True, styles.COLOR_PRIMARY)
        lx = styles.BASE_WIDTH // 2 - logo_surf.get_width() // 2
        # Subtle y pulse on logo
        ly = 30 + int(2 * math.sin(self._time * 1.5))
        styles.draw_text_outline(screen, title_text, font_logo,
                                  styles.COLOR_PRIMARY, (lx, ly),
                                  outline_color=(120, 0, 30), outline_width=2)

        sub_font = styles.font_hint()
        sub_surf = sub_font.render("THE NEXT GENERATION", True, styles.COLOR_SECONDARY)
        screen.blit(sub_surf, (styles.BASE_WIDTH//2 - sub_surf.get_width()//2, ly + 28))

        # Separator
        styles.draw_separator(screen, ly + 40,
                               color=(*styles.COLOR_PRIMARY, 120),
                               width=200, x=styles.BASE_WIDTH//2 - 100)

        # ── Form Panel ───────────────────────────────────────────────
        slide = int(self._slide_y)
        panel_rect = pygame.Rect(styles.BASE_WIDTH//2 - 100, 94 + slide, 200, 165)
        styles.draw_panel(screen, panel_rect, border_color=styles.COLOR_BORDER)

        # Field labels
        lbl_font = styles.font_hint()
        screen.blit(lbl_font.render("USUARIO", True, styles.COLOR_MUTED),
                    (styles.BASE_WIDTH//2 - 90, 102 + slide))
        screen.blit(lbl_font.render("CONTRASEÑA", True, styles.COLOR_MUTED),
                    (styles.BASE_WIDTH//2 - 90, 140 + slide))

        # Shift widgets Y dynamically (slide-in effect)
        for widget in [self.user_input, self.pass_input,
                        self.btn_login, self.btn_register, self.btn_settings]:
            base_y = widget.target_pos.y
            widget.current_pos.y = base_y + slide
            widget.rect.y = int(widget.current_pos.y)

        self.user_input.draw(screen)
        self.pass_input.draw(screen)
        self.btn_login.draw(screen)
        self.btn_register.draw(screen)
        self.btn_settings.draw(screen)

        # ── Feedback ────────────────────────────────────────────────
        self.feedback.draw(screen, y=styles.BASE_HEIGHT - 18)
