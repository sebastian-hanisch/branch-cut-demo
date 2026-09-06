"""Greedy-Trennungsheuristik - unverändert aus cutting-planes-demo/cp_cuts.py
übernommen, da sich der Mechanismus selbst nicht ändert, nur wo er eingesetzt wird
(hier: einmalig an der Wurzel, siehe bc_root_cuts.py)."""

from bc_constants import EPS


def find_violated_cover(instance, x, existing_covers, eps=EPS):
    n = instance.n_items
    order = sorted(range(n), key=lambda i: x[i], reverse=True)

    cover = []
    total_weight = 0
    for i in order:
        if x[i] <= eps:
            break
        cover.append(i)
        total_weight += instance.weights[i]
        if total_weight > instance.capacity:
            break

    if total_weight <= instance.capacity:
        return None

    cover_set = set(cover)
    for i in sorted(cover, key=lambda i: x[i]):
        if i not in cover_set:
            continue
        trial = cover_set - {i}
        trial_weight = sum(instance.weights[j] for j in trial)
        if trial_weight > instance.capacity:
            cover_set = trial

    cover_final = tuple(sorted(cover_set))
    violation = sum(x[i] for i in cover_final) - (len(cover_final) - 1)
    if violation <= eps or cover_final in existing_covers:
        return None
    return cover_final
