# Automated Test and Integration Script
#
# Showcases the grammar's ability to intermix top-level execution
# commands (INSERT, DELETE) with rule evaluations dynamically.
# Useful for creating integration tests or benchmarking scenarios.

# 1. Populating the tree iteratively
INSERT 50
INSERT 25
INSERT 75
INSERT 80
INSERT 90

# 2. Applying an ad-hoc custom rule mid-execution
# If the right side gets too heavy, we do a manual fix.
IF balance_factor > 1 AND right_child_balance > 0 THEN {
    ROTATE_LEFT
}

# 3. Triggers for teardown and cleanup
DELETE 25

# 4. Standard AVL rebalancing commands
IF balance_factor < -1 AND right_child_balance > 0 THEN {
    ROTATE_RIGHT_LEFT
}
