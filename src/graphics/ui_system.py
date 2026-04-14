import pygame
import math
from src.graphics import styles

# ============================================================
# WAR BRAWL ARENA II — Unified UI Widget System
# ============================================================

class UIElement:
    """Base class for all UI elements with smooth animation support."""
    def __init__(self, manager, pos, size):
        self.manager     = manager
        self.rect        = pygame.Rect(pos, size)
        self.target_pos  = pygame.Vector2(pos)
        self.current_pos = pygame.Vector2(pos)
        self.is_hovered  = False
        self.alpha       = 255
        self._time       = 0.0

    def update(self, dt):
        self._time += dt
        speed = 12.0
        self.current_pos.x += (self.target_pos.x - self.current_pos.x) * speed * dt
        self.current_pos.y += (self.target_pos.y - self.current_pos.y) * speed * dt
        self.rect.topleft = (int(self.current_pos.x), int(self.current_pos.y))

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            prev = self.is_hovered
            self.is_hovered = self.rect.collidepoint(event.pos)
            if self.is_hovered and not prev:
                try:
                    self.manager.data_manager.play_sfx("hover")
                except Exception:
                    pass

    def draw(self, surface):
        pass


# ============================================================
# PIXEL BUTTON — Primary interactive control
# ============================================================

class PixelButton(UIElement):
    """
    Professional retro-style button with variants.
    variant: "primary" | "secondary" | "danger" | "ghost" | "success"
    """
    VARIANTS = {
        "primary":   (styles.COLOR_PRIMARY,   (180, 20, 50)),
        "secondary": (styles.COLOR_SECONDARY, (180, 140, 0)),
        "danger":    ((220, 50, 50),           (150, 30, 30)),
        "ghost":     (styles.COLOR_BORDER_MID, (50, 50, 70)),
        "success":   (styles.COLOR_SUCCESS,    (40, 160, 70)),
        "info":      (styles.COLOR_ACCENT,     (0, 140, 180)),
    }

    def __init__(self, manager, text, pos, size=(120, 24), callback=None,
                 base_color=None, variant="ghost", tooltip_text=None, font_size=None):
        super().__init__(manager, pos, size)
        self.text         = text
        self.callback     = callback
        self.variant      = variant
        self.tooltip_text = tooltip_text
        self._hover_lift  = 0.0
        self._press_scale = 1.0
        self._pressed     = False
        self._tooltip_timer = 0.0

        fs = font_size if font_size else styles.FONT_SIZE["BODY"]
        self.font      = styles.get_font(fs, is_bold=True)
        self.text_surf = self.font.render(self.text, True, styles.COLOR_WHITE)

        # Resolve colors
        if base_color:
            self.color_normal = base_color
            self.color_hover  = base_color
        else:
            var = self.VARIANTS.get(variant, self.VARIANTS["ghost"])
            self.color_normal = var[1]
            self.color_hover  = var[0]

    def set_text(self, text):
        self.text = text
        self.text_surf = self.font.render(text, True, styles.COLOR_WHITE)

    def update(self, dt):
        super().update(dt)
        if self.is_hovered:
            self._hover_lift  = min(3.0, self._hover_lift + 18.0 * dt)
            if self.tooltip_text:
                self._tooltip_timer += dt
        else:
            self._hover_lift  = max(0.0, self._hover_lift - 18.0 * dt)
            self._tooltip_timer = 0.0
        if self._pressed:
            self._press_scale = max(0.93, self._press_scale - 5.0 * dt)
        else:
            self._press_scale = min(1.0, self._press_scale + 5.0 * dt)

    def handle_event(self, event):
        super().handle_event(event)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered:
                self._pressed = True
                try:
                    self.manager.data_manager.play_sfx("click")
                except Exception:
                    pass
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._pressed and self.is_hovered and self.callback:
                self.callback()
            self._pressed = False

    def draw(self, surface):
        draw_rect = self.rect.copy()
        lift = int(self._hover_lift)
        draw_rect.y -= lift

        # Shadow
        shadow_rect = draw_rect.copy()
        shadow_rect.x += 2
        shadow_rect.y += 2 + lift
        shadow_surf = pygame.Surface((draw_rect.width, draw_rect.height), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, 80))
        surface.blit(shadow_surf, shadow_rect.topleft)

        # Body color
        color = self.color_hover if self.is_hovered else self.color_normal
        pygame.draw.rect(surface, color, draw_rect, border_radius=styles.PANEL_RADIUS)

        # Border
        border_col = styles.COLOR_WHITE if self.is_hovered else styles.COLOR_BORDER_MID
        pygame.draw.rect(surface, border_col, draw_rect, 1, border_radius=styles.PANEL_RADIUS)

        # Top highlight stripe (bevel effect)
        if draw_rect.height > 6:
            hi_rect = pygame.Rect(draw_rect.x+1, draw_rect.y+1, draw_rect.width-2, 2)
            hi_surf = pygame.Surface((hi_rect.width, hi_rect.height), pygame.SRCALPHA)
            hi_surf.fill((255, 255, 255, 30))
            surface.blit(hi_surf, hi_rect.topleft)

        # Text
        tx = draw_rect.centerx - self.text_surf.get_width() // 2
        ty = draw_rect.centery - self.text_surf.get_height() // 2
        if self._pressed:
            ty += 1
        surface.blit(self.text_surf, (tx, ty))

        # Tooltip
        if self.tooltip_text and self._tooltip_timer > 0.5:
            self._draw_tooltip(surface, draw_rect)

    def _draw_tooltip(self, surface, anchor_rect):
        font = styles.font_hint()
        txt  = font.render(self.tooltip_text, True, styles.COLOR_WHITE)
        w    = txt.get_width() + 8
        h    = txt.get_height() + 6
        tx   = anchor_rect.centerx - w // 2
        ty   = anchor_rect.top - h - 4
        ty   = max(2, ty)

        bg = pygame.Surface((w, h), pygame.SRCALPHA)
        bg.fill((20, 20, 35, 220))
        surface.blit(bg, (tx, ty))
        pygame.draw.rect(surface, styles.COLOR_ACCENT, (tx, ty, w, h), 1, border_radius=2)
        surface.blit(txt, (tx + 4, ty + 3))


# ============================================================
# HEALTH BAR — Combat HP tracker with ghost HP
# ============================================================

class HealthBar(UIElement):
    """Retro health bar with ghost segment for recent damage."""
    def __init__(self, manager, pos, size=(150, 14), is_right_aligned=False):
        super().__init__(manager, pos, size)
        self.hp_percent    = 1.0
        self.ghost_percent = 1.0
        self.is_right_aligned = is_right_aligned

    def set_hp(self, percent):
        self.hp_percent = max(0.0, min(1.0, percent))

    def update(self, dt):
        super().update(dt)
        if self.ghost_percent > self.hp_percent:
            self.ghost_percent = max(self.hp_percent, self.ghost_percent - 0.4 * dt)
        else:
            self.ghost_percent = self.hp_percent

    def draw(self, surface):
        color = styles.COLOR_HP_BAR
        if self.hp_percent < 0.3:
            color = styles.COLOR_ERROR
        elif self.hp_percent < 0.6:
            color = styles.COLOR_WARNING
        styles.draw_segmented_bar(surface, self.rect, self.hp_percent, color,
                                  segments=12, ghost_percent=self.ghost_percent)


# ============================================================
# STAT BAR — Visual attribute representation
# ============================================================

class StatBar(UIElement):
    """
    Visual stat bar for Profile/Gym screens.
    Draws label, numeric value, and a colored fill bar.
    """
    def __init__(self, manager, pos, size, label, value, max_value, color, show_value=True):
        super().__init__(manager, pos, size)
        self.label     = label
        self.value     = value
        self.max_value = max_value
        self.color     = color
        self.show_value = show_value
        self._anim_pct = 0.0   # Animated fill proportion

    def set_value(self, value, max_value=None):
        self.value = value
        if max_value: self.max_value = max_value

    def update(self, dt):
        super().update(dt)
        target = self.value / max(1, self.max_value)
        self._anim_pct += (target - self._anim_pct) * 8.0 * dt

    def draw(self, surface):
        font_lbl = styles.font_caption(bold=True)
        font_val = styles.font_caption(bold=True)

        # Label on left
        lbl_surf = font_lbl.render(self.label, True, styles.COLOR_MUTED)
        surface.blit(lbl_surf, (self.rect.x, self.rect.centery - lbl_surf.get_height() // 2))

        # Bar in the middle
        bar_x = self.rect.x + 80
        bar_w = self.rect.width - 80 - (30 if self.show_value else 0)
        bar_rect = pygame.Rect(bar_x, self.rect.y, bar_w, self.rect.height)
        styles.draw_stat_bar(surface, bar_rect, self._anim_pct, self.color)

        # Value on right
        if self.show_value:
            val_surf = font_val.render(str(self.value), True, self.color)
            vx = self.rect.right - val_surf.get_width()
            surface.blit(val_surf, (vx, self.rect.centery - val_surf.get_height() // 2))


# ============================================================
# PROGRESS BAR — Generic bar (XP, training, loading)
# ============================================================

class ProgressBar(UIElement):
    """A versatile animated progress bar."""
    def __init__(self, manager, pos, size=(200, 10), color=None, label=None):
        super().__init__(manager, pos, size)
        self.percent    = 0.0
        self._anim_pct  = 0.0
        self.color      = color if color else styles.COLOR_PRIMARY
        self.label      = label

    def set_percent(self, p):
        self.percent = max(0.0, min(1.0, p))

    def update(self, dt):
        super().update(dt)
        self._anim_pct += (self.percent - self._anim_pct) * 6.0 * dt

    def draw(self, surface):
        styles.draw_stat_bar(surface, self.rect, self._anim_pct, self.color,
                             label=self.label)


# ============================================================
# STAT EDITOR — Lab upgrade widget
# ============================================================

class StatEditor(UIElement):
    """Widget for the Laboratory to increase/decrease stats."""
    def __init__(self, manager, label, value, pos, callback_change=None):
        super().__init__(manager, pos, (190, 22))
        self.label    = label
        self.value    = value
        self.callback = callback_change
        self.font     = styles.font_body()

        self.btn_minus = PixelButton(manager, "-", (pos[0]+100, pos[1]),
                                     size=(22, 22), callback=lambda: self.change(-1),
                                     variant="danger")
        self.btn_plus  = PixelButton(manager, "+", (pos[0]+126, pos[1]),
                                     size=(22, 22), callback=lambda: self.change(1),
                                     variant="success")

    def change(self, delta):
        if self.callback:
            self.callback(delta)

    def handle_event(self, event):
        self.btn_minus.handle_event(event)
        self.btn_plus.handle_event(event)

    def update(self, dt):
        self.btn_minus.update(dt)
        self.btn_plus.update(dt)

    def draw(self, surface):
        lbl = self.font.render(f"{self.label}: {self.value}", True, styles.COLOR_WHITE)
        surface.blit(lbl, (self.rect.x, self.rect.y + 3))
        self.btn_minus.draw(surface)
        self.btn_plus.draw(surface)


# ============================================================
# COMMAND MENU — Combat action selector
# ============================================================

class CommandMenu(UIElement):
    """Nested combat menu supporting keyboard and mouse navigation."""
    def __init__(self, manager, pos, options_dict, callback, player_id=1):
        super().__init__(manager, pos, (148, 100))
        self.options_dict    = options_dict
        self.options         = list(options_dict.keys())
        self.callback        = callback
        self.player_id       = player_id
        self.selected_idx    = 0
        self.current_layer   = "ROOT"
        self.path            = []
        self.font            = styles.font_body()
        self.font_hint       = styles.font_hint()
        self.is_active       = True
        self._time           = 0.0
        self.row_h           = 20

    def handle_event(self, event):
        if not self.is_active:
            return
        if event.type == pygame.KEYDOWN:
            d = self.manager.data_manager
            if event.key == d.get_key("DOWN", player=self.player_id):
                self.selected_idx = (self.selected_idx + 1) % len(self.options)
                d.play_sfx("hover")
            elif event.key == d.get_key("UP", player=self.player_id):
                self.selected_idx = (self.selected_idx - 1) % len(self.options)
                d.play_sfx("hover")
            elif event.key == d.get_key("CONFIRM", player=self.player_id):
                self.select_option()
            elif event.key == d.get_key("BACK", player=self.player_id) and self.current_layer != "ROOT":
                self.back()

    def select_option(self):
        choice = self.options[self.selected_idx]
        sub    = self.options_dict.get(choice)
        if isinstance(sub, list):
            self.path.append((self.current_layer, self.options))
            self.current_layer = choice
            self.options       = sub
            self.selected_idx  = 0
        else:
            self.callback(choice)

    def back(self):
        self.current_layer, self.options = self.path.pop()
        self.selected_idx = 0

    def draw(self, surface):
        if not self.is_active:
            return
        self._time += 0.016

        n_rows  = len(self.options)
        menu_h  = n_rows * self.row_h + 10
        menu_w  = self.rect.width
        bg_rect = pygame.Rect(self.rect.x, self.rect.y, menu_w, menu_h)

        # Background panel
        styles.draw_panel(surface, bg_rect, bg_color=styles.COLOR_PANEL_BG2,
                          border_color=styles.COLOR_PRIMARY)

        for i, opt in enumerate(self.options):
            is_sel = (i == self.selected_idx)
            y = self.rect.y + 5 + i * self.row_h

            if is_sel:
                # Selection highlight
                hi_rect = pygame.Rect(bg_rect.x + 1, y - 1, menu_w - 2, self.row_h)
                hi_surf = pygame.Surface((hi_rect.width, hi_rect.height), pygame.SRCALPHA)
                hi_surf.fill((*styles.COLOR_PRIMARY, 45))
                surface.blit(hi_surf, hi_rect.topleft)
                # Cursor arrow
                arrow_x = bg_rect.x + 4
                arrow_y = y + self.row_h // 2
                pulsed_alpha = styles.pulse_alpha(self._time, speed=3)
                arrow_surf = pygame.Surface((6, 6), pygame.SRCALPHA)
                pygame.draw.polygon(arrow_surf, (*styles.COLOR_PRIMARY, pulsed_alpha),
                                    [(0, 0), (0, 5), (5, 2)])
                surface.blit(arrow_surf, (arrow_x, arrow_y - 3))

            color = styles.COLOR_ACCENT if is_sel else styles.COLOR_WHITE
            text  = self.font.render(opt, True, color)
            surface.blit(text, (bg_rect.x + 14, y + 2))


# ============================================================
# TEXT INPUT — Professional entry field
# ============================================================

class TextInput(UIElement):
    """Professional text entry field with cursor and placeholder."""
    def __init__(self, manager, pos, size=(200, 28), placeholder="", is_password=False):
        super().__init__(manager, pos, size)
        self.text         = ""
        self.placeholder  = placeholder
        self.is_password  = is_password
        self.active       = False
        self.font         = styles.font_body()
        self.font_ph      = styles.font_body(bold=False)
        self.cursor_vis   = True
        self.cursor_timer = 0.0
        self._focus_time  = 0.0

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if self.active and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_v and pygame.key.get_mods() & pygame.KMOD_CTRL:
                try:
                    clip = pygame.scrap.get(pygame.SCRAP_TEXT)
                    if clip:
                        self.text += clip.decode().strip("\x00")
                except Exception:
                    pass
            else:
                if len(self.text) < 24 and event.unicode.isprintable():
                    self.text += event.unicode

    def update(self, dt):
        super().update(dt)
        self.cursor_timer += dt
        if self.cursor_timer >= 0.5:
            self.cursor_vis   = not self.cursor_vis
            self.cursor_timer = 0.0
        if self.active:
            self._focus_time += dt

    def draw(self, surface):
        # Border color based on focus
        border_color = styles.COLOR_PRIMARY if self.active else styles.COLOR_BORDER
        pygame.draw.rect(surface, styles.COLOR_PANEL_BG2, self.rect, border_radius=styles.PANEL_RADIUS)
        pygame.draw.rect(surface, border_color, self.rect, 2, border_radius=styles.PANEL_RADIUS)

        # Bottom accent line when active
        if self.active:
            pygame.draw.line(surface, styles.COLOR_PRIMARY,
                             (self.rect.x+2, self.rect.bottom-1),
                             (self.rect.right-2, self.rect.bottom-1), 2)

        # Text render
        display = ("*" * len(self.text)) if self.is_password else self.text
        if not self.text and not self.active:
            surf = self.font_ph.render(self.placeholder, True, styles.COLOR_DISABLED)
        else:
            surf = self.font.render(display if display else " ", True, styles.COLOR_WHITE)

        ty = self.rect.centery - surf.get_height() // 2
        surface.blit(surf, (self.rect.x + 6, ty))

        # Cursor
        if self.active and self.cursor_vis:
            cx = self.rect.x + 6 + surf.get_width() + 1
            pygame.draw.line(surface, styles.COLOR_ACCENT,
                             (cx, self.rect.y+4), (cx, self.rect.bottom-4), 2)


# ============================================================
# SLIDER — Volume/Settings control
# ============================================================

class Slider(UIElement):
    """Visual slider for volume and setting controls."""
    def __init__(self, manager, label, pos, value=0.5, callback=None):
        super().__init__(manager, pos, (200, 28))
        self.label       = label
        self.value       = value
        self.callback    = callback
        self.is_dragging = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.is_dragging = True
        if event.type == pygame.MOUSEBUTTONUP:
            self.is_dragging = False
        if self.is_dragging and event.type == pygame.MOUSEMOTION:
            rel_x      = max(0, min(self.rect.width, event.pos[0] - self.rect.x))
            self.value = rel_x / self.rect.width
            if self.callback:
                self.callback(self.value)

    def draw(self, surface):
        font = styles.font_caption(bold=True)
        lbl  = font.render(f"{self.label}: {int(self.value * 100)}%", True, styles.COLOR_WHITE)
        surface.blit(lbl, (self.rect.x, self.rect.y))

        # Track
        track_y  = self.rect.y + 18
        track_h  = 5
        track_rect = pygame.Rect(self.rect.x, track_y, self.rect.width, track_h)
        pygame.draw.rect(surface, styles.COLOR_PANEL_BG2, track_rect, border_radius=2)
        pygame.draw.rect(surface, styles.COLOR_BORDER, track_rect, 1, border_radius=2)

        # Fill
        fill_w = int(self.value * self.rect.width)
        if fill_w > 0:
            fill_rect = pygame.Rect(self.rect.x, track_y, fill_w, track_h)
            pygame.draw.rect(surface, styles.COLOR_ACCENT, fill_rect, border_radius=2)

        # Handle
        hx = self.rect.x + int(self.value * self.rect.width)
        handle_rect = pygame.Rect(hx - 5, track_y - 4, 10, track_h + 8)
        pygame.draw.rect(surface, styles.COLOR_WHITE, handle_rect, border_radius=3)
        pygame.draw.rect(surface, styles.COLOR_ACCENT, handle_rect, 1, border_radius=3)


# ============================================================
# FEEDBACK MESSAGE — Animated status messages
# ============================================================

class FeedbackMessage:
    """
    Animated feedback message that appears and fades out.
    Replaces simple self.message strings across all states.
    """
    def __init__(self, duration=2.5):
        self._text     = ""
        self._color    = styles.COLOR_WHITE
        self._timer    = 0.0
        self._duration = duration
        self._alpha    = 0

    def show(self, text, kind="info"):
        """
        Display a message of a given kind:
        "success", "error", "warning", "info"
        """
        self._text    = text
        self._timer   = self._duration
        color_map = {
            "success": styles.COLOR_SUCCESS,
            "error":   styles.COLOR_ERROR,
            "warning": styles.COLOR_WARNING,
            "info":    styles.COLOR_ACCENT,
        }
        self._color = color_map.get(kind, styles.COLOR_WHITE)

    @property
    def is_visible(self):
        return self._timer > 0

    def update(self, dt):
        if self._timer > 0:
            self._timer  = max(0.0, self._timer - dt)
            fade_start   = 0.6
            if self._timer < fade_start:
                self._alpha = int(255 * (self._timer / fade_start))
            else:
                self._alpha = 255

    def draw(self, surface, y=None, x=None):
        if not self.is_visible or not self._text:
            return
        font = styles.font_body(bold=True)
        txt  = font.render(self._text, True, self._color)

        # Background pill
        margin = 8
        bw = txt.get_width() + margin * 2
        bh = txt.get_height() + 6

        bx = (x - bw // 2) if x else (styles.BASE_WIDTH // 2 - bw // 2)
        by = y if y else (styles.BASE_HEIGHT - bh - 8)

        bg_surf = pygame.Surface((bw, bh), pygame.SRCALPHA)
        r, g, b = self._color
        bg_surf.fill((max(0, r-120), max(0, g-120), max(0, b-120), max(0, min(200, self._alpha - 30))))
        surface.blit(bg_surf, (bx, by))

        txt_surf = pygame.Surface((txt.get_width(), txt.get_height()), pygame.SRCALPHA)
        txt_surf.blit(txt, (0, 0))
        txt_surf.set_alpha(self._alpha)
        surface.blit(txt_surf, (bx + margin, by + 3))


# ============================================================
# TOOLTIP — Hover-activated context help
# ============================================================

class Tooltip:
    """
    Standalone tooltip that can be attached to any rect.
    Draw after calling update() with the current mouse position.
    """
    def __init__(self, text, delay=0.5):
        self.text       = text
        self.delay      = delay
        self._timer     = 0.0
        self._visible   = False
        self._target_rect = None

    def set_target(self, rect):
        self._target_rect = rect

    def update(self, dt, mouse_pos):
        if self._target_rect and self._target_rect.collidepoint(mouse_pos):
            self._timer += dt
            self._visible = self._timer >= self.delay
        else:
            self._timer   = 0.0
            self._visible = False

    def draw(self, surface, mouse_pos):
        if not self._visible or not self.text:
            return
        font = styles.font_hint()
        txt  = font.render(self.text, True, styles.COLOR_WHITE)
        w, h = txt.get_width() + 10, txt.get_height() + 6
        mx, my = mouse_pos
        tx = min(mx + 8, styles.BASE_WIDTH - w - 2)
        ty = max(2, my - h - 4)

        bg = pygame.Surface((w, h), pygame.SRCALPHA)
        bg.fill((15, 15, 30, 220))
        surface.blit(bg, (tx, ty))
        pygame.draw.rect(surface, styles.COLOR_ACCENT, (tx, ty, w, h), 1, border_radius=2)
        surface.blit(txt, (tx + 5, ty + 3))


# ============================================================
# NAV BAR — Consistent navigation across Hub screens
# ============================================================

class NavBar(UIElement):
    """
    Horizontal navigation bar for all hub screens.
    Shows icon + label buttons for quick navigation.
    """
    ITEMS = [
        ("GYM",       "gym",       "💪"),
        ("LAB",       "lab",       "🧪"),
        ("TIENDA",    "shop",      "🛒"),
        ("HOSPITAL",  "hospital",  "💊"),
        ("COLECCIÓN", "roster",    "👥"),
        ("MOCHILA",   "inventory", "🎒"),
        ("PERFIL",    "profile",   "⚡"),
        ("CONFIG",    "settings",  "⚙"),
    ]

    def __init__(self, manager, current_state="menu"):
        y = styles.BASE_HEIGHT - styles.NAV_HEIGHT
        super().__init__(manager, (0, y), (styles.BASE_WIDTH, styles.NAV_HEIGHT))
        self.current_state = current_state
        self._font = styles.font_hint()
        self._item_w = styles.BASE_WIDTH // len(self.ITEMS)
        self._hover_idx = -1
        self._time = 0.0

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            if self.rect.collidepoint(mx, my):
                self._hover_idx = (mx - self.rect.x) // self._item_w
            else:
                self._hover_idx = -1
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                idx = (event.pos[0] - self.rect.x) // self._item_w
                if 0 <= idx < len(self.ITEMS):
                    _, state, _ = self.ITEMS[idx]
                    try:
                        self.manager.data_manager.play_sfx("click")
                    except Exception:
                        pass
                    if state == "settings":
                        self.manager.push_state("settings")
                    else:
                        self.manager.change_state(state)

    def update(self, dt):
        self._time += dt

    def draw(self, surface):
        # Background
        bg = pygame.Surface((styles.BASE_WIDTH, styles.NAV_HEIGHT), pygame.SRCALPHA)
        bg.fill((*styles.COLOR_HEADER_BG, 240))
        surface.blit(bg, self.rect.topleft)
        # Top border
        pygame.draw.line(surface, styles.COLOR_BORDER,
                         self.rect.topleft, (self.rect.right, self.rect.top), 1)

        for i, (label, state, icon) in enumerate(self.ITEMS):
            x        = self.rect.x + i * self._item_w
            item_rect= pygame.Rect(x, self.rect.y, self._item_w, styles.NAV_HEIGHT)
            is_hover = (i == self._hover_idx)
            is_curr  = (state == self.current_state)

            if is_curr:
                sel_surf = pygame.Surface((self._item_w, styles.NAV_HEIGHT), pygame.SRCALPHA)
                sel_surf.fill((*styles.COLOR_PRIMARY, 40))
                surface.blit(sel_surf, item_rect.topleft)
                pygame.draw.line(surface, styles.COLOR_PRIMARY,
                                 (x, self.rect.y), (x + self._item_w, self.rect.y), 2)
            elif is_hover:
                hi_surf = pygame.Surface((self._item_w, styles.NAV_HEIGHT), pygame.SRCALPHA)
                hi_surf.fill((255, 255, 255, 15))
                surface.blit(hi_surf, item_rect.topleft)

            # Separator
            if i > 0:
                pygame.draw.line(surface, styles.COLOR_BORDER,
                                 (x, self.rect.y+3), (x, self.rect.bottom-3), 1)

            # Label
            color  = styles.COLOR_PRIMARY if is_curr else (
                     styles.COLOR_WHITE if is_hover else styles.COLOR_MUTED)
            lbl    = self._font.render(label, True, color)
            lx     = x + self._item_w // 2 - lbl.get_width() // 2
            ly     = self.rect.centery - lbl.get_height() // 2
            surface.blit(lbl, (lx, ly))


# ============================================================
# CARD WIDGET — Fighter / Item card for grids
# ============================================================

class CardWidget(UIElement):
    """
    A styled card for displaying fighters or items in a grid.
    Shows portrait (if available), name, level, and a mini stat bar.
    """
    def __init__(self, manager, pos, size, label, sublabel="", color_accent=None, on_click=None):
        super().__init__(manager, pos, size)
        self.label        = label
        self.sublabel     = sublabel
        self.color_accent = color_accent if color_accent else styles.COLOR_ACCENT
        self.on_click     = on_click
        self._image       = None
        self._hover_lift  = 0.0
        self.hp_pct       = 1.0    # Optional HP bar display

    def set_image(self, surface):
        self._image = surface

    def set_hp(self, pct):
        self.hp_pct = max(0.0, min(1.0, pct))

    def update(self, dt):
        super().update(dt)
        if self.is_hovered:
            self._hover_lift = min(3.0, self._hover_lift + 14.0 * dt)
        else:
            self._hover_lift = max(0.0, self._hover_lift - 14.0 * dt)

    def handle_event(self, event):
        super().handle_event(event)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered and self.on_click:
                self.on_click()

    def draw(self, surface):
        draw_rect = self.rect.copy()
        draw_rect.y -= int(self._hover_lift)

        # Shadow
        shd = draw_rect.copy()
        shd.x += 2; shd.y += 2 + int(self._hover_lift)
        shd_s = pygame.Surface((shd.width, shd.height), pygame.SRCALPHA)
        shd_s.fill((0, 0, 0, 70))
        surface.blit(shd_s, shd.topleft)

        # Card background
        bg = (42, 42, 60) if self.is_hovered else styles.COLOR_PANEL_BG
        pygame.draw.rect(surface, bg, draw_rect, border_radius=styles.PANEL_RADIUS)

        # Border
        bc = self.color_accent if self.is_hovered else styles.COLOR_BORDER
        pygame.draw.rect(surface, bc, draw_rect, 2, border_radius=styles.PANEL_RADIUS)

        # Portrait
        img_size = min(draw_rect.width - 6, draw_rect.height - 22)
        if self._image:
            img = pygame.transform.scale(self._image, (img_size, img_size))
            surface.blit(img, (draw_rect.centerx - img_size // 2, draw_rect.y + 3))
        else:
            # Placeholder silhouette
            ph_rect = pygame.Rect(draw_rect.centerx - img_size//2, draw_rect.y+3, img_size, img_size)
            ph_surf = pygame.Surface((img_size, img_size), pygame.SRCALPHA)
            pygame.draw.rect(ph_surf, (50, 50, 70, 200), ph_surf.get_rect(), border_radius=2)
            # Silhouette body shape
            cx = img_size // 2
            pygame.draw.circle(ph_surf, (70, 70, 95), (cx, img_size // 3), img_size // 5)
            pygame.draw.rect(ph_surf, (70, 70, 95),
                             pygame.Rect(cx - img_size//6, img_size//2, img_size//3, img_size//3))
            surface.blit(ph_surf, ph_rect.topleft)

        # Name label
        font = styles.font_hint()
        lbl  = font.render(self.label[:12], True, styles.COLOR_WHITE)
        surface.blit(lbl, (draw_rect.centerx - lbl.get_width()//2,
                           draw_rect.bottom - 18))

        # Sublabel (level)
        if self.sublabel:
            sub = font.render(self.sublabel, True, self.color_accent)
            surface.blit(sub, (draw_rect.centerx - sub.get_width()//2,
                               draw_rect.bottom - 10))

        # Mini HP bar at very bottom
        bar_rect = pygame.Rect(draw_rect.x+2, draw_rect.bottom-3, draw_rect.width-4, 3)
        pygame.draw.rect(surface, (30, 30, 40), bar_rect)
        hp_color = styles.COLOR_HP_BAR if self.hp_pct > 0.5 else (
                   styles.COLOR_WARNING if self.hp_pct > 0.25 else styles.COLOR_ERROR)
        pygame.draw.rect(surface, hp_color,
                         pygame.Rect(bar_rect.x, bar_rect.y,
                                     int(bar_rect.width * self.hp_pct), bar_rect.height))


# ============================================================
# CONFIRMATION DIALOG — Modal for destructive actions
# ============================================================

class ConfirmationDialog(UIElement):
    """Professional modal for confirming purchases or destructive actions."""
    def __init__(self, manager, message, on_confirm, on_cancel):
        w, h = 220, 100
        cx   = styles.BASE_WIDTH  // 2 - w // 2
        cy   = styles.BASE_HEIGHT // 2 - h // 2
        super().__init__(manager, (cx, cy), (w, h))
        self.message    = message
        self.on_confirm = on_confirm
        self.on_cancel  = on_cancel
        self.font       = styles.font_body()
        self.font_hint  = styles.font_hint()

        btn_y = self.rect.bottom - 32
        self.btn_confirm = PixelButton(manager, "CONFIRMAR",
                                       (self.rect.x + 8, btn_y),
                                       size=(95, 24), callback=on_confirm,
                                       variant="success")
        self.btn_cancel  = PixelButton(manager, "CANCELAR",
                                       (self.rect.x + w - 103, btn_y),
                                       size=(95, 24), callback=on_cancel,
                                       variant="danger")

    def handle_event(self, event):
        self.btn_confirm.handle_event(event)
        self.btn_cancel.handle_event(event)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.on_cancel()

    def update(self, dt):
        self.btn_confirm.update(dt)
        self.btn_cancel.update(dt)

    def draw(self, surface):
        # Dimmer overlay
        overlay = pygame.Surface((styles.BASE_WIDTH, styles.BASE_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        # Dialog box with glow border
        styles.draw_panel(surface, self.rect,
                          bg_color=styles.COLOR_PANEL_BG,
                          border_color=styles.COLOR_SECONDARY)
        styles.draw_glow_border(surface, self.rect, styles.COLOR_SECONDARY, intensity=0.6)

        # Message with word-wrap
        words   = self.message.split()
        lines   = []
        cur     = ""
        max_ch  = 24
        for w in words:
            if len(cur + w) <= max_ch:
                cur += w + " "
            else:
                lines.append(cur.strip())
                cur = w + " "
        lines.append(cur.strip())

        for i, line in enumerate(lines):
            surf = self.font.render(line, True, styles.COLOR_WHITE)
            surface.blit(surf, (self.rect.centerx - surf.get_width()//2,
                                self.rect.y + 12 + i * 15))

        self.btn_confirm.draw(surface)
        self.btn_cancel.draw(surface)


# ============================================================
# HELPER — Draw circular image
# ============================================================

def draw_circular_image(surface, image, pos, size):
    """Draws an image clipped to a circle (avatar/portrait frames)."""
    mask_surf = pygame.Surface(size, pygame.SRCALPHA)
    r = min(size) // 2
    pygame.draw.circle(mask_surf, (255, 255, 255, 255), (size[0]//2, size[1]//2), r)
    img_scaled = pygame.transform.scale(image, size)
    img_scaled.blit(mask_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    surface.blit(img_scaled, pos)
