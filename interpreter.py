import os

from lark import Lark, Transformer, Tree, v_args

from tree import BST, TreeNode


# ==========================================
# 1. The Logic Evaluator (Transformer)
# ==========================================
@v_args(inline=True)
class BalancingLogic(Transformer):
    def __init__(self, current_node):
        self.node = current_node

    # --- Primitives ---

    def number(self, n):
        return float(n)

    # --- Tree Properties (Sensors) ---
    def get_height(self, _):
        return self.node.height if self.node else 0

    def get_balance(self, _):
        if not self.node:
            return 0
        left_h = self.node.left.height if self.node.left else 0
        right_h = self.node.right.height if self.node.right else 0
        return left_h - right_h

    def get_left_balance(self, _):
        if not self.node or not self.node.left:
            return 0
        left_h = self.node.left.left.height if self.node.left.left else 0
        right_h = self.node.left.right.height if self.node.left.right else 0
        return left_h - right_h

    def get_right_balance(self, _):
        if not self.node or not self.node.right:
            return 0
        left_h = self.node.right.left.height if self.node.right.left else 0
        right_h = self.node.right.right.height if self.node.right.right else 0
        return left_h - right_h

    def get_colour(self, _):
        return self.node.colour if self.node else "BLACK"

    def get_parent_colour(self, _):
        """Return the colour of the current node's parent (BLACK if root)."""
        if self.node and self.node.parent:
            return self.node.parent.colour
        return "BLACK"

    def get_uncle_colour(self, _):
        """Return the colour of the current node's uncle (BLACK if absent)."""
        if not self.node or not self.node.parent or not self.node.parent.parent:
            return "BLACK"
        grandparent = self.node.parent.parent
        if grandparent.left is self.node.parent:
            uncle = grandparent.right
        else:
            uncle = grandparent.left
        return uncle.colour if uncle else "BLACK"

    def get_is_left_child(self, _):
        """Return 1 if current node is its parent's left child, else 0."""
        if not self.node or not self.node.parent:
            return 0
        return 1 if self.node.parent.left is self.node else 0

    def get_parent_is_left_child(self, _):
        """Return 1 if current node's parent is grandparent's left child, else 0."""
        if not self.node or not self.node.parent:
            return 0
        parent = self.node.parent
        if not parent.parent:
            return 0
        return 1 if parent.parent.left is parent else 0

    def get_sibling_colour(self, _):
        """Return the colour of the current node's sibling (BLACK if absent)."""
        sibling = self._get_sibling(self.node)
        return sibling.colour if sibling else "BLACK"

    def get_sibling_left_colour(self, _):
        """Return the colour of the sibling's left child (BLACK if absent)."""
        sibling = self._get_sibling(self.node)
        if sibling and sibling.left:
            return sibling.left.colour
        return "BLACK"

    def get_sibling_right_colour(self, _):
        """Return the colour of the sibling's right child (BLACK if absent)."""
        sibling = self._get_sibling(self.node)
        if sibling and sibling.right:
            return sibling.right.colour
        return "BLACK"

    @staticmethod
    def _parse_colour(colour_str):
        """Extract a clean colour string from a Lark tree or plain string."""
        raw = (
            str(colour_str.children[0])
            if hasattr(colour_str, "children")
            else str(colour_str)
        )
        return raw.strip('"').upper()

    @staticmethod
    def _get_uncle(node):
        """Return the uncle node (or None) for a given node."""
        if not node or not node.parent or not node.parent.parent:
            return None
        grandparent = node.parent.parent
        if grandparent.left is node.parent:
            return grandparent.right
        return grandparent.left

    @staticmethod
    def _get_sibling(node):
        """Return the sibling node (or None) for a given node."""
        if not node or not node.parent:
            return None
        if node.parent.left is node:
            return node.parent.right
        return node.parent.left

    def set_colour(self, colour_str):
        """Handle SET_COLOUR action — returns a tuple for the action loop."""
        return ("SET_COLOUR", self._parse_colour(colour_str))

    def set_parent_colour(self, colour_str):
        """Handle SET_PARENT_COLOUR — recolour current node's parent."""
        return ("SET_PARENT_COLOUR", self._parse_colour(colour_str))

    def set_uncle_colour(self, colour_str):
        """Handle SET_UNCLE_COLOUR — recolour current node's uncle."""
        return ("SET_UNCLE_COLOUR", self._parse_colour(colour_str))

    def set_grandparent_colour(self, colour_str):
        """Handle SET_GRANDPARENT_COLOUR — recolour current node's grandparent."""
        return ("SET_GRANDPARENT_COLOUR", self._parse_colour(colour_str))

    def set_sibling_colour(self, colour_str):
        """Handle SET_SIBLING_COLOUR — recolour current node's sibling."""
        return ("SET_SIBLING_COLOUR", self._parse_colour(colour_str))

    def set_sibling_left_colour(self, colour_str):
        """Handle SET_SIBLING_LEFT_COLOUR — recolour sibling's left child."""
        return ("SET_SIBLING_LEFT_COLOUR", self._parse_colour(colour_str))

    def set_sibling_right_colour(self, colour_str):
        """Handle SET_SIBLING_RIGHT_COLOUR — recolour sibling's right child."""
        return ("SET_SIBLING_RIGHT_COLOUR", self._parse_colour(colour_str))

    def set_sibling_colour_from_parent(self, _):
        """Handle SET_SIBLING_COLOUR_FROM_PARENT — copy parent colour to sibling."""
        return "SET_SIBLING_COLOUR_FROM_PARENT"

    def string(self, s):
        return str(s)

    def string_literal(self, s):
        """Return a bare string (strip quotes) for use in comparisons."""
        return str(s).strip('"')

    # --- Arithmetic ---
    def add_expr(self, left, right):
        return float(left) + float(right)

    def sub_expr(self, left, right):
        return float(left) - float(right)

    def term(self, val):
        return val

    def expression(self, val):
        """Pass-through for expression: term (no arithmetic)."""
        return val

    # --- Comparisons ---
    def comparison(self, val1, op, val2):
        # Robust Operator Extraction
        operator = getattr(op, "value", str(op))

        # Try numeric comparison first, fall back to string for colours
        try:
            v1 = float(val1)
            v2 = float(val2)
        except (ValueError, TypeError):
            # String comparison (e.g. node_colour == "RED")
            v1 = str(val1).strip('"').upper()
            v2 = str(val2).strip('"').upper()

        if operator == ">":
            return v1 > v2
        if operator == "<":
            return v1 < v2
        if operator == "==":
            return v1 == v2
        if operator == "!=":
            return v1 != v2
        if operator == ">=":
            return v1 >= v2
        if operator == "<=":
            return v1 <= v2
        return False

    # --- Boolean Logic ---
    def and_expr(self, cond1, cond2):
        return cond1 and cond2

    def or_expr(self, cond1, cond2):
        return cond1 or cond2

    def not_expr(self, cond):
        return not cond

    # --- Actions ---
    def action_block(self, *actions):
        return list(actions)

    def rotate_left(self, _):
        return "ROTATE_LEFT"

    def rotate_right(self, _):
        return "ROTATE_RIGHT"

    def rotate_left_right(self, _):
        return "ROTATE_LEFT_RIGHT"

    def rotate_right_left(self, _):
        return "ROTATE_RIGHT_LEFT"

    def rotate_left_at_parent(self, _):
        return "ROTATE_LEFT_AT_PARENT"

    def rotate_right_at_parent(self, _):
        return "ROTATE_RIGHT_AT_PARENT"

    def rotate_left_at_grandparent(self, _):
        return "ROTATE_LEFT_AT_GRANDPARENT"

    def rotate_right_at_grandparent(self, _):
        return "ROTATE_RIGHT_AT_GRANDPARENT"

    def rotate_left_at_sibling(self, _):
        return "ROTATE_LEFT_AT_SIBLING"

    def rotate_right_at_sibling(self, _):
        return "ROTATE_RIGHT_AT_SIBLING"

    def signal_done(self, _):
        return "SIGNAL_DONE"

    def signal_propagate(self, _):
        return "SIGNAL_PROPAGATE"

    def insert_cmd(self, n):
        return ("INSERT", int(float(n)))

    def delete_cmd(self, n):
        return ("DELETE", int(float(n)))

    @v_args(inline=False, meta=True)
    def rule(self, meta, children):
        condition, actions = children[0], children[1]
        # Extract the actual boolean value from the Tree object
        actual_condition = condition
        if hasattr(condition, "children") and condition.children:
            actual_condition = condition.children[0]

        if actual_condition:
            if not isinstance(actions, list):
                actions = [actions]
            return [{"type": "highlight_line", "line": meta.line}] + actions
        return None

    def start(self, *items):
        # First-match-wins for rules: when an IF/THEN rule fires (returns a
        # list), return immediately — remaining rules are not evaluated.  This
        # mirrors the if/elif structure of native implementations.
        # Bare actions (tuples like INSERT/DELETE) are always collected.
        collected = []
        for item in items:
            if item:
                if isinstance(item, list):
                    # A triggered rule — return its actions immediately
                    # (prepend any bare actions already collected)
                    return collected + item
                else:
                    collected.append(item)
        return collected


# ==========================================
# 2. The Interpreter Engine
# ==========================================


class DSLInterpreter:
    def __init__(self, grammar_file="grammar.lark"):
        # The Path Fix:
        # Finds grammar.lark in the same directory as this script (DSL/)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        grammar_path = os.path.join(base_dir, grammar_file)

        with open(grammar_path, "r") as f:
            self.parser = Lark(
                f.read(), start="start", parser="lalr", propagate_positions=True
            )

        self.rotations = 0

    def apply_rules(self, node, dsl_input, return_flag=False):
        if not node:
            if return_flag:
                return None, False
            return None

        # Accept either a raw DSL string or a pre-parsed Lark Tree
        if isinstance(dsl_input, Tree):
            parsed_tree = dsl_input
        else:
            try:
                parsed_tree = self.parser.parse(dsl_input)
            except Exception as e:
                raise RuntimeError(f"Syntax Error in DSL: {e}")

        # Capture structural relatives before any mutations.
        # SET_GRANDPARENT_COLOUR and the rotate-at-relative actions all rely on
        # these references staying valid; the DSL rules always place recolouring
        # BEFORE rotation actions in each action block, so orig_gp is still the
        # correct grandparent when SET_GRANDPARENT_COLOUR executes.
        orig_parent = node.parent
        orig_gp = orig_parent.parent if orig_parent else None
        orig_ggp = orig_gp.parent if orig_gp else None
        # Snapshot sibling for deletion fix-up operations
        if node and node.parent:
            orig_sibling = (
                node.parent.right if node.parent.left is node else node.parent.left
            )
        else:
            orig_sibling = None

        # Evaluate the AST with this node's context
        evaluator = BalancingLogic(node)
        try:
            actions = evaluator.transform(parsed_tree)
        except Exception as e:
            raise RuntimeError(f"Runtime Error: {str(e)}")

        # 3. Execute
        new_root = node
        tree_ops = BST()

        for action in actions:
            if action == "ROTATE_LEFT":
                self.rotations += 1
                new_root = tree_ops.rotate_left(new_root)
            elif action == "ROTATE_RIGHT":
                self.rotations += 1
                new_root = tree_ops.rotate_right(new_root)
            elif action == "ROTATE_LEFT_RIGHT":
                self.rotations += 2
                new_root = tree_ops.rotate_left_right(new_root)
            elif action == "ROTATE_RIGHT_LEFT":
                self.rotations += 2
                new_root = tree_ops.rotate_right_left(new_root)
            elif action == "ROTATE_LEFT_AT_PARENT":
                if orig_parent:
                    new_sr = tree_ops.rotate_left(orig_parent)
                    if orig_gp:
                        if orig_gp.left is orig_parent:
                            orig_gp.left = new_sr
                        elif orig_gp.right is orig_parent:
                            orig_gp.right = new_sr
                    self.rotations += 1
            elif action == "ROTATE_RIGHT_AT_PARENT":
                if orig_parent:
                    new_sr = tree_ops.rotate_right(orig_parent)
                    if orig_gp:
                        if orig_gp.left is orig_parent:
                            orig_gp.left = new_sr
                        elif orig_gp.right is orig_parent:
                            orig_gp.right = new_sr
                    self.rotations += 1
            elif action == "ROTATE_LEFT_AT_GRANDPARENT":
                if orig_gp:
                    new_sr = tree_ops.rotate_left(orig_gp)
                    if orig_ggp:
                        if orig_ggp.left is orig_gp:
                            orig_ggp.left = new_sr
                        elif orig_ggp.right is orig_gp:
                            orig_ggp.right = new_sr
                    self.rotations += 1
                    new_root = new_sr
            elif action == "ROTATE_RIGHT_AT_GRANDPARENT":
                if orig_gp:
                    new_sr = tree_ops.rotate_right(orig_gp)
                    if orig_ggp:
                        if orig_ggp.left is orig_gp:
                            orig_ggp.left = new_sr
                        elif orig_ggp.right is orig_gp:
                            orig_ggp.right = new_sr
                    self.rotations += 1
                    new_root = new_sr
            elif isinstance(action, tuple) and action[0] == "SET_COLOUR":
                new_root.colour = action[1]
            elif isinstance(action, tuple) and action[0] == "SET_PARENT_COLOUR":
                if new_root.parent:
                    new_root.parent.colour = action[1]
            elif isinstance(action, tuple) and action[0] == "SET_UNCLE_COLOUR":
                uncle = BalancingLogic._get_uncle(new_root)
                if uncle:
                    uncle.colour = action[1]
            elif isinstance(action, tuple) and action[0] == "SET_GRANDPARENT_COLOUR":
                if new_root.parent and new_root.parent.parent:
                    new_root.parent.parent.colour = action[1]
            elif isinstance(action, tuple) and action[0] == "SET_SIBLING_COLOUR":
                sibling = BalancingLogic._get_sibling(new_root)
                if sibling:
                    sibling.colour = action[1]
            elif isinstance(action, tuple) and action[0] == "SET_SIBLING_LEFT_COLOUR":
                sibling = BalancingLogic._get_sibling(new_root)
                if sibling and sibling.left:
                    sibling.left.colour = action[1]
            elif isinstance(action, tuple) and action[0] == "SET_SIBLING_RIGHT_COLOUR":
                sibling = BalancingLogic._get_sibling(new_root)
                if sibling and sibling.right:
                    sibling.right.colour = action[1]
            elif action == "SET_SIBLING_COLOUR_FROM_PARENT":
                sibling = BalancingLogic._get_sibling(new_root)
                if sibling and new_root.parent:
                    sibling.colour = new_root.parent.colour
            elif action == "ROTATE_LEFT_AT_SIBLING":
                if orig_sibling:
                    parent = orig_sibling.parent
                    new_sr = tree_ops.rotate_left(orig_sibling)
                    if parent:
                        if parent.left is orig_sibling:
                            parent.left = new_sr
                        elif parent.right is orig_sibling:
                            parent.right = new_sr
                    self.rotations += 1
            elif action == "ROTATE_RIGHT_AT_SIBLING":
                if orig_sibling:
                    parent = orig_sibling.parent
                    new_sr = tree_ops.rotate_right(orig_sibling)
                    if parent:
                        if parent.left is orig_sibling:
                            parent.left = new_sr
                        elif parent.right is orig_sibling:
                            parent.right = new_sr
                    self.rotations += 1
            # SIGNAL_DONE and SIGNAL_PROPAGATE are non-mutating control signals;
            # they remain in the actions list for the caller to inspect.

        if return_flag:
            return new_root, actions
        return new_root

    def balance_step(self, node, parsed_tree):
        """Apply EXACTLY ONE rotation (the first found bottom-up) and return.

        Returns (new_node, changed) where *changed* is True when a rotation
        was performed during this call.  The caller can keep calling this
        method until *changed* comes back False to animate one rotation per
        frame.
        """
        new_root, changed = self._balance_step_recursive(node, parsed_tree)
        if new_root and hasattr(new_root, "colour"):
            new_root.colour = "BLACK"
        return new_root, changed

    def _balance_step_recursive(self, node, parsed_tree):
        if not node:
            return None, False

        # Recurse left first
        _, changed = self._balance_step_recursive(node.left, parsed_tree)
        if changed:
            node.height = 1 + max(
                node.left.height if node.left else 0,
                node.right.height if node.right else 0,
            )
            curr = node
            while curr and curr.parent:
                curr = curr.parent
            return curr, True

        # Then right
        _, changed = self._balance_step_recursive(node.right, parsed_tree)
        if changed:
            node.height = 1 + max(
                node.left.height if node.left else 0,
                node.right.height if node.right else 0,
            )
            curr = node
            while curr and curr.parent:
                curr = curr.parent
            return curr, True

        # Update height at this node
        node.height = 1 + max(
            node.left.height if node.left else 0,
            node.right.height if node.right else 0,
        )

        # Try to apply rules at this node.
        # NOTE: triggered may contain INSERT/DELETE tuples from the script even
        # when no IF rule fired.  Only return changed=True when an actual rule
        # condition was met — indicated by the presence of a highlight_line dict
        # that rule() unconditionally prepends to its actions list.
        new_sub_root, triggered = self.apply_rules(node, parsed_tree, return_flag=True)
        rule_fired = triggered and any(
            isinstance(a, dict) and a.get("type") == "highlight_line"
            for a in triggered
        )
        if rule_fired:
            # Walk up from the (possibly rotated) sub-root to find the tree root
            curr = new_sub_root if new_sub_root else node
            while curr and curr.parent:
                curr = curr.parent
            return curr, True

        curr = node
        while curr and curr.parent:
            curr = curr.parent
        return curr, False

    def execute_script(self, dsl_script):
        """Parse a full DSL script and return a flat list of actions.

        Each action is either a rotation string (e.g. ``"ROTATE_LEFT"``) or
        a tuple like ``("INSERT", 10)`` / ``("DELETE", 20)``.
        Rules whose conditions are False produce no actions.
        """
        parsed_tree = self.parser.parse(dsl_script)  # caller handles errors
        evaluator = BalancingLogic(current_node=None)
        return evaluator.transform(parsed_tree)

    def balance_tree(self, node, dsl_script):
        if not node:
            return None

        # Parse the DSL script exactly once, then pass the AST down
        try:
            parsed_tree = self.parser.parse(dsl_script)
        except Exception as e:
            raise RuntimeError(f"Syntax Error in DSL: {e}")

        new_root = self._balance_recursive(node, parsed_tree)
        if new_root and hasattr(new_root, "colour"):
            new_root.colour = "BLACK"
        return new_root

    def _balance_recursive(self, node, parsed_tree):
        if not node:
            return None

        # Post-Order Traversal (Bottom-Up)
        self._balance_recursive(node.left, parsed_tree)
        self._balance_recursive(node.right, parsed_tree)

        # Update height before applying rules
        node.height = 1 + max(
            node.left.height if node.left else 0, node.right.height if node.right else 0
        )

        self.apply_rules(node, parsed_tree)

        curr = node
        while curr and curr.parent:
            curr = curr.parent
        return curr

    # ==================================================================
    # Red-Black Deletion Engine
    # ==================================================================

    @staticmethod
    def _find_node(root, val):
        """Search for a node with *val* starting from *root*."""
        node = root
        while node:
            if val == node.val:
                return node
            elif val < node.val:
                node = node.left
            else:
                node = node.right
        return None

    @staticmethod
    def _minimum(node):
        """Return the leftmost descendant of *node*."""
        while node.left:
            node = node.left
        return node

    @staticmethod
    def _transplant(root, u, v):
        """Replace subtree rooted at *u* with subtree rooted at *v*.

        Returns the (possibly new) tree root.
        """
        if not u.parent:
            root = v
        elif u is u.parent.left:
            u.parent.left = v
        else:
            u.parent.right = v
        if v:
            v.parent = u.parent
        return root

    def rb_delete(self, root, val, delete_dsl):
        """Delete *val* from the RB tree rooted at *root* using DSL fix-up rules.

        Returns the new root.
        """
        if not root:
            return None

        # Parse DSL once
        if isinstance(delete_dsl, Tree):
            parsed_dsl = delete_dsl
        else:
            parsed_dsl = self.parser.parse(delete_dsl)

        z = self._find_node(root, val)
        if z is None:
            return root  # not found

        y = z  # node to be physically removed
        y_original_colour = y.colour

        if z.left is None:
            x = z.right
            x_parent = z.parent
            x_is_left = z.parent and z.parent.left is z
            root = self._transplant(root, z, z.right)
        elif z.right is None:
            x = z.left
            x_parent = z.parent
            x_is_left = z.parent and z.parent.left is z
            root = self._transplant(root, z, z.left)
        else:
            y = self._minimum(z.right)
            y_original_colour = y.colour
            x = y.right
            if y.parent is z:
                x_parent = y
                x_is_left = False  # x replaces y which is z.right's subtree
            else:
                x_parent = y.parent
                x_is_left = y.parent.left is y
                root = self._transplant(root, y, y.right)
                y.right = z.right
                y.right.parent = y
            root = self._transplant(root, z, y)
            y.left = z.left
            y.left.parent = y
            y.colour = z.colour

        # Fix-up if we removed a BLACK node
        if y_original_colour == "BLACK":
            root = self._rb_delete_fixup(root, x, x_parent, x_is_left, parsed_dsl)

        # Ensure root is BLACK
        if root:
            root.colour = "BLACK"

        return root

    def _rb_delete_fixup(self, root, x, x_parent, x_is_left, parsed_dsl):
        """Apply DSL deletion fix-up rules iteratively.

        *x* may be None (double-black NIL). *x_parent* and *x_is_left*
        track position when x is None.
        """
        MAX_ITER = 200  # safety bound

        for _ in range(MAX_ITER):
            # Termination: x is root or x is RED
            if x is root:
                break
            if x is not None and x.colour == "RED":
                break
            if x is None and x_parent is None:
                break

            # --- Phantom node for None case ---
            phantom = None
            eval_node = x
            if x is None:
                phantom = TreeNode(val=0)
                phantom.colour = "BLACK"
                phantom.parent = x_parent
                if x_is_left:
                    x_parent.left = phantom
                else:
                    x_parent.right = phantom
                eval_node = phantom

            # Apply the DSL rules at this node — returns (new_node, actions_list)
            _, actions = self.apply_rules(eval_node, parsed_dsl, return_flag=True)

            # Remove phantom node (restore None in parent's child slot)
            if phantom is not None:
                if phantom.parent:
                    if phantom.parent.left is phantom:
                        phantom.parent.left = None
                    elif phantom.parent.right is phantom:
                        phantom.parent.right = None
                phantom.parent = None

            # Update root if a rotation moved it
            if root and root.parent:
                while root.parent:
                    root = root.parent

            if not actions:
                break

            # Check control signals
            if "SIGNAL_DONE" in actions:
                break

            if "SIGNAL_PROPAGATE" in actions:
                x = x_parent
                x_parent = x.parent if x else None
                if x and x.parent:
                    x_is_left = x.parent.left is x
                continue

            # Cases 1, 3: tree was transformed, re-evaluate at same position

        if x is not None:
            x.colour = "BLACK"

        return root
