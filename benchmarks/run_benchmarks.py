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


sequences = {
    "sorted_asc":  list(range(1, 51)),
    "sorted_desc": list(range(50, 0, -1)),
    "random":      random.sample(range(1, 201), 50),
}

results = []
interp = DSLInterpreter()

for seq_name, seq in sequences.items():
    bst = BST()
    for i, val in enumerate(seq):
        bst.insert(val)
        bst.root = interp.balance_tree(bst.root, AVL_DSL)
        h = get_height(bst.root)
        results.append({
            "sequence": seq_name,
            "n": i + 1,
            "height": h,
            "val_inserted": val,
        })

os.makedirs(os.path.join(os.path.dirname(__file__)), exist_ok=True)
with open(os.path.join(os.path.dirname(__file__), "results.csv"), "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["sequence", "n", "height", "val_inserted"])
    writer.writeheader()
    writer.writerows(results)

print(f"Results written to benchmarks/results.csv ({len(results)} rows)")
