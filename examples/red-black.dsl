# Red-Black Insertion Fix-Up
#
# Implements the three canonical cases of Red-Black insertion
# rebalancing using the extended DSL colour actions.
#
# Invariants maintained:
#   1. Every node is RED or BLACK
#   2. Root is BLACK (enforced externally after each insert)
#   3. No two consecutive RED nodes (parent-child)
#   4. Equal black-height on all root-to-leaf paths

# -------------------------------------------------------
# Case 1: Uncle is RED — recolour and propagate upward
# -------------------------------------------------------
IF node_colour == "RED" AND parent_colour == "RED" AND uncle_colour == "RED" THEN {
    SET_PARENT_COLOUR "BLACK"
    SET_UNCLE_COLOUR "BLACK"
    SET_GRANDPARENT_COLOUR "RED"
}

# -------------------------------------------------------
# Case 2: Uncle is BLACK, inner child — double rotation
# -------------------------------------------------------
# Left-Right case (parent is left child, node is right child)
IF node_colour == "RED" AND parent_colour == "RED" AND uncle_colour == "BLACK" AND balance_factor > 1 AND left_child_balance < 0 THEN ROTATE_LEFT_RIGHT

# Right-Left case (parent is right child, node is left child)
IF node_colour == "RED" AND parent_colour == "RED" AND uncle_colour == "BLACK" AND balance_factor < -1 AND right_child_balance > 0 THEN ROTATE_RIGHT_LEFT

# -------------------------------------------------------
# Case 3: Uncle is BLACK, outer child — single rotation
# -------------------------------------------------------
# Left-Left case
IF node_colour == "RED" AND parent_colour == "RED" AND uncle_colour == "BLACK" AND balance_factor > 1 THEN ROTATE_RIGHT

# Right-Right case
IF node_colour == "RED" AND parent_colour == "RED" AND uncle_colour == "BLACK" AND balance_factor < -1 THEN ROTATE_LEFT
