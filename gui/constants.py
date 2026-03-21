"""
Shared colour palette and layout constants for the DSL Tree Visualizer.
Deep navy/slate dark theme — WCAG 2.1 AA compliant contrast ratios noted.
"""

# ==========================================
# Colour Palette — Deep Navy / Slate
# ==========================================
COLOURS = {
    # Backgrounds (deep → surface → card)
    "bg_dark":       "#020617",   # Sleek Slate 950 (Extremely dark)
    "bg_medium":     "#020617",   # Canvas background
    "bg_surface":    "#0f172a",   # Elevated surface — left panel (Slate 900)
    "bg_panel":      "#0f172a",   # Control panel background
    "bg_card":       "#1e293b",   # Card containers (elevated - Slate 800)
    "bg_gutter":     "#020617",   # Line-number gutter

    # Foregrounds
    "fg_text":       "#f8fafc",   # Primary text (Slate 50)
    "fg_gutter":     "#64748b",   # Gutter numbers (Slate 500)
    "fg_placeholder":"#94a3b8",   # Placeholder hint (Slate 400)

    # Interactive — Primary (Run / execute actions)
    "btn_primary":      "#10b981",   # Modern Emerald 500
    "btn_primary_hover":"#34d399",   # Emerald 400
    "btn_primary_active":"#059669",  # Emerald 600

    # Interactive — Secondary (Insert / Step / default)
    "btn_bg":        "#3b82f6",   # Vibrant Blue 500
    "btn_fg":        "#ffffff",
    "btn_hover":     "#60a5fa",   # Blue 400
    "btn_active":    "#2563eb",   # Blue 600

    # Interactive — Danger (Clear / Delete)
    "btn_danger":       "#f43f5e",   # Rose 500 (Vibrant Danger)
    "btn_danger_hover": "#fb7185",   # Rose 400
    "btn_danger_active":"#e11d48",   # Rose 600

    # Interactive — Neutral (Reset / Step Back)
    "btn_neutral":       "#475569",  # Slate 600
    "btn_neutral_hover": "#64748b",  # Slate 500
    "btn_neutral_active":"#334155",  # Slate 700

    # Accent / focus
    "focus_ring":    "#38bdf8",   # Sky 400 (glow)
    "status_bg":     "#2563eb",   # Blue 600
    "status_fg":     "#ffffff",

    # Borders & separators
    "border":        "#0f172a",   # Slate 900
    "separator":     "#1e293b",   # Slate 800
    "entry_bg":      "#000000",   # Deepest input bg (True Black)
    "entry_fg":      "#f8fafc",

    # Canvas — nodes
    "node_fill":        "#1e293b",   # Sleek Slate 800 for default/black nodes
    "node_inner":       "#334155",   # Lighter inner
    "node_outline":     "#64748b",   # Slate 500 outline
    "node_shadow":      "#020617",   # Deep shadow
    "node_glow":        "#94a3b8",   # Soft white/slate glow
    "node_text":        "#f8fafc",   # Crisp white text
    "edge_colour":      "#475569",   # Slate 600 for thick edges

    # Canvas — background grid
    "grid_dot":         "#1e293b",   # Slate 800

    # Canvas — deletion highlight
    "node_delete_highlight": "#f43f5e",  # Rose 500

    # Canvas — Red-Black node colours
    "node_red_fill":    "#e11d48",   # Rose 600 (vibrant modern red)
    "node_red_outline": "#fb7185",   # Rose 400
    "node_red_glow":    "#f43f5e",   # Rose 500 glow

    # Section header accent
    "header_accent":    "#38bdf8",   # Sky 400
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
CARD_CORNER_RADIUS = 16       # fuller rounded corners for modern card containers
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
