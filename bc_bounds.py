"""Drei Schranken-Funktionen, gemeinsame Signatur
`bound_fn(instance, order, depth, remaining_capacity, current_value, decisions, cuts)`
- so kann bc_solver.solve() alle drei austauschbar verwenden, für den
Drei-Wege-Vergleich in bc_evaluation.py.

`weak_bound`/`lp_bound` ignorieren `decisions`/`cuts` (1:1 die Formeln aus
branch-bound-demo/bb_bound.py)."""

from bc_lp import solve_node_lp


def weak_bound(instance, order, depth, remaining_capacity, current_value, decisions, cuts):
    return current_value + sum(instance.values[idx] for idx in order[depth:])


def lp_bound(instance, order, depth, remaining_capacity, current_value, decisions, cuts):
    bound = current_value
    capacity = remaining_capacity
    for idx in order[depth:]:
        w, v = instance.weights[idx], instance.values[idx]
        if w <= capacity:
            capacity -= w
            bound += v
        else:
            bound += v * (capacity / w)
            break
    return bound


def cut_bound(instance, order, depth, remaining_capacity, current_value, decisions, cuts):
    x, bound = solve_node_lp(instance, order, depth, remaining_capacity, decisions, cuts)
    if x is None:
        # Mathematisch unerreichbar bei dieser Verzweigungsreihenfolge (siehe
        # bc_solver.py's Modul-Docstring und die "Mathematische Formulierung" in
        # app.py): sobald alle Pakete einer Deckung ausgewählt wären, hätte bereits
        # der gewöhnliche Kapazitäts-Check den Knoten als prune_infeasible
        # abgeschnitten, bevor cut_bound überhaupt aufgerufen wird. Eine Assertion
        # statt eines stillen Sonderfalls, damit ein Verstoß gegen diese Invariante
        # (z. B. durch eine künftige Änderung der Verzweigungsreihenfolge) laut
        # auffällt statt sich als falsches Ergebnis zu verstecken.
        raise AssertionError(
            "cut_bound: ein Schnitt wurde allein durch bereits fixierte Entscheidungen "
            "verletzt - das sollte bei include-vor-exclude-Verzweigung unmöglich sein, "
            "da der Kapazitäts-Check eine vollständig ausgewählte Deckung immer zuerst abfängt."
        )
    return bound
