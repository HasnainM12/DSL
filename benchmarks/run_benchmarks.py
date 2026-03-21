"""
Benchmarking harness — compares DSL-driven AVL against native Python AVL.
Outputs results to benchmarks/results.csv
"""
import csv
import random
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tree import BST
from interpreter import DSLInterpreter

AVL_DSL = open(os.path.join(os.path.dirname(__file__), '..', 'examples', 'avl.dsl')).read()


def get_height(node):
    return node.height if node else 0


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


sequences = {
    "sorted_asc":  list(range(1, 51)),
    "sorted_desc": list(range(50, 0, -1)),
    "random":      random.sample(range(1, 201), 50),
}

results = []

for seq_name, seq in sequences.items():
    # Native Pass
    bst_native = BST()
    for i, val in enumerate(seq):
        bst_native.insert(val)
        bst_native.root = native_balance(bst_native.root, bst_native)
        h = get_height(bst_native.root)
        results.append({
            "sequence": seq_name,
            "method": "native_python",
            "n": i + 1,
            "height": h,
            "rotations": bst_native.rotations,
            "val_inserted": val,
        })

    # DSL Pass
    bst_dsl = BST()
    interp = DSLInterpreter()
    for i, val in enumerate(seq):
        bst_dsl.insert(val)
        bst_dsl.root = interp.balance_tree(bst_dsl.root, AVL_DSL)
        h = get_height(bst_dsl.root)
        results.append({
            "sequence": seq_name,
            "method": "dsl_driven",
            "n": i + 1,
            "height": h,
            "rotations": interp.rotations,
            "val_inserted": val,
        })

os.makedirs(os.path.join(os.path.dirname(__file__)), exist_ok=True)
with open(os.path.join(os.path.dirname(__file__), "results.csv"), "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["sequence", "method", "n", "height", "rotations", "val_inserted"])
    writer.writeheader()
    writer.writerows(results)

print(f"Results written to benchmarks/results.csv ({len(results)} rows)")
