# AVL Balancing Rules
# Order matters — double rotations must come before single rotations

IF balance_factor > 1 AND left_child_balance < 0 THEN ROTATE_LEFT_RIGHT
IF balance_factor < -1 AND right_child_balance > 0 THEN ROTATE_RIGHT_LEFT
IF balance_factor > 1 THEN ROTATE_RIGHT
IF balance_factor < -1 THEN ROTATE_LEFT
