"""
Shared colour palette and layout constants for the DSL Tree Visualizer.
Deep navy/slate dark theme — WCAG 2.1 AA compliant contrast ratios noted.
"""

# ==========================================
# Colour Palette — Deep Navy / Slate
# ==========================================
COLOURS = {
    # Backgrounds (deep → surface → card)
    "bg_dark":       "#0D1117",   # Deepest — editor, canvas
    "bg_medium":     "#0D1117",   # Canvas background
    "bg_surface":    "#161B22",   # Elevated surface — left panel
    "bg_panel":      "#161B22",   # Control panel background
    "bg_card":       "#21262D",   # Card containers (elevated)
    "bg_gutter":     "#0D1117",   # Line-number gutter

    # Foregrounds
    "fg_text":       "#E6EDF3",   # Primary text       (vs #0D1117 → 15.4:1)
    "fg_gutter":     "#7D8590",   # Gutter numbers     (vs #0D1117 →  4.7:1)
    "fg_placeholder":"#6A9955",   # Placeholder hint

    # Interactive — Primary (Run / execute actions)
    "btn_primary":      "#2EA043",   # Green primary button
    "btn_primary_hover":"#3FB950",   # Green hover
    "btn_primary_active":"#238636",  # Green press

    # Interactive — Secondary (Insert / Step / default)
    "btn_bg":        "#2188FF",   # Blue button
    "btn_fg":        "#FFFFFF",
    "btn_hover":     "#58A6FF",   # Blue hover
    "btn_active":    "#1A7CF4",   # Blue press

    # Interactive — Danger (Clear / Delete)
    "btn_danger":       "#DA3633",   # Red danger button
    "btn_danger_hover": "#F85149",   # Red hover
    "btn_danger_active":"#B62324",   # Red press

    # Interactive — Neutral (Reset / Step Back)
    "btn_neutral":       "#30363D",  # Slate neutral button
    "btn_neutral_hover": "#484F58",  # Slate hover
    "btn_neutral_active":"#21262D",  # Slate press

    # Accent / focus
    "focus_ring":    "#58A6FF",   # Focus indicator (brighter blue)
    "status_bg":     "#1F6FEB",   # Status bar bg
    "status_fg":     "#FFFFFF",

    # Borders & separators
    "border":        "#30363D",
    "separator":     "#30363D",   # Section dividers
    "entry_bg":      "#010409",   # Deepest entry for contrast
    "entry_fg":      "#E6EDF3",

    # Canvas — nodes
    "node_fill":        "#1F6FEB",   # Node circle fill
    "node_inner":       "#388BFD",   # Lighter inner for gradient effect
    "node_outline":     "#58A6FF",   # Node outline accent
    "node_shadow":      "#010409",   # Shadow behind node
    "node_glow":        "#1F6FEB",   # Glow circle colour
    "node_text":        "#FFFFFF",   # Node label colour
    "edge_colour":      "#8B949E",   # Softer edge lines

    # Canvas — background grid
    "grid_dot":         "#21262D",   # Dot-grid colour (matches card tone)

    # Canvas — deletion highlight
    "node_delete_highlight": "#F85149",  # Red flash for node being deleted

    # Canvas — Red-Black node colours
    "node_red_fill":    "#8B0000",
    "node_red_outline": "#F85149",

    # Section header accent
    "header_accent":    "#58A6FF",   # Accent for section titles
}

# ==========================================
# Layout / animation constants
# ==========================================
NODE_RADIUS       = 24        # radius of each drawn circle
Y_START           = 50        # top margin before root node
Y_SPACING         = 80        # vertical gap between depth levels
ANIM_FRAMES       = 15        # number of interpolation frames
ANIM_DELAY_MS     = 20        # milliseconds between frames
HIGHLIGHT_DURATION_MS = 400   # how long the deletion highlight flash lasts
CARD_CORNER_RADIUS = 12       # rounded corners for card containers
SECTION_PAD_X     = 12        # horizontal padding inside sections
SECTION_PAD_Y     = 8         # vertical padding inside sections

# ==========================================
# Fonts
# ==========================================
FONT_FAMILY       = "Inter"           # Modern UI font (falls back gracefully)
FONT_MONO         = "Cascadia Code"   # Modern monospace (ships with Win Terminal / VS Code)

FONT_HEADER       = (FONT_FAMILY, 18, "bold")    # Section headers, editor title
FONT_BODY         = (FONT_FAMILY, 15)             # Labels, status bar
FONT_BUTTON       = (FONT_FAMILY, 15)             # Button text
FONT_BUTTON_BOLD  = (FONT_FAMILY, 15, "bold")     # Primary buttons
FONT_EDITOR       = (FONT_MONO, 11)               # Code editor
FONT_GUTTER       = (FONT_MONO, 11)               # Line numbers
FONT_NODE         = (FONT_FAMILY, 16, "bold")      # Node labels on canvas
FONT_TOOLTIP      = (FONT_FAMILY, 12)              # Tooltip text
