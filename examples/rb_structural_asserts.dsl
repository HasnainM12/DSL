# Red-Black Tree Structural Asserts
#
# Showcases the grammar's ability to interrogate complex tree topologies,
# using sibling, parent, and uncle keywords alongside boolean logic.

# 1. Enforcing Red-Black invariant: No double RED nodes
# If a violation occurs, we can halt and propagate the error up
IF node_colour == "RED" AND parent_colour == "RED" THEN {
    PROPAGATE
}

# 2. Complex relationship constraints
# We can check specific grandchild relationships (sibling's children)
IF NOT (node_colour == "BLACK") AND (sibling_colour == "RED" OR sibling_left_colour == "RED") THEN {
    SET_SIBLING_COLOUR "BLACK"
}

# 3. Deep Structural positioning and multiple fixup actions
IF is_left_child == 1 AND parent_is_left_child == 0 AND uncle_colour == "BLACK" THEN {
    SET_COLOUR "BLACK"
    SET_GRANDPARENT_COLOUR "RED"
    ROTATE_RIGHT_AT_PARENT
    ROTATE_LEFT_AT_GRANDPARENT
    DONE
}
