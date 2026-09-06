from bc_lp import project_cuts, solve_node_lp
from bc_scenario import KnapsackInstance


def test_project_cuts_reduces_rhs_by_fixed_included_items():
    # Deckung {0,1,2}, item 0 bereits aufgenommen -> rhs sinkt von 2 auf 1, nur
    # noch Pakete 1,2 sind frei in dieser Restriktion.
    decisions = {0: True}
    projected = project_cuts([(0, 1, 2)], decisions)
    assert projected == [([1, 2], 1)]


def test_project_cuts_ignores_items_excluded_by_decision():
    # Item 0 bereits AUSGELASSEN zählt nicht zur fixed_sum, verkleinert aber die
    # freie Menge in der Restriktion.
    decisions = {0: False}
    projected = project_cuts([(0, 1, 2)], decisions)
    assert projected == [([1, 2], 2)]


def test_project_cuts_skips_fully_decided_satisfied_cut():
    # Alle Mitglieder der Deckung entschieden, keiner aufgenommen -> Restriktion ist
    # trivial erfüllt, wird nicht mehr aufgeführt.
    decisions = {0: False, 1: False, 2: False}
    projected = project_cuts([(0, 1, 2)], decisions)
    assert projected == []


def test_solve_node_lp_returns_full_length_x_with_fixed_values_baked_in():
    instance = KnapsackInstance(weights=(2, 3, 4, 5), values=(3, 4, 5, 6), capacity=5, correlation=0.0)
    order = (0, 1, 2, 3)
    decisions = {0: True}
    x, bound = solve_node_lp(instance, order, 1, instance.capacity - 2, decisions, cuts=())
    assert len(x) == instance.n_items
    assert x[0] == 1.0
    assert bound >= 3  # mindestens der bereits sichere Wert von Paket 0
