# avl_position_routing.dsl
#
# SHOWCASE: Positional sensors as routing conditions
#           + relative rotation actions (_AT_PARENT, _AT_GRANDPARENT)
#           + multi-action blocks for double rotations
#
# This file demonstrates:
#   - is_left_child == 1   : current node is its parent's left child
#   - is_left_child == 0   : current node is its parent's right child  (== 0 pattern)
#   - parent_is_left_child == 1 / == 0   : grandchild position routing
#   - ROTATE_RIGHT_AT_GRANDPARENT  and  ROTATE_LEFT_AT_GRANDPARENT
#   - ROTATE_RIGHT_AT_PARENT       and  ROTATE_LEFT_AT_PARENT
#   - Multi-action { } block for double-rotation sequences
#
# Motivation:
#   Some AVL fix-up implementations evaluate rules AT THE INSERTED NODE
#   rather than at the unbalanced subtree root.  The node's own position
#   in the tree (left/right child, left/right grandchild) determines which
#   ancestor to rotate — this is the "case analysis by position" approach
#   found in many AVL textbooks.
#
# The four positional configurations and their fixes:
#
#   Case LL — inserted node is a left child  AND  its parent is a left child.
#             Grandparent is right-heavy looking upward from this node.
#             Fix: single right rotation AT GRANDPARENT.
#
#   Case RR — inserted node is a right child AND  its parent is a right child.
#             Grandparent is left-heavy looking upward from this node.
#             Fix: single left rotation AT GRANDPARENT.
#
#   Case LR — inserted node is a right child AND  its parent is a left child.
#             The zig-zag shape requires two rotations.
#             Fix: left rotation AT PARENT, then right rotation AT GRANDPARENT.
#
#   Case RL — inserted node is a left child  AND  its parent is a right child.
#             The zig-zag shape (mirror of LR) requires two rotations.
#             Fix: right rotation AT PARENT, then left rotation AT GRANDPARENT.
#
# Rule ordering: single-rotation cases are listed first.  The double-rotation
# cases (LR, RL) are then checked, preventing a single rotation from partially
# fixing a zig-zag imbalance.

# -----------------------------------------------------------------------
# Case LL: left child of a left child -> single right rotation at grandparent
# Demonstrates: is_left_child == 1, parent_is_left_child == 1,
#               ROTATE_RIGHT_AT_GRANDPARENT.
# -----------------------------------------------------------------------
IF is_left_child == 1 AND parent_is_left_child == 1 THEN ROTATE_RIGHT_AT_GRANDPARENT

# -----------------------------------------------------------------------
# Case RR: right child of a right child -> single left rotation at grandparent
# Demonstrates: is_left_child == 0  (the "false" check pattern),
#               parent_is_left_child == 0, ROTATE_LEFT_AT_GRANDPARENT.
# -----------------------------------------------------------------------
IF is_left_child == 0 AND parent_is_left_child == 0 THEN ROTATE_LEFT_AT_GRANDPARENT

# -----------------------------------------------------------------------
# Case LR: right child of a left child -> double rotation (left-at-parent, then right-at-grandparent)
# Demonstrates: mixed == 0 / == 1 on positional sensors,
#               multi-action block { },
#               ROTATE_LEFT_AT_PARENT followed by ROTATE_RIGHT_AT_GRANDPARENT.
# -----------------------------------------------------------------------
IF is_left_child == 0 AND parent_is_left_child == 1 THEN {
    ROTATE_LEFT_AT_PARENT
    ROTATE_RIGHT_AT_GRANDPARENT
}

# -----------------------------------------------------------------------
# Case RL: left child of a right child -> double rotation (right-at-parent, then left-at-grandparent)
# Demonstrates: mixed == 1 / == 0 on positional sensors,
#               multi-action block { },
#               ROTATE_RIGHT_AT_PARENT followed by ROTATE_LEFT_AT_GRANDPARENT.
# -----------------------------------------------------------------------
IF is_left_child == 1 AND parent_is_left_child == 0 THEN {
    ROTATE_RIGHT_AT_PARENT
    ROTATE_LEFT_AT_GRANDPARENT
}
