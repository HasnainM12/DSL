"""
Shared colour palette and layout constants for the DSL Tree Visualizer.
Beige & Brown Light Theme (inspired by modern reference image).
"""

COLOURS = {
    # Main App Backgrounds
    "bg_dark":       "#FDF7EC",  # Primary Background
    "bg_medium":     "#FDF7EC",
    "bg_surface":    "#FDF7EC",  # Same as main so cards float above it
    "bg_panel":      "rgba(252, 250, 245, 0.85)",  # Floating Card background
    "bg_card":       "#EBE0D3",  # Highlight/Selection cards in editor
    "bg_gutter":     "#FDF7EC",  # Editor line numbers gutter
    
    # Text
    "fg_text":       "#4A3C31",  # Deep brown for high contrast main text
    "fg_gutter":     "#A39E95",  # Faint taupe for line numbers
    "fg_placeholder":"#A3968A",
    
    # Primary Buttons (Brown/Charcoal)
    "btn_primary":      "#1A202C", # Rich Charcoal
    "btn_primary_hover":"#2D3748",
    "btn_primary_active":"#4A5568",
    "btn_primary_fg":   "#FDF7EC",
    
    # Standard Action Buttons (Medium warm brown/Taupe)
    "btn_bg":        "#DDCBB7", # Warm Taupe
    "btn_fg":        "#1A202C", # Charcoal text on taupe
    "btn_hover":     "#C3B2A0",
    "btn_active":    "#A89988",
    
    # Danger Buttons (Terracotta)
    "btn_danger":       "#C53030",
    "btn_danger_hover": "#E53E3E",
    "btn_danger_active":"#9B2C2C",
    "btn_danger_fg":    "#FDF7EC",
    
    # Neutral Buttons
    "btn_neutral":       "#E8E2D6",
    "btn_neutral_hover": "#D8D2C6",
    "btn_neutral_active":"#C8C2B6",
    
    # Accents & Borders
    "focus_ring":    "#DDCBB7",
    "status_bg":     "#1A202C",
    "status_fg":     "#FFFFFF",
    "border":        "#DDCBB7",
    "separator":     "#DDCBB7",
    "shadow":        "rgba(82, 64, 50, 0.12)",  # Warm Umber
    
    # Editor Inputs
    "entry_bg":      "#FFFFFF",
    "entry_fg":      "#4A3C31",
    
    # Tree Canvas Visuals (algorithm states)
    # Black nodes in Red-Black tree algorithms:
    "node_fill":        "#1A202C",   # Rich Charcoal
    "node_outline":     "#1A202C",
    "node_text":        "#FFFFFF",
    "edge_colour":      "#4A5568",   # Matte Graphite
    "grid_dot":         "#E5D8CA",
    
    # Red nodes in Red-Black tree algorithms:
    "node_delete_highlight": "#FF9999",
    "node_red_fill":    "#9B2C2C",   # Darker Terracotta
    "node_red_outline": "#9B2C2C",
    "header_accent":    "#4A3C31",
    
    # AVL Specific
    "node_avl_fill":    "#4A3C31",   # Deep Brown
    "avl_hud_bg":       "#DDCBB7",   # Warm Taupe
    "avl_hud_fg":       "#1A202C",   # Charcoal
    "avl_highlight":    "#C3B2A0",   # Active Highlight
}

NODE_RADIUS           = 24
Y_START               = 100
Y_SPACING             = 80
ANIM_FRAMES           = 15
ANIM_DELAY_MS         = 20
HIGHLIGHT_DURATION_MS = 400

MODE_AVL = "AVL"
MODE_RB  = "Red-Black"

TEMPLATES = {
    MODE_AVL: """# AVL Balancing Rules
# Order matters — double rotations must come before single rotations

IF balance_factor > 1 AND left_child_balance < 0 THEN ROTATE_LEFT_RIGHT
IF balance_factor < -1 AND right_child_balance > 0 THEN ROTATE_RIGHT_LEFT
IF balance_factor > 1 THEN ROTATE_RIGHT
IF balance_factor < -1 THEN ROTATE_LEFT
""",
    MODE_RB: """# Red-Black Insertion Fix-Up

# Case 1: Uncle is RED — recolour and propagate upward
IF node_colour == "RED" AND parent_colour == "RED" AND uncle_colour == "RED" THEN {
    SET_PARENT_COLOUR "BLACK"
    SET_UNCLE_COLOUR "BLACK"
    SET_GRANDPARENT_COLOUR "RED"
}

# Case 2a + 3a: Parent is LEFT child, node is RIGHT child
IF node_colour == "RED" AND parent_colour == "RED" AND uncle_colour == "BLACK" AND parent_is_left_child == 1 AND is_left_child == 0 THEN {
    SET_COLOUR "BLACK"
    SET_GRANDPARENT_COLOUR "RED"
    ROTATE_LEFT_AT_PARENT
    ROTATE_RIGHT_AT_GRANDPARENT
}

# Case 3a: Parent is LEFT child, node is LEFT child
IF node_colour == "RED" AND parent_colour == "RED" AND uncle_colour == "BLACK" AND parent_is_left_child == 1 AND is_left_child == 1 THEN {
    SET_PARENT_COLOUR "BLACK"
    SET_GRANDPARENT_COLOUR "RED"
    ROTATE_RIGHT_AT_GRANDPARENT
}

# Case 2b + 3b: Parent is RIGHT child, node is LEFT child
IF node_colour == "RED" AND parent_colour == "RED" AND uncle_colour == "BLACK" AND parent_is_left_child == 0 AND is_left_child == 1 THEN {
    SET_COLOUR "BLACK"
    SET_GRANDPARENT_COLOUR "RED"
    ROTATE_RIGHT_AT_PARENT
    ROTATE_LEFT_AT_GRANDPARENT
}

# Case 3b: Parent is RIGHT child, node is RIGHT child
IF node_colour == "RED" AND parent_colour == "RED" AND uncle_colour == "BLACK" AND parent_is_left_child == 0 AND is_left_child == 0 THEN {
    SET_PARENT_COLOUR "BLACK"
    SET_GRANDPARENT_COLOUR "RED"
    ROTATE_LEFT_AT_GRANDPARENT
}
"""
}
