import pytest
from entropy.constraint_bank import ConstraintBank

@pytest.fixture
def constraint_bank():
    return ConstraintBank()

def test_constraint_bank_add_and_get(constraint_bank):
    """Tests adding and getting constraints."""
    constraint1 = "x > 10"
    constraint2 = "y < 5"

    constraint_bank.add_constraint(constraint1)
    constraint_bank.add_constraint(constraint2)

    constraints = constraint_bank.get_constraints()
    assert len(constraints) == 2
    assert constraint1 in constraints
    assert constraint2 in constraints

def test_constraint_bank_add_duplicate(constraint_bank):
    """Tests that adding a duplicate constraint does not change the bank."""
    constraint = "x > 10"
    constraint_bank.add_constraint(constraint)
    constraint_bank.add_constraint(constraint)

    assert len(constraint_bank) == 1

def test_constraint_bank_len(constraint_bank):
    """Tests the __len__ method."""
    assert len(constraint_bank) == 0
    constraint_bank.add_constraint("a == b")
    assert len(constraint_bank) == 1

def test_check_violation_placeholder(constraint_bank):
    """Tests the placeholder implementation of check_violation."""
    assert not constraint_bank.check_violation({"x": 5})
