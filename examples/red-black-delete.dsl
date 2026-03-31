# Red-Black Deletion Fix-Up
#
# Implements the four canonical cases of Red-Black deletion
# rebalancing, each mirrored for left/right child positions.
#
# The fix-up loop in the interpreter applies these rules iteratively
# at the "double-black" node (x) after a BLACK node is removed:
#   - DONE signals that fix-up is complete (Case 4)
#   - PROPAGATE signals to move x up to its parent (Case 2)
#   - Neither signal means the tree was transformed and the same
#     node should be re-evaluated (Cases 1, 3)
#
# Sensors used:
#   is_left_child        — 1 if x is parent's left child
#   sibling_colour       — colour of x's sibling
#   sibling_left_colour  — colour of sibling's left child
#   sibling_right_colour — colour of sibling's right child
#   parent_colour        — colour of x's parent

# =========================================================
# x is LEFT child — sibling is parent.right
# =========================================================

# Case 1 (left): Sibling is RED
# Recolour and rotate to get a BLACK sibling, then re-evaluate.
IF is_left_child == 1 AND sibling_colour == "RED" THEN {
    SET_SIBLING_COLOUR "BLACK"
    SET_PARENT_COLOUR "RED"
    ROTATE_LEFT_AT_PARENT
}

# Case 2 (left): Sibling BLACK, both sibling children BLACK
# Push the extra black up to the parent.
IF is_left_child == 1 AND sibling_colour == "BLACK" AND sibling_left_colour == "BLACK" AND sibling_right_colour == "BLACK" THEN {
    SET_SIBLING_COLOUR "RED"
    PROPAGATE
}

# Case 3 (left): Sibling BLACK, near child (left) RED, far child (right) BLACK
# Rotate sibling to make far child RED, then re-evaluate (falls to Case 4).
IF is_left_child == 1 AND sibling_colour == "BLACK" AND sibling_left_colour == "RED" AND sibling_right_colour == "BLACK" THEN {
    SET_SIBLING_LEFT_COLOUR "BLACK"
    SET_SIBLING_COLOUR "RED"
    ROTATE_RIGHT_AT_SIBLING
}

# Case 4 (left): Sibling BLACK, far child (right) RED
# Terminal case — rotate at parent and recolour to absorb the extra black.
IF is_left_child == 1 AND sibling_colour == "BLACK" AND sibling_right_colour == "RED" THEN {
    SET_SIBLING_COLOUR_FROM_PARENT
    SET_PARENT_COLOUR "BLACK"
    SET_SIBLING_RIGHT_COLOUR "BLACK"
    ROTATE_LEFT_AT_PARENT
    DONE
}

# =========================================================
# x is RIGHT child — sibling is parent.left (mirror cases)
# =========================================================

# Case 1 (right): Sibling is RED
IF is_left_child == 0 AND sibling_colour == "RED" THEN {
    SET_SIBLING_COLOUR "BLACK"
    SET_PARENT_COLOUR "RED"
    ROTATE_RIGHT_AT_PARENT
}

# Case 2 (right): Sibling BLACK, both sibling children BLACK
IF is_left_child == 0 AND sibling_colour == "BLACK" AND sibling_left_colour == "BLACK" AND sibling_right_colour == "BLACK" THEN {
    SET_SIBLING_COLOUR "RED"
    PROPAGATE
}

# Case 3 (right): Sibling BLACK, near child (right) RED, far child (left) BLACK
IF is_left_child == 0 AND sibling_colour == "BLACK" AND sibling_right_colour == "RED" AND sibling_left_colour == "BLACK" THEN {
    SET_SIBLING_RIGHT_COLOUR "BLACK"
    SET_SIBLING_COLOUR "RED"
    ROTATE_LEFT_AT_SIBLING
}

# Case 4 (right): Sibling BLACK, far child (left) RED
IF is_left_child == 0 AND sibling_colour == "BLACK" AND sibling_left_colour == "RED" THEN {
    SET_SIBLING_COLOUR_FROM_PARENT
    SET_PARENT_COLOUR "BLACK"
    SET_SIBLING_LEFT_COLOUR "BLACK"
    ROTATE_RIGHT_AT_PARENT
    DONE
}
