import pygame
import math
import sys
import os

def resource_path(relative_path):
    """Resolves a resource path for both dev mode and PyInstaller frozen exe."""
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, relative_path)

# ============================================================
# WAR BRAWL ARENA II — UNIFIED DESIGN SYSTEM
# ============================================================

# --- LOGICAL RESOLUTION (Retro 16:9) ---
BASE_WIDTH  = 480
BASE_HEIGHT = 270

# ============================================================
# COLOR PALETTE — "Dark Nitro" Theme
# ============================================================

# Core Identity
COLOR_PRIMARY     = (255,  30,  80)   # Neon Red — actions, highlights
COLOR_SECONDARY   = (255, 204,   0)   # Champion Gold — rewards, titles
COLOR_ACCENT      = (  0, 210, 255)   # Cyber Blue — info, XP, accents

# Backgrounds
COLOR_BG          = ( 14,  14,  22)   # Deep dark charcoal
COLOR_HEADER_BG   = ( 22,  22,  34)   # Slightly lighter for headers
COLOR_PANEL_BG    = ( 28,  28,  42)   # Panel backgrounds
COLOR_PANEL_BG2   = ( 20,  20,  32)   # Alternate panel (darker)
COLOR_OVERLAY     = (  0,   0,   0)   # Used for alpha overlays

# Text
COLOR_WHITE       = (240, 240, 248)   # Slightly warm white
COLOR_MUTED       = (140, 140, 160)   # Secondary / disabled text
COLOR_DISABLED    = ( 70,  70,  90)   # Locked / unavailable

# Borders
COLOR_BORDER      = ( 55,  55,  75)   # Default panel border
COLOR_BORDER_MID  = ( 90,  90, 115)   # Intermediate border
COLOR_BORDER_BRIGHT = (130, 130, 160) # Bright border (hover)
COLOR_BLACK       = (  0,   0,   0)

# Semantic Feedback
COLOR_SUCCESS     = ( 80, 230, 120)   # Green — success messages
COLOR_ERROR       = (255,  60,  60)   # Red — error messages
COLOR_WARNING     = (255, 180,  40)   # Orange — warnings
COLOR_INFO        = (100, 190, 255)   # Blue — info messages

# Element-specific
COLOR_HP_BAR      = ( 60, 220,  80)   # Player HP
COLOR_HP_GHOST    = (200,  80,  40)   # Ghost HP (damage taken)
COLOR_XP_BAR      = (  0, 190, 255)   # Experience bar
COLOR_STAMINA_BAR = (255, 180,  30)   # Stamina resource
COLOR_ENERGY_BAR  = (120, 100, 255)   # Magic energy resource

# ============================================================
# TYPOGRAPHY
# ============================================================

FONT_SIZE = {
    "TITLE":    28,   # Main screen header — Agency FB bold
    "SUBTITLE": 16,   # Sub-header / section label
    "BODY":     12,   # Standard interface text
    "CAPTION":  10,   # Labels, stat names
    "HINT":      8,   # Hints, tooltips, watermarks
}

def get_font(size, is_bold=True, is_header=False):
    """Returns a cached system font for the given size."""
    font_name = "Agency FB" if is_header else "Bahnschrift"
    return pygame.font.SysFont(font_name, size, is_bold)

def font_title():
    return get_font(FONT_SIZE["TITLE"], is_bold=True, is_header=True)

def font_subtitle():
    return get_font(FONT_SIZE["SUBTITLE"], is_bold=True, is_header=True)

def font_body(bold=True):
    return get_font(FONT_SIZE["BODY"], is_bold=bold)

def font_caption(bold=False):
    return get_font(FONT_SIZE["CAPTION"], is_bold=bold)

def font_hint():
    return get_font(FONT_SIZE["HINT"], is_bold=False)

# ============================================================
# LAYOUT CONSTANTS
# ============================================================

PADDING       = 10
BORDER_WIDTH  = 2
HEADER_HEIGHT = 52   # Height of top header bar
CONTENT_TOP   = 58   # Y start of page content (below header)
NAV_HEIGHT    = 28   # Height of navigation bar
PANEL_RADIUS  = 3    # Border radius for panels / buttons

# ============================================================
# ASSET PATHS
# ============================================================

ASSET_PATHS = {
    "sfx": {
        "hover": resource_path("assets/sounds/sfx/hover.wav"),
        "click": resource_path("assets/sounds/sfx/click.wav"),
        "stat":  resource_path("assets/sounds/sfx/cash.wav")
    },
    "music": {
        "login":  resource_path("assets/sounds/general/War Brawl Arena - Login.mp3"),
        "hub":    resource_path("assets/sounds/general/Calmnessy - Hub.mp3"),
        "gym":    resource_path("assets/sounds/general/Venisius - Training.mp3"),
        "hosp":   resource_path("assets/sounds/general/loneliness - Hospital.mp3"),
        "lab":    resource_path("assets/sounds/general/Sombrio - Shop.mp3"),
        "battle": resource_path("assets/sounds/general/Stronger - Battle.mp3")
    },
    "images": {
        "presenter": resource_path("assets/images/others/Presentador.png")
    }
}

# ============================================================
# DRAWING HELPERS
# ============================================================

def draw_text_outline(surface, text, font, color, pos, outline_color=COLOR_BLACK, outline_width=1):
    """Draws text with an outline for improved readability."""
    text_surf    = font.render(text, True, color)
    outline_surf = font.render(text, True, outline_color)
    x, y = pos
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx != 0 or dy != 0:
                surface.blit(outline_surf, (x + dx, y + dy))
    surface.blit(text_surf, (x, y))

def draw_segmented_bar(surface, rect, percent, color, segments=10, ghost_percent=None):
    """
    Draws a premium segmented health/resource bar.
    Optionally renders a ghost segment showing recent damage.
    """
    # Background
    pygame.draw.rect(surface, (30, 30, 40), rect)
    pygame.draw.rect(surface, COLOR_BORDER, rect, 1)

    if percent <= 0 and (ghost_percent is None or ghost_percent <= 0):
        return

    total_w   = rect.width
    seg_w     = max(1, (total_w // segments) - 2)
    gap       = 2

    # Ghost HP (behind real HP)
    if ghost_percent is not None and ghost_percent > percent:
        ghost_segs = int(segments * ghost_percent)
        for i in range(ghost_segs):
            seg_rect = pygame.Rect(
                rect.x + 1 + i * (seg_w + gap),
                rect.y + 1,
                seg_w,
                rect.height - 2
            )
            pygame.draw.rect(surface, COLOR_HP_GHOST, seg_rect)

    # Real HP
    if percent > 0:
        filled = int(segments * percent)
        for i in range(filled):
            seg_rect = pygame.Rect(
                rect.x + 1 + i * (seg_w + gap),
                rect.y + 1,
                seg_w,
                rect.height - 2
            )
            pygame.draw.rect(surface, color, seg_rect)
            # Top highlight line
            pygame.draw.line(surface, (min(color[0]+60,255), min(color[1]+60,255), min(color[2]+60,255)),
                             seg_rect.topleft, (seg_rect.right-1, seg_rect.top), 1)

def draw_panel(surface, rect, bg_color=None, border_color=None, radius=PANEL_RADIUS):
    """Draws a styled panel with background and border."""
    bg  = bg_color     if bg_color     else COLOR_PANEL_BG
    brd = border_color if border_color else COLOR_BORDER
    pygame.draw.rect(surface, bg, rect, border_radius=radius)
    pygame.draw.rect(surface, brd, rect, BORDER_WIDTH, border_radius=radius)

def draw_glow_border(surface, rect, color, intensity=1.0, radius=PANEL_RADIUS):
    """
    Draws a luminous glowing border around a rect.
    intensity: 0.0–1.0, controls alpha of glow layers.
    """
    alpha = int(120 * intensity)
    # Outer glow — 2px expanded
    outer = rect.inflate(4, 4)
    glow_surf = pygame.Surface((outer.width, outer.height), pygame.SRCALPHA)
    r, g, b = color
    pygame.draw.rect(glow_surf, (r, g, b, alpha // 2), glow_surf.get_rect(), border_radius=radius + 2)
    surface.blit(glow_surf, outer.topleft)
    # Main border
    pygame.draw.rect(surface, color, rect, 2, border_radius=radius)

def draw_header(surface, title_text, subtitle_text=None,
                title_color=None, subtitle_color=None,
                border_color=None):
    """
    Draws a consistent page header bar at the top of the screen.
    All screens should use this for visual coherence.
    """
    tc  = title_color    if title_color    else COLOR_PRIMARY
    sc  = subtitle_color if subtitle_color else COLOR_MUTED
    bc  = border_color   if border_color   else COLOR_PRIMARY

    # Header background
    pygame.draw.rect(surface, COLOR_HEADER_BG, (0, 0, BASE_WIDTH, HEADER_HEIGHT))
    # Bottom accent line
    pygame.draw.line(surface, bc, (0, HEADER_HEIGHT), (BASE_WIDTH, HEADER_HEIGHT), 2)
    # Subtle top line
    pygame.draw.line(surface, COLOR_BORDER, (0, 0), (BASE_WIDTH, 0), 1)

    # Title
    title_surf = font_subtitle().render(title_text.upper(), True, tc)
    ty = (HEADER_HEIGHT // 2) - (title_surf.get_height() // 2)
    if subtitle_text:
        ty -= 7
    surface.blit(title_surf, (BASE_WIDTH // 2 - title_surf.get_width() // 2, ty))

    # Subtitle
    if subtitle_text:
        sub_surf = font_hint().render(subtitle_text.upper(), True, sc)
        sy = ty + title_surf.get_height() + 2
        surface.blit(sub_surf, (BASE_WIDTH // 2 - sub_surf.get_width() // 2, sy))

def draw_scanlines(surface, alpha=18, spacing=4):
    """Draws subtle scanline effect over the screen for retro feel."""
    line_surf = pygame.Surface((BASE_WIDTH, 1), pygame.SRCALPHA)
    line_surf.fill((0, 0, 0, alpha))
    for y in range(0, BASE_HEIGHT, spacing):
        surface.blit(line_surf, (0, y))

def draw_vignette(surface, strength=80):
    """Draws a soft vignette (darkening at edges) for dramatic effect."""
    vig = pygame.Surface((BASE_WIDTH, BASE_HEIGHT), pygame.SRCALPHA)
    cx, cy = BASE_WIDTH // 2, BASE_HEIGHT // 2
    max_r = max(cx, cy) + 20
    for r in range(max_r, 0, -8):
        alpha = max(0, int(strength * (1 - r / max_r)))
        pygame.draw.circle(vig, (0, 0, 0, alpha), (cx, cy), r)
    surface.blit(vig, (0, 0))

def draw_separator(surface, y, color=None, width=BASE_WIDTH, x=0):
    """Draws a horizontal separator line."""
    c = color if color else COLOR_BORDER
    pygame.draw.line(surface, c, (x, y), (x + width, y), 1)

def draw_corner_brackets(surface, rect, color, size=6):
    """Draws stylish corner brackets around a rect (no full border)."""
    x, y, w, h = rect.x, rect.y, rect.width, rect.height
    s = size
    lines = [
        # Top-left
        ((x, y), (x+s, y)), ((x, y), (x, y+s)),
        # Top-right
        ((x+w, y), (x+w-s, y)), ((x+w, y), (x+w, y+s)),
        # Bottom-left
        ((x, y+h), (x+s, y+h)), ((x, y+h), (x, y+h-s)),
        # Bottom-right
        ((x+w, y+h), (x+w-s, y+h)), ((x+w, y+h), (x+w, y+h-s)),
    ]
    for start, end in lines:
        pygame.draw.line(surface, color, start, end, 2)

def draw_stat_bar(surface, rect, percent, color, label=None, show_percent=False):
    """
    Draws a clean stat/progress bar with optional label and percentage.
    Used for stats in profile, gym, hospital, etc.
    """
    # Background track
    pygame.draw.rect(surface, (25, 25, 38), rect)
    pygame.draw.rect(surface, COLOR_BORDER, rect, 1)

    if percent > 0:
        fill_w = max(2, int(rect.width * min(1.0, percent)))
        fill_rect = pygame.Rect(rect.left, rect.top, fill_w, rect.height)
        pygame.draw.rect(surface, color, fill_rect)
        # Highlight stripe at top
        pygame.draw.line(surface,
                         (min(color[0]+80,255), min(color[1]+80,255), min(color[2]+80,255)),
                         fill_rect.topleft, (fill_rect.right-1, fill_rect.top), 1)

    # Label overlay
    if label:
        lbl = font_hint().render(label, True, COLOR_WHITE)
        surface.blit(lbl, (rect.x + 2, rect.y + rect.height // 2 - lbl.get_height() // 2))
    if show_percent:
        pct_txt = font_hint().render(f"{int(percent*100)}%", True, COLOR_WHITE)
        surface.blit(pct_txt, (rect.right - pct_txt.get_width() - 2,
                                rect.y + rect.height // 2 - pct_txt.get_height() // 2))

def lerp_color(c1, c2, t):
    """Linear interpolation between two colors. t: 0.0–1.0."""
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

def pulse_alpha(t, speed=2.0, min_a=100, max_a=255):
    """Returns a pulsing alpha value based on time t."""
    return int(min_a + (max_a - min_a) * (0.5 + 0.5 * math.sin(t * speed * math.pi)))

def draw_tag(surface, text, pos, color, bg_color=None):
    """Draws a small colored tag/badge (e.g. [F], [M], [LV5])."""
    font = font_hint()
    surf = font.render(text, True, color)
    bg   = bg_color if bg_color else (int(color[0]*0.3), int(color[1]*0.3), int(color[2]*0.3))
    pad  = 2
    tag_rect = pygame.Rect(pos[0]-pad, pos[1]-pad, surf.get_width()+pad*2, surf.get_height()+pad*2)
    pygame.draw.rect(surface, bg, tag_rect, border_radius=2)
    pygame.draw.rect(surface, color, tag_rect, 1, border_radius=2)
    surface.blit(surf, pos)
    return tag_rect.width
