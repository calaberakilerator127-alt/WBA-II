import pygame
import math
from src.graphics import styles
from src.graphics.ui_system import PixelButton, TextInput, FeedbackMessage
from src.utils.localization import lang

class RegistrationState:
    """
    Account registration — 2-step wizard.
    Step 1: Username & password with validation hints.
    Step 2: Profile icon selector with visual highlighting.
    """
    def __init__(self, manager):
        self.manager   = manager
        self.step      = 0     # 0 = data, 1 = icon
        self._time     = 0.0
        self.feedback  = FeedbackMessage(duration=2.5)

        cx = styles.BASE_WIDTH // 2

        self.inputs = [
            TextInput(manager, (cx - 90, 100), size=(180, 26), placeholder="Usuario"),
            TextInput(manager, (cx - 90, 138), size=(180, 26),
                      placeholder="Contraseña", is_password=True),
        ]
        self.btn_next = PixelButton(manager, "SIGUIENTE →", (cx - 70, 178),
                                    size=(140, 28), callback=self.next_step,
                                    variant="primary")
        self.btn_back = PixelButton(manager, "← VOLVER", (20, 20), size=(80, 22),
                                    callback=lambda: manager.change_state("login"),
                                    variant="ghost")

        # Icon list
        self.icons = [
            r"assets/images/profile/masculino/Amsterdam.png",
            r"assets/images/profile/masculino/Brandom.png",
            r"assets/images/profile/femenino/Natasha.png",
            r"assets/images/profile/femenino/Wendy.png",
        ]
        self.selected_icon_idx = 0
        self.icon_surfaces     = {}

    def next_step(self):
        if self.step == 0:
            user = self.inputs[0].text.strip()
            pswd = self.inputs[1].text.strip()
            if not user:
                self.feedback.show("INGRESA UN NOMBRE DE USUARIO", kind="error")
                return
            if not pswd:
                self.feedback.show("INGRESA UNA CONTRASEÑA", kind="error")
                return
            if len(pswd) < 3:
                self.feedback.show("LA CONTRASEÑA ES DEMASIADO CORTA", kind="warning")
                return
            self.step = 1
            self.feedback.show("ELIGE TU ÍCONO DE PERFIL", kind="info")
        else:
            acc = self.manager.data_manager.register(
                self.inputs[0].text, self.inputs[1].text)
            if acc:
                acc.avatar_path = self.icons[self.selected_icon_idx]
                self.manager.data_manager.save_account(acc)
                self.feedback.show("¡CUENTA CREADA!", kind="success")
            self.manager.change_state("login")

    def update(self, dt, events):
        self._time += dt
        for event in events:
            if self.step == 0:
                for inp in self.inputs:
                    inp.handle_event(event)
            elif self.step == 1:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RIGHT:
                        self.selected_icon_idx = (self.selected_icon_idx+1) % len(self.icons)
                    elif event.key == pygame.K_LEFT:
                        self.selected_icon_idx = (self.selected_icon_idx-1) % len(self.icons)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.manager.change_state("login")
            self.btn_next.handle_event(event)
            self.btn_back.handle_event(event)

        for inp in self.inputs:
            inp.update(dt)
        self.btn_next.update(dt)
        self.btn_back.update(dt)
        self.feedback.update(dt)

    # ── Drawing ─────────────────────────────────────────────────────

    def draw(self, screen):
        screen.fill(styles.COLOR_BG)
        styles.draw_scanlines(screen, alpha=18)
        styles.draw_vignette(screen, strength=70)

        # Header
        styles.draw_header(screen, "REGISTRO DE CUENTA",
                           subtitle_text=f"PASO {self.step+1} DE 2",
                           border_color=styles.COLOR_ACCENT)

        # Step indicator dots
        for i in range(2):
            color = styles.COLOR_ACCENT if i == self.step else styles.COLOR_BORDER
            pygame.draw.circle(screen, color,
                                (styles.BASE_WIDTH//2 - 8 + i*16, 60), 4)
            pygame.draw.circle(screen, styles.COLOR_WHITE,
                                (styles.BASE_WIDTH//2 - 8 + i*16, 60), 4, 1)

        if self.step == 0:
            self._draw_step_data(screen)
        else:
            self._draw_step_icon(screen)

        self.feedback.draw(screen, y=styles.BASE_HEIGHT - 18)
        self.btn_back.draw(screen)

    def _draw_step_data(self, screen):
        cx  = styles.BASE_WIDTH // 2
        lbl = styles.font_hint()

        # Panel
        panel_rect = pygame.Rect(cx - 100, 80, 200, 128)
        styles.draw_panel(screen, panel_rect, border_color=styles.COLOR_BORDER)

        # Labels
        screen.blit(lbl.render("NOMBRE DE USUARIO", True, styles.COLOR_MUTED),
                    (cx - 90, 88))
        screen.blit(lbl.render("CONTRASEÑA", True, styles.COLOR_MUTED),
                    (cx - 90, 126))

        for inp in self.inputs:
            inp.draw(screen)
        self.btn_next.draw(screen)

        # Hint
        hint = styles.font_hint().render(
            "↑↓ para navegar  •  ENTER para continuar", True, styles.COLOR_DISABLED)
        screen.blit(hint, (cx - hint.get_width()//2, styles.BASE_HEIGHT - 30))

    def _draw_step_icon(self, screen):
        cx  = styles.BASE_WIDTH // 2
        instr_font = styles.font_body()
        instr = instr_font.render("ELIGE TU ÍCONO DE PERFIL", True, styles.COLOR_WHITE)
        screen.blit(instr, (cx - instr.get_width()//2, 72))

        icon_size = 60
        n         = len(self.icons)
        total_w   = n * (icon_size + 10) - 10
        start_x   = cx - total_w // 2

        for i, path in enumerate(self.icons):
            if path not in self.icon_surfaces:
                try:
                    img = pygame.image.load(path).convert_alpha()
                    self.icon_surfaces[path] = pygame.transform.scale(img, (icon_size, icon_size))
                except Exception:
                    s = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
                    pygame.draw.rect(s, (60, 60, 80), s.get_rect(), border_radius=4)
                    self.icon_surfaces[path] = s

            img  = self.icon_surfaces[path]
            ix   = start_x + i * (icon_size + 10)
            iy   = 100

            # Glow on selected
            if i == self.selected_icon_idx:
                t    = self._time
                glow = pygame.Surface((icon_size+12, icon_size+12), pygame.SRCALPHA)
                alpha = 60 + int(40 * math.sin(t * 3))
                pygame.draw.rect(glow, (*styles.COLOR_SECONDARY, alpha),
                                  glow.get_rect(), border_radius=6)
                screen.blit(glow, (ix-6, iy-6))
                # Gold border
                styles.draw_glow_border(screen,
                                         pygame.Rect(ix-2, iy-2, icon_size+4, icon_size+4),
                                         styles.COLOR_SECONDARY, intensity=0.9)

            screen.blit(img, (ix, iy))

            # Role label
            role = "MASCULINO" if i < 2 else "FEMENINO"
            lbl  = styles.font_hint().render(role, True, styles.COLOR_MUTED)
            screen.blit(lbl, (ix + icon_size//2 - lbl.get_width()//2, iy + icon_size + 3))

        # Selection name
        sel_name = ["Amsterdam", "Brandom", "Natasha", "Wendy"][self.selected_icon_idx]
        nf       = styles.font_body(bold=True)
        ns       = nf.render(sel_name.upper(), True, styles.COLOR_SECONDARY)
        screen.blit(ns, (cx - ns.get_width()//2, 180))

        # Navigation hint
        hint = styles.font_hint().render("◄ ► FLECHAS PARA CAMBIAR  |  ENTER PARA CONFIRMAR",
                                          True, styles.COLOR_MUTED)
        screen.blit(hint, (cx - hint.get_width()//2, 200))

        # Update button label for final step
        self.btn_next.set_text("CREAR CUENTA ✓")
        self.btn_next.rect.x = cx - 80
        self.btn_next.rect.y = 220
        self.btn_next.rect.width = 160
        self.btn_next.draw(screen)
