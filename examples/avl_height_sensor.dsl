# avl_height_sensor.dsl
#
# SHOWCASE: The 'height' sensor as a routing discriminator
#           + underused comparison operators: >=, <=, !=
#           + arithmetic expressions on sensor values
#
# Operators demonstrated:
#   >=  balance_factor >= 2  (correct AVL imbalance threshold — left-heavy)
#   <=  balance_factor <= -2  (right-heavy) and left_child_balance <= -1 (zig-zag)
#   !=  height != 1  (leaf guard)
#   arithmetic: height - 1 >= 2  (equivalent to height >= 3)
#
# Important: AVL allows balance_factor of -1, 0, or +1.
# A rotation is ONLY needed when |balance_factor| >= 2.
# A node requiring rotation always has height >= 3 (needs at least two levels
# of children on one side), so height - 1 >= 2 is a natural height-based gate.
#
# Rule ordering: double-rotation cases first (LR/RL), then single (LL/RR).

# -----------------------------------------------------------------------
# Rule 1 — Left-Right case (zig-zag: left-heavy but left child is right-heavy)
# height != 1 is a leaf guard — at height 1, balance_factor is always 0 so
# this rule could never fire there anyway. Written explicitly to showcase !=.
# Demonstrates: !=, >=, <=, three-sensor AND chain.
# -----------------------------------------------------------------------
IF height != 1 AND balance_factor >= 2 AND left_child_balance <= -1 THEN ROTATE_LEFT_RIGHT

# -----------------------------------------------------------------------
# Rule 2 — Right-Left case (zig-zag: right-heavy but right child is left-heavy)
# Symmetric to Rule 1.
# Demonstrates: <=, >=, !=, three-sensor AND chain.
# -----------------------------------------------------------------------
IF height != 1 AND balance_factor <= -2 AND right_child_balance >= 1 THEN ROTATE_RIGHT_LEFT

# -----------------------------------------------------------------------
# Rule 3 — Left-Left case (straight left spine)
# height - 1 >= 2 is equivalent to height >= 3, written as arithmetic to
# demonstrate the height sensor in an expression.
# The double-rotation rules above have already handled any zig-zag cases,
# so reaching here means the left subtree is also left-heavy.
# Demonstrates: height arithmetic, >= operator.
# -----------------------------------------------------------------------
IF height - 1 >= 2 AND balance_factor >= 2 THEN ROTATE_RIGHT

# -----------------------------------------------------------------------
# Rule 4 — Right-Right case (straight right spine)
# Symmetric to Rule 3.
# Demonstrates: height arithmetic, <= operator.
# -----------------------------------------------------------------------
IF height - 1 >= 2 AND balance_factor <= -2 THEN ROTATE_LEFT
