"""
Generates empirical profiling data for Chapter 5 using cProfile.
Outputs the top time-consuming functions to benchmarks/dsl_profile.txt
"""
import cProfile
import pstats
import io
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tree import BST
from interpreter import DSLInterpreter

def run_bulk_insertions():
    # Setup tree and interpreter
    tree = BST()
    interpreter = DSLInterpreter()
    
    # Load AVL DSL script
    dsl_script = open(os.path.join(os.path.dirname(__file__), '..', 'examples', 'avl.dsl')).read()
    
    # Run the 1000 insertions
    for i in range(1000):
        tree.insert(i)
        # Using balance_tree as balance_step only applies a single rotation
        tree.root = interpreter.balance_tree(tree.root, dsl_script)

if __name__ == "__main__":
    print("Initializing profiler...")
    profiler = cProfile.Profile()
    
    print("Running 1,000 insertions (this will take a moment)...")
    profiler.enable()
    run_bulk_insertions()
    profiler.disable()

    print("Formatting results...")
    s = io.StringIO()
    # Sort by cumulative time to find the biggest bottlenecks
    sortby = 'cumulative' 
    ps = pstats.Stats(profiler, stream=s).sort_stats(sortby)

    # Print the top 40 most time-consuming functions to the file
    ps.print_stats(40)
    
    profile_data = s.getvalue()
    
    # Print a summary to console
    print(profile_data[:1000] + "\n... [truncated] ...\n")
    
    out_path = os.path.join(os.path.dirname(__file__), "dsl_profile.txt")
    with open(out_path, "w") as f:
        f.write("=== DSL Profiling Results (1,000 sorted ascending insertions) ===\n")
        f.write(profile_data)
        
    print(f"Full profile written to {out_path}")
