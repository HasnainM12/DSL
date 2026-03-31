# Advanced AVL Balancing Logic
#
# Demonstrates the grammar's capability to handle arithmetic,
# compound boolean logic (AND, OR, NOT), parenthesis precedence,
# and multi-action blocks applied to AVL properties.

# 1. Arithmetic and Compound Logic
# We can evaluate mathematical expressions before comparing them.
# In a "relaxed" variation of an AVL tree, we might tolerate slightly
# heavier balance thresholds before triggering a rotation.
IF (balance_factor + right_child_balance > 2) AND NOT (is_left_child == 1 OR parent_is_left_child == 1) THEN {
    ROTATE_LEFT_AT_PARENT
    ROTATE_LEFT_AT_GRANDPARENT
    DONE
}

# 2. Mathematical Equality and Negative Comparisons
# Checking strict subtree height offsets.
IF balance_factor <= -2 AND (left_child_balance - right_child_balance == 0) THEN {
    ROTATE_RIGHT
    PROPAGATE
}

 # Rule 3 demo: height-capped LR rotation
  IF NOT (height > 5) AND (balance_factor > 1 OR left_child_balance < 0) THEN {
      ROTATE_LEFT_RIGHT
  }

  INSERT 50
  INSERT 30
  INSERT 40