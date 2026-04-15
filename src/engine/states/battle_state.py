import pygame
import random
import math
from src.graphics import styles
from src.graphics.ui_system import HealthBar, CommandMenu, ProgressBar, PixelButton
from src.graphics.hud import PredictionHUD
from src.graphics.stage_manager import Stage
from src.entities.fighter import Fighter
from src.engine.combat_engine import CombatManager
from src.utils.localization import lang

class BattleState:
    """
    Advanced Battle State — Two-team turn-based combat with full HUD.
    Redesigned with professional health bars, log panel, stat overlay, 
    round counter, and smooth win/lose screens.
    """
    def __init__(self, manager):
        self.manager = manager
        self.active  = True
        self._time   = 0.0
        self._result_flash = 0.0   # Flash effect on win/lose

        config = getattr(manager, "combat_config",
                         {"rounds": 1, "team_size": 1, "is_deathmatch": False})
        acc1   = manager.data_manager.active_p1

        # Fighter Preparation
        self.team1_profiles = getattr(manager, "selected_team", None) or acc1.fighters[:config["team_size"]]
        avg_lv = self.team1_profiles[0].level if self.team1_profiles else 1

        team2_sel = getattr(manager, "selected_team_p2", None)
        acc2 = getattr(manager.data_manager, "active_p2", None)
        if team2_sel:
            self.team2_profiles = team2_sel
        elif acc2 and acc2.fighters:
            self.team2_profiles = acc2.fighters[:config["team_size"]]
        else:
            self.team2_profiles = [
                manager.data_manager.create_default_fighter(name=f"Rival {i+1}")
                for i in range(config["team_size"])
            ]
            for p in self.team2_profiles:
                p.level = avg_lv

        # Engine
        self.engine = CombatManager(self.team1_profiles, self.team2_profiles)
        self.engine.initialize_combat(rounds=config["rounds"],
                                       is_deathmatch=config["is_deathmatch"])
        self.p1_wins    = 0
        self.p2_wins    = 0
        self.stage      = Stage(manager.selected_stage)
        self.prediction = PredictionHUD(manager)

        # Turn management
        self.turn_owner     = 1
        self.combat_log     = ["¡COMBATE INICIADO!"]
        self.turn_mode      = "ACTION_SELECT"
        self.stats_visible  = False

        self.menu_moves_p1 = None
        self.menu_moves_p2 = None

        # Command menus
        self.root_options = ["⚔  LUCHAR", "🛡  DEFENDER", "🎒  MOCHILA", "🚪 HUIR"]
        self.menu_root_p1 = CommandMenu(
            manager,
            (18, styles.BASE_HEIGHT - 82),
            {opt: opt for opt in self.root_options},
            lambda c: self.on_root_select(c, 1),
            player_id=1
        )
        self.menu_root_p2 = CommandMenu(
            manager,
            (styles.BASE_WIDTH - 166, styles.BASE_HEIGHT - 82),
            {opt: opt for opt in self.root_options},
            lambda c: self.on_root_select(c, 2),
            player_id=2
        )
        self.update_active_fighters()
        self.check_turn()

    # ── Fighter Management ────────────────────────────────────────

    def update_active_fighters(self):
        self.engine.participation_p1.add(self.engine.active_f1_idx)
        self.engine.participation_p2.add(self.engine.active_f2_idx)

        p1 = self.engine.team1[self.engine.active_f1_idx]
        p2 = self.engine.team2[self.engine.active_f2_idx]
        self.f1 = Fighter(p1, (95, 130), is_player_1=True)
        self.f2 = Fighter(p2, (380, 130), is_player_1=False)

        # Build move menu with type tags for P1
        moves_dict_p1 = {}
        for m in p1.moves:
            tag          = "[F]" if m.type == "Fisico" else "[M]"
            display_name = f"{tag} {m.name}"
            moves_dict_p1[display_name] = m

        self.menu_moves_p1 = CommandMenu(
            self.manager,
            (18, styles.BASE_HEIGHT - 82),
            moves_dict_p1,
            lambda c: self.select_move(c, 1),
            player_id=1
        )

        moves_dict_p2 = {}
        for m in p2.moves:
            tag          = "[F]" if m.type == "Fisico" else "[M]"
            display_name = f"{tag} {m.name}"
            moves_dict_p2[display_name] = m

        self.menu_moves_p2 = CommandMenu(
            self.manager,
            (styles.BASE_WIDTH - 166, styles.BASE_HEIGHT - 82),
            moves_dict_p2,
            lambda c: self.select_move(c, 2),
            player_id=2
        )

    # ── Turn Logic ────────────────────────────────────────────────

    def check_turn(self):
        if not self.active: return
        self.menu_root_p1.is_active = False
        self.menu_root_p2.is_active = False
        if self.menu_moves_p1: self.menu_moves_p1.is_active = False
        if self.menu_moves_p2: self.menu_moves_p2.is_active = False

        if self.f1.profile.stats.velocidad >= self.f2.profile.stats.velocidad:
            self.turn_owner      = 1
            self.menu_root_p1.is_active = True
        else:
            self.turn_owner      = 2
            self.menu_root_p2.is_active = True
        self.turn_mode = "ACTION_SELECT"

    def on_root_select(self, choice, player_id):
        if not self.active or self.turn_owner != player_id: return
        clean = choice.strip().lstrip("⚔🛡🎒🚪 ")
        active_menu_moves = self.menu_moves_p1 if player_id == 1 else self.menu_moves_p2
        active_menu_root  = self.menu_root_p1 if player_id == 1 else self.menu_root_p2

        if "LUCHAR" in clean:
            if active_menu_moves and active_menu_moves.options:
                self.turn_mode             = "MOVE_SELECT"
                active_menu_root.is_active = False
                active_menu_moves.is_active= True
            else:
                self.combat_log.append("SIN MOVIMIENTOS DISPONIBLES")
        elif "DEFENDER" in clean:
            self.execute_defense(player_id)
        elif "MOCHILA" in clean:
            self.combat_log.append("MOCHILA VACÍA (PRÓXIMAMENTE)")
        elif "HUIR" in clean:
            self.active = False
            self.manager.change_state("menu")

    def execute_defense(self, player_id):
        f = self.f1 if player_id == 1 else self.f2
        self.engine.process_defend(f.profile)
        self.combat_log.append(f"▶ {f.profile.name} se DEFIENDE")
        self.end_turn()

    def select_move(self, display_name, player_id):
        if not self.active or self.turn_owner != player_id: return
        f_atk = self.f1 if player_id == 1 else self.f2
        f_def = self.f2 if player_id == 1 else self.f1
        move_name = display_name[4:] if display_name.startswith("[") else display_name
        move = next((m for m in f_atk.profile.moves if m.name == move_name), None)
        if move:
            res = self.engine.process_move(f_atk.profile, f_def.profile, move)
            dmg = res.get("damage", 0)
            self.combat_log.append(f"▶ {f_atk.profile.name} usa {move.name}  [{dmg} DMG]")
            self.end_turn()

    def end_turn(self):
        if not self.active: return
        self.menu_root_p1.is_active = False
        self.menu_root_p2.is_active = False
        if self.menu_moves_p1: self.menu_moves_p1.is_active = False
        if self.menu_moves_p2: self.menu_moves_p2.is_active = False
        self.turn_mode = "ANIMATING"

        if self.f2.profile.hp <= 0:
            self.handle_defeat(side=2)
        elif self.f1.profile.hp <= 0:
            self.handle_defeat(side=1)
        else:
            if self.turn_owner == 1:
                self.turn_owner = 2
                self.menu_root_p2.is_active = True
            else:
                self.turn_owner = 1
                self.menu_root_p1.is_active = True
            self.turn_mode = "ACTION_SELECT"

    def handle_defeat(self, side):
        if not self.active: return
        defeated = self.f1.profile.name if side == 2 else self.f2.profile.name
        self.combat_log.append(f"✦ ¡{defeated} derrotado!")

        if side == 2:
            next_f2 = next(
                (i for i, f in enumerate(self.engine.team2) if f.hp > 0), None)
            if next_f2 is not None:
                self.engine.active_f2_idx = next_f2
                self.combat_log.append(f"▶ Siguiente rival: {self.engine.team2[next_f2].name}")
                self.update_active_fighters()
                self.end_turn()
            else:
                self.p1_wins += 1
                if self.p1_wins >= (self.engine.rounds // 2 + 1) or self.engine.rounds == 1:
                    self.finish_battle(winner=1)
                else:
                    self.start_new_round()
        else:
            next_f1 = next(
                (i for i, f in enumerate(self.engine.team1) if f.hp > 0), None)
            if next_f1 is not None:
                self.engine.active_f1_idx = next_f1
                self.combat_log.append(f"▶ ¡Adelante, {self.engine.team1[next_f1].name}!")
                self.update_active_fighters()
                self.end_turn()
            else:
                self.p2_wins += 1
                if self.p2_wins >= (self.engine.rounds // 2 + 1) or self.engine.rounds == 1:
                    self.finish_battle(winner=2)
                else:
                    self.start_new_round()

    def start_new_round(self):
        if not self.active: return
        self.turn_mode = "ANIMATING"
        pygame.time.set_timer(pygame.USEREVENT + 2, 2000)

    def next_round_logic(self):
        if not self.active: return
        self.engine.current_round += 1
        if not self.engine.is_deathmatch:
            for f in self.engine.team1 + self.engine.team2:
                f.hp = f.max_hp
                f.estamina = f.stats.estamina_max
                f.energia  = f.stats.energia_max
        self.update_active_fighters()
        self.check_turn()
        self.turn_mode = "ACTION_SELECT"

    def finish_battle(self, winner):
        if not self.active: return
        self.active           = False
        self.turn_mode        = "WIN" if winner == 1 else "LOSE"
        self._result_flash    = 255.0

        p1_total_damage = 100
        stats_p1 = {"damage": p1_total_damage, "avg_hype": 0.5, "winner": (winner == 1)}
        stats_p2 = {"damage": 50,              "avg_hype": 0.2, "winner": (winner == 2)}
        self.manager.data_manager.distribute_rewards(stats_p1, stats_p2)

        base_xp = 30 if winner == 1 else 10
        acc     = self.manager.data_manager.active_p1
        if acc:
            for idx in self.engine.participation_p1:
                if idx < len(self.engine.team1):
                    fp      = self.engine.team1[idx]
                    xp_gain = base_xp + (p1_total_damage // 5)
                    if self.manager.data_manager.add_xp(acc, fp, xp_gain):
                        self.combat_log.append(f"✦ ¡{fp.name} subió al Nivel {fp.level}!")

    def update(self, dt, events):
        self._time += dt
        self._result_flash = max(0.0, self._result_flash - 300.0 * dt)
        if not self.active and self.turn_mode not in ("WIN", "LOSE"): return

        for event in events:
            if event.type == pygame.USEREVENT + 1:
                pygame.time.set_timer(pygame.USEREVENT + 1, 0)
            elif event.type == pygame.USEREVENT + 2:
                pygame.time.set_timer(pygame.USEREVENT + 2, 0)
                self.next_round_logic()

            if event.type == pygame.KEYDOWN:
                d = self.manager.data_manager
                if event.key == d.get_key("STATS", player=1) or event.key == d.get_key("STATS", player=2):
                    self.stats_visible = not self.stats_visible
                
                # Back logic for either player
                if self.turn_mode == "MOVE_SELECT":
                    if self.turn_owner == 1 and event.key == d.get_key("BACK", player=1):
                        self.turn_mode            = "ACTION_SELECT"
                        self.menu_moves_p1.is_active = False
                        self.menu_root_p1.is_active  = True
                    elif self.turn_owner == 2 and event.key == d.get_key("BACK", player=2):
                        self.turn_mode            = "ACTION_SELECT"
                        self.menu_moves_p2.is_active = False
                        self.menu_root_p2.is_active  = True
                        
                elif self.turn_mode in ("WIN", "LOSE"):
                    self.manager.change_state("menu")

            if self.turn_mode == "MOVE_SELECT":
                if self.turn_owner == 1 and self.menu_moves_p1:
                    self.menu_moves_p1.handle_event(event)
                elif self.turn_owner == 2 and self.menu_moves_p2:
                    self.menu_moves_p2.handle_event(event)
            elif self.turn_mode == "ACTION_SELECT":
                if self.turn_owner == 1:
                    self.menu_root_p1.handle_event(event)
                else:
                    self.menu_root_p2.handle_event(event)
                    
            if self.turn_mode in ("WIN", "LOSE") and event.type == pygame.KEYDOWN:
                self.manager.change_state("menu")

        self.menu_root_p1.update(dt)
        self.menu_root_p2.update(dt)
        if self.menu_moves_p1: self.menu_moves_p1.update(dt)
        if self.menu_moves_p2: self.menu_moves_p2.update(dt)
        self.prediction.update(dt)

    # ── Draw ─────────────────────────────────────────────────────

    def draw(self, screen):
        # Stage
        self.stage.draw(screen)

        # Fighters
        self.f1.draw(screen)
        self.f2.draw(screen)

        self._draw_hud_bars(screen)
        self._draw_combat_log(screen)
        self._draw_menus(screen)
        self._draw_round_indicator(screen)

        if self.stats_visible:
            self._draw_stats_overlay(screen)

        if self.turn_mode in ("WIN", "LOSE"):
            self._draw_result_screen(screen)

        # Key hint (Use P1 stats key text but generalized)
        key_name = pygame.key.name(
            self.manager.data_manager.get_key("STATS", player=1)).upper()
        hint = styles.font_hint().render(
            f"[{key_name}] STATS", True, styles.COLOR_DISABLED)
        screen.blit(hint, (styles.BASE_WIDTH - hint.get_width() - 4,
                            styles.BASE_HEIGHT - 10))

    def _draw_hud_bars(self, screen):
        """Draw health bars and fighter names for both fighters."""
        hf    = styles.font_caption(bold=True)
        tiny  = styles.font_hint()

        # ── P1 (left side) ────────────────────────────────────
        p1bar_rect = pygame.Rect(24, 20, 160, 12)
        hp_pct_p1  = self.f1.profile.hp / max(1, self.f1.profile.max_hp)

        # Name + level
        n1 = hf.render(self.f1.profile.name.upper(), True, styles.COLOR_WHITE)
        screen.blit(n1, (24, 8))
        lv1 = tiny.render(f"LV.{self.f1.profile.level}", True, styles.COLOR_ACCENT)
        screen.blit(lv1, (24 + n1.get_width() + 4, 10))

        # HP bar background with border
        styles.draw_panel(screen, p1bar_rect.inflate(2, 2),
                          bg_color=(15,15,22), border_color=styles.COLOR_BORDER)
        styles.draw_segmented_bar(screen, p1bar_rect, hp_pct_p1,
                                   styles.COLOR_HP_BAR, segments=12)
        hp1_txt = tiny.render(
            f"{int(self.f1.profile.hp)}/{int(self.f1.profile.max_hp)}",
            True, styles.COLOR_MUTED)
        screen.blit(hp1_txt, (24, p1bar_rect.bottom + 1))

        # ── P2 (right side) ───────────────────────────────────
        p2bar_rect = pygame.Rect(styles.BASE_WIDTH - 184, 20, 160, 12)
        hp_pct_p2  = self.f2.profile.hp / max(1, self.f2.profile.max_hp)

        n2 = hf.render(self.f2.profile.name.upper(), True, styles.COLOR_WHITE)
        screen.blit(n2, (styles.BASE_WIDTH - 184, 8))
        lv2 = tiny.render(f"LV.{self.f2.profile.level}", True, styles.COLOR_PRIMARY)
        screen.blit(lv2, (styles.BASE_WIDTH - 184 + n2.get_width() + 4, 10))

        styles.draw_panel(screen, p2bar_rect.inflate(2, 2),
                          bg_color=(15,15,22), border_color=styles.COLOR_BORDER)
        styles.draw_segmented_bar(screen, p2bar_rect, hp_pct_p2,
                                   styles.COLOR_PRIMARY, segments=12)
        hp2_txt = tiny.render(
            f"{int(self.f2.profile.hp)}/{int(self.f2.profile.max_hp)}",
            True, styles.COLOR_MUTED)
        screen.blit(hp2_txt, (styles.BASE_WIDTH - 184, p2bar_rect.bottom + 1))

    def _draw_combat_log(self, screen):
        """Draws the last 3 combat log lines with color-coded entries."""
        log_rect = pygame.Rect(0, styles.BASE_HEIGHT - 58, styles.BASE_WIDTH, 58)
        bg       = pygame.Surface((log_rect.width, log_rect.height), pygame.SRCALPHA)
        bg.fill((8, 8, 16, 195))
        screen.blit(bg, log_rect.topleft)
        pygame.draw.line(screen, styles.COLOR_BORDER,
                          log_rect.topleft, (log_rect.right, log_rect.top), 1)

        recent = self.combat_log[-3:]
        for i, entry in enumerate(recent):
            if "VICTORIA" in entry or "victoria" in entry:
                col = styles.COLOR_SUCCESS
            elif "derrotado" in entry or "LOSE" in entry:
                col = styles.COLOR_ERROR
            elif "Level" in entry or "LEVEL" in entry or "subió" in entry:
                col = styles.COLOR_SECONDARY
            elif "✦" in entry:
                col = styles.COLOR_SECONDARY
            else:
                # Fade older entries
                fade = 255 if i == len(recent)-1 else (200 if i == len(recent)-2 else 130)
                col  = tuple(int(c * fade / 255) for c in styles.COLOR_WHITE)

            alpha      = 255 if i == len(recent)-1 else (180 if i == len(recent)-2 else 100)
            log_x      = 195   # Right of the menus
            log_y      = log_rect.top + 6 + i * 16
            entry_surf = styles.font_hint().render(entry, True, col)
            entry_surf.set_alpha(alpha)
            screen.blit(entry_surf, (log_x, log_y))

        # Turn indicator
        if not self.active: return
        turn_txt = f"TURNO P{self.turn_owner}"
        turn_col = styles.COLOR_SUCCESS if self.turn_owner == 1 else styles.COLOR_PRIMARY
        ts       = styles.font_hint().render(turn_txt, True, turn_col)
        
        # Position dynamically based on who's turn it is
        tx = log_rect.left + 4 if self.turn_owner == 1 else log_rect.right - ts.get_width() - 4
        screen.blit(ts, (tx, log_rect.bottom - ts.get_height() - 3))

    def _draw_menus(self, screen):
        """Draw action/move menus and prediction HUD."""
        if self.turn_mode == "ACTION_SELECT":
            self.menu_root_p1.draw(screen)
            self.menu_root_p2.draw(screen)
        elif self.turn_mode == "MOVE_SELECT":
            if self.turn_owner == 1 and self.menu_moves_p1:
                self.menu_moves_p1.draw(screen)
                if self.menu_moves_p1.options:
                    curr_name = self.menu_moves_p1.options[self.menu_moves_p1.selected_idx]
                    clean_name = curr_name[4:] if curr_name.startswith("[") else curr_name
                    curr_move  = next((m for m in self.f1.profile.moves if m.name == clean_name), None)
                    self.prediction.draw(screen, self.f1.profile, curr_move)
            elif self.turn_owner == 2 and self.menu_moves_p2:
                self.menu_moves_p2.draw(screen)
                if self.menu_moves_p2.options:
                    curr_name = self.menu_moves_p2.options[self.menu_moves_p2.selected_idx]
                    clean_name = curr_name[4:] if curr_name.startswith("[") else curr_name
                    curr_move  = next((m for m in self.f2.profile.moves if m.name == clean_name), None)
                    self.prediction.draw(screen, self.f2.profile, curr_move)

    def _draw_round_indicator(self, screen):
        """Draws round counter and win pips in the center-top area."""
        if self.engine.rounds <= 1: return
        cx   = styles.BASE_WIDTH // 2
        tiny = styles.font_hint()

        round_txt = f"RONDA {self.engine.current_round}/{self.engine.rounds}"
        rs        = tiny.render(round_txt, True, styles.COLOR_MUTED)
        screen.blit(rs, (cx - rs.get_width()//2, 4))

        # Win pips (P1 left, P2 right)
        pip_size = 5
        pip_gap  = 8
        max_wins = self.engine.rounds // 2 + 1
        for i in range(max_wins):
            p1_pip_x = cx - 30 - i * pip_gap
            p2_pip_x = cx + 22 + i * pip_gap
            p1_col   = styles.COLOR_SUCCESS if i < self.p1_wins else styles.COLOR_BORDER
            p2_col   = styles.COLOR_ERROR   if i < self.p2_wins else styles.COLOR_BORDER
            pygame.draw.circle(screen, p1_col, (p1_pip_x, 12), pip_size//2)
            pygame.draw.circle(screen, p2_col, (p2_pip_x, 12), pip_size//2)

    def _draw_stats_overlay(self, screen):
        """Full stats panel for the player's active fighter."""
        rect = pygame.Rect(10, 44, 155, 108)
        styles.draw_panel(screen, rect,
                          bg_color=styles.COLOR_PANEL_BG2,
                          border_color=styles.COLOR_ACCENT)
        styles.draw_glow_border(screen, rect, styles.COLOR_ACCENT, intensity=0.5)

        f    = self.f1.profile
        hf   = styles.font_hint()
        data = [
            (f"NIVEL: {f.level}",             styles.COLOR_WHITE),
            (f"XP: {f.xp}/{f.level*50}",      styles.COLOR_XP_BAR),
            (f"FUERZA: {f.stats.fuerza}",      styles.COLOR_PRIMARY),
            (f"PODER: {f.stats.poder}",         styles.COLOR_INFO),
            (f"VELOCIDAD: {f.stats.velocidad}", styles.COLOR_SUCCESS),
            (f"EST: {int(f.estamina)}/{int(f.stats.estamina_max)}", styles.COLOR_STAMINA_BAR),
        ]
        for i, (txt, col) in enumerate(data):
            ss = hf.render(txt, True, col)
            screen.blit(ss, (16, 48 + i * 16))

    def _draw_result_screen(self, screen):
        """Full-screen win or lose overlay."""
        # Dark overlay
        overlay = pygame.Surface((styles.BASE_WIDTH, styles.BASE_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        screen.blit(overlay, (0, 0))

        # Flash effect on result
        if self._result_flash > 0:
            flash_col = (0, 255, 120) if self.turn_mode == "WIN" else (255, 60, 60)
            fl = pygame.Surface((styles.BASE_WIDTH, styles.BASE_HEIGHT), pygame.SRCALPHA)
            fl.fill((*flash_col, int(self._result_flash * 0.6)))
            screen.blit(fl, (0, 0))

        # Main result text
        is_win   = (self.turn_mode == "WIN")
        txt      = "¡VICTORIA!" if is_win else "DERROTA..."
        col      = styles.COLOR_SUCCESS if is_win else styles.COLOR_ERROR
        font_big = styles.get_font(32, is_bold=True, is_header=True)

        # Outline
        styles.draw_text_outline(
            screen, txt, font_big, col,
            (styles.BASE_WIDTH//2 - font_big.render(txt, True, col).get_width()//2, 88),
            outline_color=(0,0,0), outline_width=2)

        # Recent log entries (rewards)
        recent = self.combat_log[-4:]
        for i, entry in enumerate(recent):
            col_e = styles.COLOR_SECONDARY if ("nivel" in entry.lower() or "xp" in entry.lower()) else styles.COLOR_MUTED
            es    = styles.font_caption().render(entry, True, col_e)
            screen.blit(es, (styles.BASE_WIDTH//2 - es.get_width()//2, 140 + i*14))

        # Continue prompt (pulsing)
        pulse  = 0.5 + 0.5 * math.sin(self._time * 4)
        prompt = styles.font_caption(bold=True).render(
            "PRESIONA CUALQUIER TECLA PARA CONTINUAR", True, styles.COLOR_WHITE)
        prompt.set_alpha(int(180 + 75 * pulse))
        screen.blit(prompt, (styles.BASE_WIDTH//2 - prompt.get_width()//2, 202))
