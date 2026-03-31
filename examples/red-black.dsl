# Red-Black Insertion Fix-Up
#
# Implements the three canonical cases of Red-Black insertion
# rebalancing using structural position sensors and relative-level
# rotation actions.
#
# Sensors used:
#   is_left_child        — 1 if current node is parent's left child, else 0
#   parent_is_left_child — 1 if parent is grandparent's left child, else 0
#
# Invariants maintained:
#   1. Every node is RED or BLACK
#   2. Root is BLACK (enforced externally after each insert)
#   3. No two consecutive RED nodes (parent-child)
#   4. Equal black-height on all root-to-leaf paths

# -------------------------------------------------------
# Case 1: Uncle is RED — recolour and propagate upward
# -------------------------------------------------------
# Post-order traversal naturally propagates this upward: after grandparent
# is made RED, it will be evaluated later in the traversal and the rules
# will fire again if its parent is also RED.
IF node_colour == "RED" AND parent_colour == "RED" AND uncle_colour == "RED" THEN {
    SET_PARENT_COLOUR "BLACK"
    SET_UNCLE_COLOUR "BLACK"
    SET_GRANDPARENT_COLOUR "RED"
}

# -------------------------------------------------------
# Case 2a + 3a: Parent is LEFT child, node is RIGHT child
# -------------------------------------------------------
# LR zig-zag: rotate left at parent (straightens to LL), then rotate
# right at grandparent. Node becomes the new subtree root (BLACK).
IF node_colour == "RED" AND parent_colour == "RED" AND uncle_colour == "BLACK" AND parent_is_left_child == 1 AND is_left_child == 0 THEN {
    SET_COLOUR "BLACK"
    SET_GRANDPARENT_COLOUR "RED"
    ROTATE_LEFT_AT_PARENT
    ROTATE_RIGHT_AT_GRANDPARENT
}

# -------------------------------------------------------
# Case 3a: Parent is LEFT child, node is LEFT child
# -------------------------------------------------------
# LL straight: rotate right at grandparent. Parent becomes new root (BLACK).
IF node_colour == "RED" AND parent_colour == "RED" AND uncle_colour == "BLACK" AND parent_is_left_child == 1 AND is_left_child == 1 THEN {
    SET_PARENT_COLOUR "BLACK"
    SET_GRANDPARENT_COLOUR "RED"
    ROTATE_RIGHT_AT_GRANDPARENT
}

# -------------------------------------------------------
# Case 2b + 3b: Parent is RIGHT child, node is LEFT child
# -------------------------------------------------------
# RL zig-zag: rotate right at parent (straightens to RR), then rotate
# left at grandparent. Node becomes the new subtree root (BLACK).
IF node_colour == "RED" AND parent_colour == "RED" AND uncle_colour == "BLACK" AND parent_is_left_child == 0 AND is_left_child == 1 THEN {
    SET_COLOUR "BLACK"
    SET_GRANDPARENT_COLOUR "RED"
    ROTATE_RIGHT_AT_PARENT
    ROTATE_LEFT_AT_GRANDPARENT
}

# -------------------------------------------------------
# Case 3b: Parent is RIGHT child, node is RIGHT child
# -------------------------------------------------------
# RR straight: rotate left at grandparent. Parent becomes new root (BLACK).
IF node_colour == "RED" AND parent_colour == "RED" AND uncle_colour == "BLACK" AND parent_is_left_child == 0 AND is_left_child == 0 THEN {
    SET_PARENT_COLOUR "BLACK"
    SET_GRANDPARENT_COLOUR "RED"
    ROTATE_LEFT_AT_GRANDPARENT
}
