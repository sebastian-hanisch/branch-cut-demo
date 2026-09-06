"""Kennzahlen aus einem Branch-&-Cut-Suchlauf, plus der Drei-Wege-Vergleich
(schwache Bound / reine LP-Bound / LP+Schnitte-Bound), die Erweiterung von
branch-bound-demo's bestehendem Zwei-Wege-Bound-Vergleich."""

from collections import Counter

from bc_bounds import lp_bound, weak_bound
from bc_constants import MAX_NODES_EXPLORED, MAX_NODES_EXPLORED_COMPARISON
from bc_root_cuts import solve_root_cuts
from bc_solver import solve, solve_from_root_cuts


def compute_stats(result, instance):
    counts = Counter(node.status for node in result.nodes)
    full_tree_nodes = 2 ** (instance.n_items + 1) - 1
    nodes_explored = len(result.nodes)
    return {
        "nodes_explored": nodes_explored,
        "full_tree_nodes": full_tree_nodes,
        "fraction_of_tree_explored": nodes_explored / full_tree_nodes,
        "pruned_bound": counts["prune_bound"],
        "pruned_infeasible": counts["prune_infeasible"],
        "branch_nodes": counts["branch"] + counts["root"],
        "leaves_evaluated": counts["leaf_new_best"] + counts["leaf_not_best"],
        "best_value": result.best_value,
        "truncated": result.truncated,
    }


def stats_up_to_step(result, step):
    counts = Counter(node.status for node in result.nodes if node.id <= step)
    current_best = 0
    for nid, v in result.incumbent_history:
        if nid <= step:
            current_best = v
    return {
        "nodes_so_far": counts.total(),
        "pruned_bound": counts["prune_bound"],
        "pruned_infeasible": counts["prune_infeasible"],
        "current_best": current_best,
    }


def three_way_bound_comparison(instance, max_nodes=MAX_NODES_EXPLORED, max_nodes_comparison=MAX_NODES_EXPLORED_COMPARISON):
    """Löst dieselbe Instanz mit allen drei Schranken - weak_bound/lp_bound ohne
    jeden Schnitt, cut_bound mit den tatsächlich an der Wurzel gefundenen Schnitten -
    und vergleicht die benötigten Knotenzahlen. weak_bound/lp_bound bekommen die
    großzügigere Grenze (reine Arithmetik, kein LP-Aufruf pro Knoten) - sonst würde
    die absichtlich schlechtere schwache Bound künstlich früh abgeschnitten."""
    root_result = solve_root_cuts(instance)
    weak_result = solve(instance, weak_bound, cuts=(), max_nodes=max_nodes_comparison)
    lp_result = solve(instance, lp_bound, cuts=(), max_nodes=max_nodes_comparison)
    cut_result = solve_from_root_cuts(instance, root_result, max_nodes=max_nodes)
    return {
        "root": root_result,
        "weak": weak_result,
        "lp": lp_result,
        "cut": cut_result,
        "weak_stats": compute_stats(weak_result, instance),
        "lp_stats": compute_stats(lp_result, instance),
        "cut_stats": compute_stats(cut_result, instance),
    }
