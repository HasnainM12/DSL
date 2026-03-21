"""Shared pytest fixtures for the DSL test-suite."""
import pytest
from tree import BST
from interpreter import DSLInterpreter


@pytest.fixture
def interpreter():
    """A fresh DSLInterpreter instance."""
    return DSLInterpreter()


@pytest.fixture
def avl_rules():
    """The standard two-rule AVL balancing script."""
    from tests.helpers import AVL_RULES
    return AVL_RULES


@pytest.fixture
def sample_bst():
    """A pre-populated 7-node BST: 50, 25, 75, 10, 30, 60, 80."""
    bst = BST()
    for v in [50, 25, 75, 10, 30, 60, 80]:
        bst.insert(v)
    return bst
