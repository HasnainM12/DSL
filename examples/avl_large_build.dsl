# avl_large_build.dsl
#
# SHOWCASE: Large INSERT/DELETE sequences as first-class DSL commands
#
# This file demonstrates:
#   - 15 INSERT commands that intentionally exercise all four AVL rotation cases
#   - 5 DELETE commands that re-trigger rebalancing on an already-balanced tree
#   - Comments labelling WHICH rotation case each step provokes
#   - The canonical four AVL rules embedded as the rebalancing engine
#
# The four AVL rotation cases:
#   LL  left-left   : balance_factor > 1,  left child NOT right-heavy  -> ROTATE_RIGHT
#   RR  right-right : balance_factor < -1, right child NOT left-heavy  -> ROTATE_LEFT
#   LR  left-right  : balance_factor > 1,  left child IS  right-heavy  -> ROTATE_LEFT_RIGHT
#   RL  right-left  : balance_factor < -1, right child IS  left-heavy  -> ROTATE_RIGHT_LEFT

# --- Rebalancing engine (rules evaluated after every INSERT / DELETE) ---
# Double-rotation cases must be listed before single-rotation cases.
IF balance_factor > 1 AND left_child_balance < 0 THEN ROTATE_LEFT_RIGHT
IF balance_factor < -1 AND right_child_balance > 0 THEN ROTATE_RIGHT_LEFT
IF balance_factor > 1 THEN ROTATE_RIGHT
IF balance_factor < -1 THEN ROTATE_LEFT

# =======================================================================
# PHASE 1 — Build the backbone; provoke LL and RR cases
# =======================================================================

# Root + two children — perfectly balanced, no rotation fires.
INSERT 50
INSERT 30
INSERT 70

# Inserting 20 then 10 grows a left spine: 50 -> 30 -> 20 -> 10
# balance_factor at node 30 becomes 2, left_child_balance >= 0
# -> LL case -> ROTATE_RIGHT fires at node 30
INSERT 20
INSERT 10

# Inserting 80 then 90 grows a right spine: 70 -> 80 -> 90
# balance_factor at node 70 becomes -2, right_child_balance <= 0
# -> RR case -> ROTATE_LEFT fires at node 70
INSERT 80
INSERT 90

# =======================================================================
# PHASE 2 — Provoke LR and RL cases
# =======================================================================

# 25 is inserted as the right child of 20.
# Segment: 30 -> 20 -> (nil, 25)
# balance_factor at node 30 > 1, left_child_balance of 20 < 0
# -> LR case -> ROTATE_LEFT_RIGHT fires at node 30
INSERT 25

# 75 is inserted as the left child of 80.
# Segment: 70 -> 80 -> (75, nil)
# balance_factor at node 70 < -1, right_child_balance of 80 > 0
# -> RL case -> ROTATE_RIGHT_LEFT fires at node 70
INSERT 75

# =======================================================================
# PHASE 3 — Fill out the tree to depth 4 (no new violations expected)
# =======================================================================

INSERT 5
INSERT 15
INSERT 35
INSERT 60
INSERT 85
INSERT 95

# =======================================================================
# PHASE 4 — Targeted deletions that re-trigger rebalancing
# =======================================================================

# Remove far-left leaf; may expose LL imbalance in left subtree.
DELETE 5

# Remove far-right leaf; symmetric to the deletion of 5.
DELETE 95

# Remove the original root (50); its in-order successor (60) takes its place.
# The replacement may create a right-heavy imbalance at the new root.
# -> RR case -> ROTATE_LEFT may fire
DELETE 50

# Further pruning to leave a lean, balanced final tree.
DELETE 10
DELETE 90
