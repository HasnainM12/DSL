# Red-Black Insertion Fix-Up (simplified — insertion-only)
#
# NOTE: Full Red-Black fix-up (including deletion) would require
# a loop construct, which is explicitly out of scope for this DSL.
# This script approximates insertion rebalancing only.

# Case 1: Uncle is RED — recolour
IF node_colour == "RED" AND parent_colour == "RED" AND uncle_colour == "RED" THEN {
    SET_COLOUR "BLACK"
}

# Case 2: Uncle is BLACK — rotations
IF balance_factor > 1 AND left_child_balance < 0 THEN ROTATE_LEFT_RIGHT
IF balance_factor < -1 AND right_child_balance > 0 THEN ROTATE_RIGHT_LEFT
IF balance_factor > 1 THEN ROTATE_RIGHT
IF balance_factor < -1 THEN ROTATE_LEFT
