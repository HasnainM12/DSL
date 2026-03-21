class TreeNode:
    def __init__(self, val):
        self.val = val
        self.left = None
        self.right = None
        self.height = 1  # Height is 1 for a new leaf
        self.parent = None
        # Placeholder for Red-Black future work [cite: 50]
        self.colour = "RED" 

class BST:
    def __init__(self):
        self.root = None
        self.rotations = 0

    # ==========================================
    # Core Operations
    # ==========================================
    def insert(self, val):
        """Standard BST insertion. Returns True if inserted, False if duplicate."""
        if self.contains(val):
            return False
        if not self.root:
            self.root = TreeNode(val)
        else:
            self.root = self._insert_recursive(self.root, val)
        return True

    def _insert_recursive(self, node, val):
        if not node:
            return TreeNode(val)
        
        if val < node.val:
            node.left = self._insert_recursive(node.left, val)
            node.left.parent = node
        elif val > node.val:
            node.right = self._insert_recursive(node.right, val)
            node.right.parent = node
        else:
            # Duplicate value — return node unchanged
            return node

        # Update height after insertion
        node.height = 1 + max(self.get_height(node.left), self.get_height(node.right))
        
        return node

    def contains(self, val) -> bool:
        """Return True if *val* is already present in the tree."""
        node = self.root
        while node:
            if val == node.val:
                return True
            elif val < node.val:
                node = node.left
            else:
                node = node.right
        return False

    def delete(self, val):
        """Standard BST deletion. Returns True if deleted, False if not found."""
        if not self.contains(val):
            return False
        self.root = self._delete_recursive(self.root, val)
        return True

    def _delete_recursive(self, node, val):
        if not node:
            return None

        if val < node.val:
            node.left = self._delete_recursive(node.left, val)
            if node.left:
                node.left.parent = node
        elif val > node.val:
            node.right = self._delete_recursive(node.right, val)
            if node.right:
                node.right.parent = node
        else:
            # Found the node to delete
            if not node.left:
                return node.right
            if not node.right:
                return node.left
            # Two children: replace with in-order successor (smallest in right subtree)
            successor = node.right
            while successor.left:
                successor = successor.left
            node.val = successor.val
            node.right = self._delete_recursive(node.right, successor.val)

        # Update height
        node.height = 1 + max(self.get_height(node.left), self.get_height(node.right))
        return node

    # ==========================================
    # DSL Helper Methods (The "Sensors")
    # ==========================================
    # These methods provide the data requested by the DSL grammar
    
    def get_height(self, node):
        if not node:
            return 0
        return node.height

    def get_balance_factor(self, node):
        """Calculates balance factor (Left Height - Right Height)."""
        if not node:
            return 0
        return self.get_height(node.left) - self.get_height(node.right)

    # ==========================================
    # Rotation Logic (The "Actuators")
    # ==========================================
    # These are triggered when the DSL rule actions are executed
    
    def rotate_left(self, z):
        """
        Performs a left rotation around node z.
        Returns the new root of the subtree.
        """
        if not z or not z.right:
            return z  # Cannot rotate

        self.rotations += 1

        y = z.right
        T2 = y.left

        # Perform rotation
        y.left = z
        z.right = T2

        # Update parent pointers
        y.parent = z.parent
        z.parent = y
        if T2:
            T2.parent = z

        # Update heights (z first, then y)
        z.height = 1 + max(self.get_height(z.left), self.get_height(z.right))
        y.height = 1 + max(self.get_height(y.left), self.get_height(y.right))

        # Return new root
        return y

    def rotate_right(self, z):
        """
        Performs a right rotation around node z.
        Returns the new root of the subtree.
        """
        if not z or not z.left:
            return z # Cannot rotate

        self.rotations += 1

        y = z.left
        T3 = y.right

        # Perform rotation
        y.right = z
        z.left = T3

        # Update parent pointers
        y.parent = z.parent
        z.parent = y
        if T3:
            T3.parent = z

        # Update heights
        z.height = 1 + max(self.get_height(z.left), self.get_height(z.right))
        y.height = 1 + max(self.get_height(y.left), self.get_height(y.right))

        return y

    def rotate_left_right(self, z):
        """
        Performs a left-right rotation around node z.
        First rotates left on z.left, then rotates right on z.
        Returns the new root of the subtree.
        """
        if not z or not z.left:
            return z  # Cannot rotate

        # First, rotate left on the left child
        z.left = self.rotate_left(z.left)
        
        # Then, rotate right on the current node
        return self.rotate_right(z)

    def rotate_right_left(self, z):
        """
        Performs a right-left rotation around node z.
        First rotates right on z.right, then rotates left on z.
        Returns the new root of the subtree.
        """
        if not z or not z.right:
            return z  # Cannot rotate

        # First, rotate right on the right child
        z.right = self.rotate_right(z.right)
        
        # Then, rotate left on the current node
        return self.rotate_left(z)