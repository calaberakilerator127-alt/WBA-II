import pygame
from src.graphics import styles
from src.graphics.ui_system import PixelButton

class P2AccessState:
    """
    P2 Access Screen — Choose between logging in a second account or playing as Guest.
    """
    def __init__(self, manager):
        self.manager = manager
        self._time = 0.0
        
        cx = styles.BASE_WIDTH // 2
        
        self.btn_login = PixelButton(manager, "INICIAR SESIÓN", (cx - 75, 100), size=(150, 30),
                                     callback=self.go_login, variant="primary",
                                     tooltip_text="Usar una cuenta guardada para el Jugador 2")
        
        self.btn_guest = PixelButton(manager, "JUGAR COMO INVITADO", (cx - 75, 140), size=(150, 30),
                                     callback=self.go_guest, variant="secondary",
                                     tooltip_text="Jugar rápido con luchadores aleatorios equilibrados")
                                     
        self.btn_back = PixelButton(manager, "← VOLVER", (8, 8), size=(70, 22),
                                    callback=self.go_back, variant="ghost")

    def go_login(self):
        # We need to tell LoginState that it's for P2
        self.manager.target_player = 2
        self.manager.change_state("login")

    def go_guest(self):
        self.manager.data_manager.active_p2 = None # Ensure no account is linked
        self.manager.target_player = 2
        self.manager.change_state("team_select")

    def go_back(self):
        self.manager.target_player = 1
        self.manager.change_state("team_select")

    def update(self, dt, events):
        self._time += dt
        for event in events:
            self.btn_login.handle_event(event)
            self.btn_guest.handle_event(event)
            self.btn_back.handle_event(event)
            
        self.btn_login.update(dt)
        self.btn_guest.update(dt)
        self.btn_back.update(dt)

    def draw(self, screen):
        screen.fill(styles.COLOR_BG)
        styles.draw_scanlines(screen, alpha=14)
        
        styles.draw_header(screen, "ACCESO JUGADOR 2", 
                           subtitle_text="¿CÓMO DESEA IDENTIFICARSE EL SEGUNDO LUCHADOR?",
                           border_color=styles.COLOR_ACCENT)
                           
        self.btn_login.draw(screen)
        self.btn_guest.draw(screen)
        self.btn_back.draw(screen)
        
        # Decoration
        hint = styles.font_hint().render("ESC PARA VOLVER A SELECCIÓN P1", True, styles.COLOR_DISABLED)
        screen.blit(hint, (styles.BASE_WIDTH//2 - hint.get_width()//2, styles.BASE_HEIGHT - 30))
