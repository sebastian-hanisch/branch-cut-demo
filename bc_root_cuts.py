"""Wurzel-Schnitte finden - Phase 1 von Branch & Cut, identisch zum Verfahren aus
cutting-planes-demo/cp_solver.py, hier über bc_lp.solve_node_lp mit depth=0 und
leeren Entscheidungen aufgerufen (der Wurzelfall der verallgemeinerten Knoten-LP)."""

from dataclasses import dataclass

from bc_constants import EPS, MAX_CUT_ITERATIONS
from bc_cuts import find_violated_cover
from bc_lp import solve_node_lp


def ratio_order(instance):
    return sorted(range(instance.n_items), key=lambda i: instance.values[i] / instance.weights[i], reverse=True)


@dataclass(frozen=True)
class RootIteration:
    x: tuple
    bound: float
    is_integral: bool
    cover: object
    violation: float


@dataclass
class RootCutResult:
    order: tuple
    iterations: tuple
    cuts: tuple
    reached_integral: bool
    root_bound: float  # Schranke nach der letzten Wurzel-Iteration


def _is_integral(x, eps=EPS):
    return all(min(xi, 1.0 - xi) <= eps for xi in x)


def solve_root_cuts(instance, max_iterations=MAX_CUT_ITERATIONS):
    order = ratio_order(instance)
    cuts = []
    iterations = []

    for _ in range(max_iterations):
        x, bound = solve_node_lp(instance, order, 0, instance.capacity, {}, cuts)
        if x is None:
            # An der Wurzel ist nichts fixiert - ein projizierter Schnitt kann hier
            # nie verletzt sein, das darf nie passieren.
            raise RuntimeError("Wurzel-LP unerwartet unzulässig")

        if _is_integral(x):
            iterations.append(RootIteration(x, bound, True, None, 0.0))
            break

        cover = find_violated_cover(instance, x, set(cuts))
        if cover is None:
            iterations.append(RootIteration(x, bound, False, None, 0.0))
            break

        violation = sum(x[i] for i in cover) - (len(cover) - 1)
        iterations.append(RootIteration(x, bound, False, cover, violation))
        cuts.append(cover)

    last = iterations[-1]
    return RootCutResult(
        order=tuple(order),
        iterations=tuple(iterations),
        cuts=tuple(cuts),
        reached_integral=last.is_integral,
        root_bound=last.bound,
    )
