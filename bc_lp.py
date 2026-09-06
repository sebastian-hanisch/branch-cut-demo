"""LP-Solver-Wrapper, der cutting-planes-demo/cp_lp.py verallgemeinert: löst nicht
mehr nur die Wurzel-LP, sondern die LP-Relaxierung an einem BELIEBIGEN Suchbaum-
Knoten - über die noch unentschiedenen Pakete, unter Kapazität UND allen
Wurzel-Schnitten, projiziert auf die bereits fixierten Entscheidungen dieses Knotens.
`depth=0, decisions={}` ist exakt der Wurzelfall aus cutting-planes-demo."""

from scipy.optimize import linprog


def project_cuts(cuts, decisions):
    """Projiziert jeden Schnitt sum_{i in C} x_i <= |C|-1 auf die noch freien
    Pakete in C, unter Berücksichtigung der bereits fixierten x_i. Gibt eine Liste
    (freie_pakete_in_C, angepasste_rhs) zurück - oder None, wenn ein Schnitt allein
    durch die fixierten Entscheidungen bereits verletzt ist (rhs < 0), was den
    gesamten Knoten unzulässig macht, ohne dass überhaupt eine LP gelöst werden
    müsste."""
    projected = []
    for cover in cuts:
        fixed_sum = sum(1 for i in cover if decisions.get(i) is True)
        free_in_cover = [i for i in cover if i not in decisions]
        rhs = (len(cover) - 1) - fixed_sum
        if rhs < 0:
            return None
        if free_in_cover:  # nichts zu tun, falls der Schnitt bereits vollständig entschieden ist
            projected.append((free_in_cover, rhs))
    return projected


def solve_node_lp(instance, order, depth, remaining_capacity, decisions, cuts):
    """x ist immer vollständig über ALLE Pakete (natürliche Reihenfolge) angegeben -
    fixierte Pakete mit ihrem entschiedenen 0/1-Wert, freie mit ihrem LP-Wert. Gibt
    (None, None) zurück, wenn der Knoten allein durch einen Schnitt unzulässig ist."""
    n = instance.n_items
    free_items = list(order[depth:])

    projected = project_cuts(cuts, decisions)
    if projected is None:
        return None, None

    x_full = [0.0] * n
    for i, take in decisions.items():
        x_full[i] = 1.0 if take else 0.0
    fixed_value = sum(instance.values[i] for i, take in decisions.items() if take)

    if not free_items:
        return tuple(x_full), fixed_value

    n_free = len(free_items)
    index_of = {item: pos for pos, item in enumerate(free_items)}
    c = [-instance.values[i] for i in free_items]
    a_ub = [[instance.weights[i] for i in free_items]]
    b_ub = [float(remaining_capacity)]
    for free_in_cut, rhs in projected:
        row = [0.0] * n_free
        for i in free_in_cut:
            row[index_of[i]] = 1.0
        a_ub.append(row)
        b_ub.append(float(rhs))

    result = linprog(c, A_ub=a_ub, b_ub=b_ub, bounds=[(0, 1)] * n_free, method="highs")
    if not result.success:
        return None, None

    lp_value = 0.0
    for i, xi in zip(free_items, result.x):
        x_full[i] = float(xi)
        lp_value += instance.values[i] * xi

    return tuple(x_full), fixed_value + lp_value
