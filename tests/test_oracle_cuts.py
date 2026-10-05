"""Unabhängiges Orakel für Branch & Cut am Rucksack: Optimum per Kapazitäts-DP,
JEDER Wurzel-Schnitt gegen ALLE ganzzahlig zulässigen Punkte (Aufzählung - nie ein
zulässiger Punkt abgeschnitten, jeder Schnitt ist eine echte Deckung), jede
Wurzel- und Knoten-Schranke gegen ein einziges `linprog` mit ALLEN (unprojizierten)
Schnitten und fixierten Variablen (statt Projektion auf die freien Pakete)."""

import itertools

import pytest

scipy_opt = pytest.importorskip("scipy.optimize")

from bc_bounds import lp_bound, weak_bound
from bc_root_cuts import solve_root_cuts
from bc_scenario import generate_instance
from bc_solver import solve, solve_from_root_cuts


def _dp(weights, values, cap):
    best = [0] * (cap + 1)
    for w, v in zip(weights, values):
        for c in range(cap, w - 1, -1):
            best[c] = max(best[c], best[c - w] + v)
    return best[cap]


def _full_lp(inst, cuts, fixed):
    n = inst.n_items
    A, b = [list(map(float, inst.weights))], [float(inst.capacity)]
    for cover in cuts:
        A.append([1.0 if i in cover else 0.0 for i in range(n)])
        b.append(len(cover) - 1.0)
    bounds = [(1, 1) if fixed.get(i) is True else (0, 0) if fixed.get(i) is False else (0, 1) for i in range(n)]
    res = scipy_opt.linprog([-v for v in inst.values], A_ub=A, b_ub=b, bounds=bounds, method="highs")
    return -res.fun


CASES = [(n, cap, corr, seed) for n in (3, 6, 9, 11) for cap in (0.2, 0.5, 0.8) for corr in (0.0, 0.95) for seed in range(2)]


@pytest.mark.parametrize("n_items,cap,corr,seed", CASES)
def test_cuts_valid_bounds_exact_and_optimum_matches(n_items, cap, corr, seed):
    inst = generate_instance(n_items, cap, corr, seed)
    opt = _dp(inst.weights, inst.values, inst.capacity)
    root = solve_root_cuts(inst)

    feasible = [
        sel for sel in itertools.product((0, 1), repeat=n_items)
        if sum(w * s for w, s in zip(inst.weights, sel)) <= inst.capacity
    ]
    for cover in root.cuts:
        assert sum(inst.weights[i] for i in cover) > inst.capacity  # echte Deckung
        for sel in feasible:
            assert sum(sel[i] for i in cover) <= len(cover) - 1  # nie ein zulässiger Punkt abgeschnitten

    previous = None
    for k, it in enumerate(root.iterations):
        assert it.bound == pytest.approx(_full_lp(inst, root.cuts[:k], {}), abs=1e-6)
        assert it.bound >= opt - 1e-6
        assert previous is None or it.bound <= previous + 1e-7
        previous = it.bound

    results = {
        "weak": solve(inst, weak_bound),
        "lp": solve(inst, lp_bound),
        "cut": solve_from_root_cuts(inst, root),
    }
    for name, res in results.items():
        assert res.best_value == opt, name
        assert sum(w for w, t in zip(inst.weights, res.best_selection) if t) <= inst.capacity
    assert len(results["cut"].nodes) <= len(results["lp"].nodes) <= len(results["weak"].nodes)

    if not root.reached_integral:
        by_id = {n.id: n for n in results["cut"].nodes}
        for node in results["cut"].nodes:
            if node.bound is None:
                continue
            decisions, cur = {}, node
            while cur.parent_id is not None:
                decisions[cur.item_index] = cur.decision
                cur = by_id[cur.parent_id]
            assert node.bound == pytest.approx(_full_lp(inst, root.cuts, decisions), abs=1e-6)
