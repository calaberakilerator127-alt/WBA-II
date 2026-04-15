import pygame
from src.graphics import styles
from src.graphics.ui_system import Slider, PixelButton, FeedbackMessage
from src.utils.localization import lang

class AdjustmentsState:
    """
    System Settings — Sound, Language, Fullscreen, Control Remapping.
    Two tabs: GENERAL and CONTROLES.
    """
    def __init__(self, manager):
        self.manager  = manager
        self._time    = 0.0
        self.feedback = FeedbackMessage(duration=2.0)

        self.acc = manager.data_manager.active_p1
        vols     = self.acc.settings if self.acc else {
            "master_vol": 0.5, "music_vol": 0.5, "sfx_vol": 0.5}

        self.tab = "GENERAL"   # or "CONTROLES"

        # ── Sliders ─────────────────────────────────────────────
        cx = styles.BASE_WIDTH // 2
        self.sliders = [
            Slider(manager, "VOLUMEN MASTER", (cx-100, 80),
                   value=vols.get("master_vol", 0.5),
                   callback=lambda v: self.set_vol("master", v)),
            Slider(manager, "MÚSICA",         (cx-100, 120),
                   value=vols.get("music_vol", 0.5),
                   callback=lambda v: self.set_vol("music", v)),
            Slider(manager, "EFECTOS (SFX)",  (cx-100, 160),
                   value=vols.get("sfx_vol", 0.5),
                   callback=lambda v: self.set_vol("sfx", v)),
        ]

        # ── Buttons ─────────────────────────────────────────────
        self.btn_lang  = PixelButton(manager, f"IDIOMA: {lang.lang.upper()}",
                                     (cx-112, 200), size=(105, 24),
                                     callback=self.toggle_lang, variant="ghost")
        self.btn_fs    = PixelButton(manager, "PANTALLA COMPLETA",
                                     (cx+8, 200), size=(105, 24),
                                     callback=self.toggle_fs, variant="ghost")
        self.btn_ctrl  = PixelButton(manager, "AJUSTAR CONTROLES →",
                                     (cx-80, 230), size=(160, 26),
                                     callback=lambda: self.switch_tab("CONTROLES"),
                                     variant="info")
        self.btn_back  = PixelButton(manager, "← VOLVER", (8, 8), size=(70, 22),
                                     callback=self.go_back, variant="ghost")
        self.btn_reset = PixelButton(manager, "RESET DEFAULT",
                                     (styles.BASE_WIDTH-110, 230), size=(100, 22),
                                     callback=self.reset_controls, variant="danger",
                                     tooltip_text="Restaurar controles predeterminados")

        # ── Control Remapping ────────────────────────────────────
        self.binding_action = None
        self.control_items  = [
            ("ARRIBA",         "UP"),
            ("ABAJO",          "DOWN"),
            ("IZQUIERDA",      "LEFT"),
            ("DERECHA",        "RIGHT"),
            ("CONFIRMAR",      "CONFIRM"),
            ("CANCELAR/VOLVER","BACK"),
            ("ENTRENAR/ACCIÓN","TRAIN"),
            ("STATS/HUD",      "STATS"),
        ]
        self._ctrl_hover = -1
        self.ctrl_player = 1
        self.btn_toggle_p = PixelButton(manager, "EDITANDO: JUGADOR 1",
                                     (cx-80, 45), size=(160, 22),
                                     callback=self.toggle_ctrl_player,
                                     variant="info", font_size=8)

    # ── Callbacks ─────────────────────────────────────────────────

    def toggle_ctrl_player(self):
        self.ctrl_player = 2 if self.ctrl_player == 1 else 1
        self.btn_toggle_p.set_text(f"EDITANDO: JUGADOR {self.ctrl_player}")
        self.binding_action = None

    def reset_controls(self):
        acc = self.manager.data_manager.active_p1 if self.ctrl_player == 1 else self.manager.data_manager.active_p2
        if not acc:
            self.feedback.show(f"INICIA SESIÓN P{self.ctrl_player} PRIMERO", kind="error")
            return
        
        if self.ctrl_player == 1:
            acc.key_bindings = {
                "UP": 1073741906, "DOWN": 1073741905,
                "LEFT": 1073741904, "RIGHT": 1073741903,
                "CONFIRM": 13, "BACK": 27, "TRAIN": 32, "STATS": 9
            }
        else:
            acc.key_bindings = {
                "UP": 119, "DOWN": 115, "LEFT": 97, "RIGHT": 100,
                "CONFIRM": 1073742049, "BACK": 122, "TRAIN": 120, "STATS": 99
            }

        if self.ctrl_player == 1:
            self.manager.data_manager.save_account(acc)
        else:
            self.manager.data_manager.save_active_account(is_p1=False)
        self.feedback.show("CONTROLES RESTAURADOS", kind="success")

    def switch_tab(self, tab):
        self.tab            = tab
        self.binding_action = None

    def set_vol(self, kind, val):
        if self.acc:
            if kind == "master": self.acc.settings["master_vol"] = val
            elif kind == "music": self.acc.settings["music_vol"]  = val
            elif kind == "sfx":   self.acc.settings["sfx_vol"]   = val
            master = self.acc.settings.get("master_vol", 1.0)
            if kind in ("master", "music"):
                pygame.mixer.music.set_volume(
                    self.acc.settings.get("music_vol", 0.5) * master)
        else:
            if kind == "music":
                pygame.mixer.music.set_volume(val)

    def toggle_lang(self):
        new_lang = "en" if lang.lang == "es" else "es"
        lang.set_language(new_lang)
        self.btn_lang.set_text(f"IDIOMA: {new_lang.upper()}")

    def toggle_fs(self):
        pygame.display.toggle_fullscreen()

    def go_back(self):
        if self.tab == "CONTROLES":
            self.switch_tab("GENERAL")
        else:
            if self.manager.state_stack:
                self.manager.pop_state()
            else:
                self.manager.change_state("menu" if self.acc else "login")

    # ── Update ────────────────────────────────────────────────────

    def update(self, dt, events):
        self._time += dt
        for event in events:
            if event.type == pygame.KEYDOWN:
                acc = self.manager.data_manager.active_p1 if self.ctrl_player == 1 else self.manager.data_manager.active_p2
                if self.binding_action and acc:
                    acc.key_bindings[self.binding_action] = event.key
                    self.manager.data_manager.save_active_account(is_p1=(self.ctrl_player == 1))
                    self.binding_action = None
                    self.manager.data_manager.play_sfx("stat")
                    self.feedback.show("TECLA ASIGNADA", kind="success")
                    return
                if event.key == pygame.K_ESCAPE:
                    self.go_back()
                    return

            if self.tab == "GENERAL":
                for s in self.sliders: s.handle_event(event)
                self.btn_lang.handle_event(event)
                self.btn_fs.handle_event(event)
                self.btn_ctrl.handle_event(event)
            else:
                self.btn_reset.handle_event(event)
                self.btn_toggle_p.handle_event(event)
                # Detect hover for control rows
                if event.type == pygame.MOUSEMOTION:
                    mx, my = event.pos
                    self._ctrl_hover = -1
                    for i in range(len(self.control_items)):
                        row_y = 80 + i * 22
                        if pygame.Rect(24, row_y-1, styles.BASE_WIDTH-48, 20).collidepoint(mx, my):
                            self._ctrl_hover = i
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    acc = self.manager.data_manager.active_p1 if self.ctrl_player == 1 else self.manager.data_manager.active_p2
                    if not acc:
                        self.feedback.show(f"INICIA SESIÓN P{self.ctrl_player} PARA EDITAR", kind="error")
                    else:
                        mx, my = event.pos
                        for i, (label, action) in enumerate(self.control_items):
                            row_y  = 80 + i * 22
                            rect_r = pygame.Rect(styles.BASE_WIDTH//2+10, row_y-1, 150, 20)
                            if rect_r.collidepoint(mx, my):
                                self.binding_action = action
                                self.manager.data_manager.play_sfx("click")

            self.btn_back.handle_event(event)

        if self.tab == "GENERAL":
            for s in self.sliders: s.update(dt)
            self.btn_lang.update(dt)
            self.btn_fs.update(dt)
            self.btn_ctrl.update(dt)
        else:
            self.btn_reset.update(dt)
            self.btn_toggle_p.update(dt)
        self.btn_back.update(dt)
        self.feedback.update(dt)

    # ── Draw ─────────────────────────────────────────────────────

    def draw(self, screen):
        screen.fill(styles.COLOR_BG)
        styles.draw_scanlines(screen, alpha=14)

        title_txt = "AJUSTES DE SISTEMA" if self.tab == "GENERAL" else "PERSONALIZAR CONTROLES"
        styles.draw_header(screen, title_txt)

        if self.tab == "GENERAL":
            self._draw_general(screen)
        else:
            self._draw_controls(screen)

        self.feedback.draw(screen, y=styles.BASE_HEIGHT - 14)
        self.btn_back.draw(screen)

    def _draw_general(self, screen):
        # ── Sound sliders ────────────────────────────────────────
        sec_font = styles.font_caption(bold=True)
        screen.blit(sec_font.render("AUDIO", True, styles.COLOR_SECONDARY),
                    (styles.BASE_WIDTH//2-100, 66))
        pygame.draw.line(screen, styles.COLOR_BORDER,
                          (styles.BASE_WIDTH//2-100, 78),
                          (styles.BASE_WIDTH//2+100, 78), 1)

        for s in self.sliders:
            s.draw(screen)

        # ── Misc buttons ─────────────────────────────────────────
        screen.blit(sec_font.render("SISTEMA", True, styles.COLOR_SECONDARY),
                    (styles.BASE_WIDTH//2-100, 188))
        pygame.draw.line(screen, styles.COLOR_BORDER,
                          (styles.BASE_WIDTH//2-100, 200),
                          (styles.BASE_WIDTH//2+100, 200), 1)

        self.btn_lang.draw(screen)
        self.btn_fs.draw(screen)
        self.btn_ctrl.draw(screen)

        # ── Hint ─────────────────────────────────────────────────
        hint = styles.font_hint().render(
            "ESC = VOLVER  •  ARRASTRA LOS SLIDERS PARA AJUSTAR",
            True, styles.COLOR_DISABLED)
        screen.blit(hint, (styles.BASE_WIDTH//2 - hint.get_width()//2,
                            styles.BASE_HEIGHT - 24))

    def _draw_controls(self, screen):
        cx       = styles.BASE_WIDTH // 2
        hf       = styles.font_hint()
        sec_font = styles.font_caption(bold=True)
        defaults_p1 = {
            "UP": 1073741906, "DOWN": 1073741905, "LEFT": 1073741904, "RIGHT": 1073741903,
            "CONFIRM": 13, "BACK": 27, "TRAIN": 32, "STATS": 9
        }
        defaults_p2 = {
            "UP": 119, "DOWN": 115, "LEFT": 97, "RIGHT": 100,
            "CONFIRM": 1073742049, "BACK": 122, "TRAIN": 120, "STATS": 99
        }
        acc = self.manager.data_manager.active_p1 if self.ctrl_player == 1 else self.manager.data_manager.active_p2
        kb = acc.key_bindings if acc else (defaults_p1 if self.ctrl_player == 1 else defaults_p2)

        self.btn_toggle_p.draw(screen)

        # Column headers
        screen.blit(sec_font.render("ACCIÓN",    True, styles.COLOR_MUTED), (30, 64))
        screen.blit(sec_font.render("TECLA ASIGNADA", True, styles.COLOR_MUTED), (cx+10, 64))
        pygame.draw.line(screen, styles.COLOR_BORDER, (24, 76), (styles.BASE_WIDTH-24, 76), 1)

        for i, (label, action) in enumerate(self.control_items):
            row_y    = 80 + i * 22
            is_hover = (i == self._ctrl_hover)
            is_bind  = (action == self.binding_action)

            # Row background
            row_rect = pygame.Rect(24, row_y-1, styles.BASE_WIDTH-48, 20)
            if is_bind:
                rb = pygame.Surface((row_rect.width, row_rect.height), pygame.SRCALPHA)
                rb.fill((*styles.COLOR_PRIMARY, 40))
                screen.blit(rb, row_rect.topleft)
                pygame.draw.rect(screen, styles.COLOR_PRIMARY, row_rect, 1)
            elif is_hover:
                rh = pygame.Surface((row_rect.width, row_rect.height), pygame.SRCALPHA)
                rh.fill((255, 255, 255, 12))
                screen.blit(rh, row_rect.topleft)

            # Action label
            lbl_col  = styles.COLOR_WHITE if is_hover or is_bind else styles.COLOR_MUTED
            lbl_surf = hf.render(label, True, lbl_col)
            screen.blit(lbl_surf, (30, row_y+2))

            # Key name
            key_int  = kb.get(action, 0)
            key_name = "... PULSA UNA TECLA ..." if is_bind else pygame.key.name(key_int).upper()
            key_col  = styles.COLOR_SECONDARY if is_bind else (
                       styles.COLOR_ACCENT if is_hover else styles.COLOR_WHITE)
            key_surf = hf.render(key_name, True, key_col)
            # Click zone indicator
            key_rect = pygame.Rect(cx+10, row_y-1, styles.BASE_WIDTH-24-cx-10, 20)
            if is_hover and not is_bind:
                kr_bg = pygame.Surface((key_rect.width, key_rect.height), pygame.SRCALPHA)
                kr_bg.fill((*styles.COLOR_ACCENT, 15))
                screen.blit(kr_bg, key_rect.topleft)
            screen.blit(key_surf, (cx+10, row_y+2))

        # Instructions
        instr = hf.render(
            "HAZ CLIC EN UNA TECLA PARA REASIGNARLA  •  LUEGO PULSA LA NUEVA TECLA",
            True, styles.COLOR_DISABLED)
        screen.blit(instr, (cx - instr.get_width()//2, styles.BASE_HEIGHT - 28))

        self.btn_reset.draw(screen)
