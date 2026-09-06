"""Depth-first Branch & Bound, direkte Portierung von branch-bound-demo/bb_solver.py,
erweitert um ein `decisions`-Dict, das pro Knoten mitgeführt und an die
Schranken-Funktion durchgereicht wird, sowie `cuts` (leer für weak_bound/lp_bound,
die tatsächlichen Wurzel-Schnitte für cut_bound) - siehe bc_bounds.py.

Bewusst KEIN neuer Knoten-Status für "durch Schnitt unzulässig": das wäre zwar
naheliegend, ist aber unmöglich bei dieser Verzweigungsreihenfolge - sobald alle
Pakete einer Deckung ausgewählt sind, überschreitet das Gewicht bereits die
Kapazität, der Knoten wäre also schon vorher als `prune_infeasible` abgeschnitten
worden (siehe bc_bounds.cut_bound für die dazugehörige Prüfung als Invariante, nicht
als normaler Codepfad, und 📐 Mathematische Formulierung in app.py für den Beweis)."""

from dataclasses import dataclass

from bc_constants import MAX_NODES_EXPLORED
from bc_root_cuts import ratio_order


@dataclass(frozen=True)
class Node:
    id: int
    parent_id: int
    depth: int
    item_index: int  # None für die Wurzel
    decision: bool  # True = aufgenommen, False = ausgelassen, None für die Wurzel
    weight: int
    value: int
    bound: float  # None für prune_infeasible-Knoten (keine Schranke berechnet)
    status: str  # root | branch | prune_bound | prune_infeasible | leaf_new_best | leaf_not_best


@dataclass(frozen=True)
class SolveResult:
    best_value: int
    best_selection: tuple
    nodes: tuple
    incumbent_history: tuple
    truncated: bool
    order: tuple


def solve(instance, bound_fn, cuts=(), max_nodes=MAX_NODES_EXPLORED):
    order = ratio_order(instance)
    nodes = []
    incumbent_history = []
    best = {"value": 0, "selection": tuple(False for _ in range(instance.n_items))}
    truncated = {"flag": False}
    next_id = [0]

    def new_node(parent_id, depth, item_index, decision, weight, value, bound, status):
        node = Node(next_id[0], parent_id, depth, item_index, decision, weight, value, bound, status)
        next_id[0] += 1
        nodes.append(node)
        return node

    root_bound = bound_fn(instance, order, 0, instance.capacity, 0, {}, cuts)
    root = new_node(None, 0, None, None, 0, 0, root_bound, "root")

    def explore(node, weight, value, decisions):
        depth = node.depth
        item = order[depth]
        w, v = instance.weights[item], instance.values[item]

        for decision in (True, False):
            if truncated["flag"] or len(nodes) >= max_nodes:
                truncated["flag"] = True
                return

            new_weight = weight + (w if decision else 0)
            new_value = value + (v if decision else 0)
            new_depth = depth + 1
            new_decisions = dict(decisions)
            new_decisions[item] = decision

            if decision and new_weight > instance.capacity:
                new_node(node.id, new_depth, item, decision, new_weight, new_value, None, "prune_infeasible")
                continue

            child_bound = bound_fn(
                instance, order, new_depth, instance.capacity - new_weight, new_value, new_decisions, cuts
            )

            if new_depth == instance.n_items:
                is_new_best = new_value > best["value"]
                status = "leaf_new_best" if is_new_best else "leaf_not_best"
                child = new_node(node.id, new_depth, item, decision, new_weight, new_value, child_bound, status)
                if is_new_best:
                    best["value"] = new_value
                    best["selection"] = tuple(new_decisions.get(i, False) for i in range(instance.n_items))
                    incumbent_history.append((child.id, new_value))
                continue

            if child_bound <= best["value"]:
                new_node(node.id, new_depth, item, decision, new_weight, new_value, child_bound, "prune_bound")
                continue

            child = new_node(node.id, new_depth, item, decision, new_weight, new_value, child_bound, "branch")
            explore(child, new_weight, new_value, new_decisions)

    explore(root, 0, 0, {})

    return SolveResult(
        best_value=best["value"],
        best_selection=best["selection"],
        nodes=tuple(nodes),
        incumbent_history=tuple(incumbent_history),
        truncated=truncated["flag"],
        order=tuple(order),
    )


def solve_from_root_cuts(instance, root, max_nodes=MAX_NODES_EXPLORED):
    """Wrapper um `solve()` mit `cut_bound`, der die Wurzel-Schnitte aus
    bc_root_cuts.solve_root_cuts wiederverwendet - UND, falls die Wurzel-LP nach
    diesen Schnitten bereits ganzzahlig ist, gar nicht erst verzweigt: die Lösung
    steht dann bereits fest, kein einziger Suchbaum-Knoten nötig. Ohne diesen
    Kurzschluss würde `solve()` trotzdem blind bis zu den Blättern hinabsteigen (der
    einfache `bound_fn <= best_value`-Pruning-Mechanismus kennt "die LP-Lösung ist
    schon ganzzahlig" nicht, er sieht nur Zahlen) - genau das per Zeitmessung
    entdeckt, bevor es als falsche Behauptung ("Schnitte reichen, kein Branchen
    nötig") in der App gelandet wäre."""
    from bc_bounds import cut_bound

    if root.reached_integral:
        x = root.iterations[-1].x
        selection = tuple(round(xi) == 1 for xi in x)
        value = sum(v for v, take in zip(instance.values, selection) if take)
        root_node = Node(0, None, 0, None, None, 0, value, root.root_bound, "root")
        return SolveResult(
            best_value=value,
            best_selection=selection,
            nodes=(root_node,),
            incumbent_history=((0, value),),
            truncated=False,
            order=root.order,
        )

    return solve(instance, cut_bound, cuts=root.cuts, max_nodes=max_nodes)
