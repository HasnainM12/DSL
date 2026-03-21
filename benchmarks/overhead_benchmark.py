"""
Interpreter overhead benchmark — times DSL-driven vs native Python AVL.
Outputs results to benchmarks/overhead.csv
"""
import csv
import time
import random
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tree import BST, TreeNode
from interpreter import DSLInterpreter

AVL_DSL = open(os.path.join(os.path.dirname(__file__), '..', 'examples', 'avl.dsl')).read()

N = 1000
random.seed(42)
values = random.sample(range(1, N * 10), N)


# --- Method 1: Native Python AVL balance (no DSL) ---
def native_balance(node, bst_ops):
    """Pure-Python AVL balance pass (no DSL parsing)."""
    if not node:
        return node

    node.left = native_balance(node.left, bst_ops)
    node.right = native_balance(node.right, bst_ops)

    node.height = 1 + max(
        node.left.height if node.left else 0,
        node.right.height if node.right else 0,
    )

    bf = (node.left.height if node.left else 0) - (node.right.height if node.right else 0)

    # Double rotations first
    if bf > 1 and node.left:
        left_bf = (node.left.left.height if node.left.left else 0) - \
                  (node.left.right.height if node.left.right else 0)
        if left_bf < 0:
            node = bst_ops.rotate_left_right(node)
            return node
    if bf < -1 and node.right:
        right_bf = (node.right.left.height if node.right.left else 0) - \
                   (node.right.right.height if node.right.right else 0)
        if right_bf > 0:
            node = bst_ops.rotate_right_left(node)
            return node

    if bf > 1:
        node = bst_ops.rotate_right(node)
    elif bf < -1:
        node = bst_ops.rotate_left(node)

    return node


results = []

# --- Native benchmark ---
bst_native = BST()
start = time.perf_counter()
for val in values:
    bst_native.insert(val)
    bst_native.root = native_balance(bst_native.root, bst_native)
elapsed_native = (time.perf_counter() - start) * 1000
results.append({"method": "native_python", "n": N, "elapsed_ms": f"{elapsed_native:.2f}"})
print(f"Native Python:  {elapsed_native:.2f} ms for {N} inserts")

# --- DSL benchmark ---
interp = DSLInterpreter()
bst_dsl = BST()
start = time.perf_counter()
for val in values:
    bst_dsl.insert(val)
    bst_dsl.root = interp.balance_tree(bst_dsl.root, AVL_DSL)
elapsed_dsl = (time.perf_counter() - start) * 1000
results.append({"method": "dsl_driven", "n": N, "elapsed_ms": f"{elapsed_dsl:.2f}"})
print(f"DSL-driven:     {elapsed_dsl:.2f} ms for {N} inserts")

overhead = elapsed_dsl / elapsed_native if elapsed_native > 0 else float('inf')
print(f"Overhead factor: {overhead:.2f}x")

os.makedirs(os.path.join(os.path.dirname(__file__)), exist_ok=True)
with open(os.path.join(os.path.dirname(__file__), "overhead.csv"), "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["method", "n", "elapsed_ms"])
    writer.writeheader()
    writer.writerows(results)

print("Results written to benchmarks/overhead.csv")
