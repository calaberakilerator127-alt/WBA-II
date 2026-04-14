import pygame
import random
from src.graphics import styles
from src.graphics.ui_system import PixelButton
from src.utils.localization import lang

class TeamSelectState:
    """
    Team Assembly — Pick 1-3 fighters from your roster.
    Visual slots, clear hints, and a confirmation prompt.
    """
    def __init__(self, manager):
        self.manager = manager
        self._time   = 0.0

        self.target_player = getattr(manager, "target_player", 1)
        self.acc           = manager.data_manager.active_p1 if self.target_player == 1 else manager.data_manager.active_p2
        self.roster        = self.acc.fighters if self.acc else []
        self.config        = getattr(manager, "combat_config", {"team_size": 1})
        self.max_slots     = self.config["team_size"]
        
        self.selected_fighters = []
        self.cursor_idx        = 0
        self.portrait_cache    = {}

        self.btn_back   = PixelButton(manager, "← VOLVER", (8, 8), size=(70, 22),
                                      callback=self.go_back, variant="ghost")
        self.btn_finish = PixelButton(manager, "LISTO",
                                      (styles.BASE_WIDTH - 130, styles.BASE_HEIGHT - 38),
                                      size=(120, 30), callback=self.finish_selection,
                                      variant="success")

    def get_portrait(self, fighter):
        if fighter.name in self.portrait_cache:
            return self.portrait_cache[fighter.name]
        try:
            img = pygame.image.load(fighter.portrait_path).convert_alpha()
            surf = pygame.transform.scale(img, (60, 60))
            self.portrait_cache[fighter.name] = surf
            return surf
        except Exception:
            dummy = pygame.Surface((60, 60))
            dummy.fill((50, 50, 60))
            return dummy

    def go_back(self):
        self.manager.change_state("mode_config")

    def finish_selection(self):
        final_team = list(self.selected_fighters)
        while len(final_team) < self.max_slots:
            random_fighter = self.manager.data_manager.create_default_fighter(name=f"Aliado {len(final_team)+1}")
            if final_team:
                random_fighter.level = final_team[0].level
            elif self.target_player == 2 and self.manager.selected_team:
                # Guest P2 gets same level as P1 leader
                random_fighter.level = self.manager.selected_team[0].level
            final_team.append(random_fighter)
            
        if self.target_player == 1:
            self.manager.selected_team = final_team
            if self.config.get("is_p2_local"):
                self.manager.target_player = 2
                self.manager.change_state("p2_access")
            else:
                self.manager.change_state("stage_select")
        else:
            self.manager.selected_team_p2 = final_team
            self.manager.change_state("stage_select")

    def toggle_selection(self, idx):
        if not self.roster or idx >= len(self.roster): return
        f = self.roster[idx]
        exists = next((i for i, sel in enumerate(self.selected_fighters) if sel.id == f.id), None)
        if exists is not None:
            self.selected_fighters.pop(exists)
            self.manager.data_manager.play_sfx("hover")
        else:
            if len(self.selected_fighters) < self.max_slots:
                self.selected_fighters.append(f)
                self.manager.data_manager.play_sfx("stat")

    def update(self, dt, events):
        self._time += dt
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:   self.cursor_idx = (self.cursor_idx + 1) % len(self.roster)
                elif event.key == pygame.K_LEFT:  self.cursor_idx = (self.cursor_idx - 1) % len(self.roster)
                elif event.key == pygame.K_DOWN:  self.cursor_idx = min(len(self.roster)-1, self.cursor_idx + 4)
                elif event.key == pygame.K_UP:    self.cursor_idx = max(0, self.cursor_idx - 4)
                elif event.key == pygame.K_RETURN: self.toggle_selection(self.cursor_idx)
                elif event.key == pygame.K_ESCAPE: self.go_back()
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                cols = 4
                for i in range(len(self.roster)):
                    col = i % cols
                    row = i // cols
                    x = 40 + col * 80
                    y = styles.CONTENT_TOP + 20 + row * 85
                    if pygame.Rect(x-5, y-5, 70, 70).collidepoint(mx, my):
                        self.toggle_selection(i)
            
            self.btn_back.handle_event(event)
            self.btn_finish.handle_event(event)
            
        self.btn_back.update(dt)
        self.btn_finish.update(dt)

    def draw(self, screen):
        screen.fill(styles.COLOR_BG)
        styles.draw_scanlines(screen, alpha=14)
        
        styles.draw_header(screen, "FORMA TU EQUIPO", subtitle_text=f"ELIGE {self.max_slots} LUCHADORES", border_color=styles.COLOR_PRIMARY)

        # Draw Roster Grid
        if not self.roster:
            empty_msg = styles.font_body().render("NO TIENES LUCHADORES.", True, styles.COLOR_ERROR)
            screen.blit(empty_msg, (styles.BASE_WIDTH//2 - empty_msg.get_width()//2, 100))
        else:
            cols = 4
            for i, f in enumerate(self.roster):
                col = i % cols
                row = i // cols
                x = 40 + col * 80
                y = styles.CONTENT_TOP + 20 + row * 85
                
                is_selected = any(sel.id == f.id for sel in self.selected_fighters)
                
                # Card Background
                bg_col = (45, 45, 60) if is_selected else styles.COLOR_PANEL_BG
                bg_rect = pygame.Rect(x-5, y-5, 70, 70)
                pygame.draw.rect(screen, bg_col, bg_rect, border_radius=4)
                
                # Borders
                if is_selected:
                    pygame.draw.rect(screen, styles.COLOR_SUCCESS, bg_rect, 2, border_radius=4)
                    check = styles.font_hint().render("✓", True, styles.COLOR_SUCCESS)
                    screen.blit(check, (bg_rect.right - 12, bg_rect.top + 2))
                elif i == self.cursor_idx:
                    pygame.draw.rect(screen, styles.COLOR_PRIMARY, bg_rect, 2, border_radius=4)
                else:
                    pygame.draw.rect(screen, styles.COLOR_BORDER, bg_rect, 1, border_radius=4)
                
                port = self.get_portrait(f)
                screen.blit(port, (x, y))
                name_surf = styles.font_hint().render(f.name[:10].upper(), True, styles.COLOR_WHITE)
                screen.blit(name_surf, (x + 30 - name_surf.get_width()//2, y + 66))

        # Bottom Team Display Line
        pygame.draw.line(screen, styles.COLOR_BORDER, (10, 185), (styles.BASE_WIDTH - 10, 185), 1)
        screen.blit(styles.font_caption(bold=True).render("EQUIPO SELECCIONADO:", True, styles.COLOR_MUTED), (15, 195))
        
        # Display Slots
        for i in range(self.max_slots):
            x = 15 + i * 110
            y = 210
            slot_rect = pygame.Rect(x, y, 100, 45)
            styles.draw_panel(screen, slot_rect, border_color=styles.COLOR_BORDER)
            
            if i < len(self.selected_fighters):
                f = self.selected_fighters[i]
                n = styles.font_caption(bold=True).render(f.name.upper(), True, styles.COLOR_WHITE)
                screen.blit(n, (x+5, y+5))
                l = styles.font_hint().render(f"LV.{f.level}", True, styles.COLOR_ACCENT)
                screen.blit(l, (x+5, y+24))
            else:
                p = styles.font_hint().render("[VACÍO]", True, styles.COLOR_DISABLED)
                screen.blit(p, (x + 50 - p.get_width()//2, y + 17))
        
        self.btn_back.draw(screen)
        
        # Only enable 'Listo' if full OR we warn about randoms
        if len(self.selected_fighters) < self.max_slots:
            txt = styles.font_hint().render(f"FALTAN {self.max_slots - len(self.selected_fighters)}. (SE LLENARÁN AL AZAR)", True, styles.COLOR_WARNING)
            screen.blit(txt, (styles.BASE_WIDTH - 130 - txt.get_width() - 10, 225))
            self.btn_finish.variant = "ghost"
        else:
            self.btn_finish.variant = "primary"

        self.btn_finish.draw(screen)
