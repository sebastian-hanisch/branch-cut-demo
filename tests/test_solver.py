import pytest

from bc_bounds import cut_bound, lp_bound, weak_bound
from bc_bruteforce import solve_bruteforce
from bc_constants import PRESETS
from bc_evaluation import compute_stats
from bc_root_cuts import solve_root_cuts
from bc_scenario import KnapsackInstance, generate_instance
from bc_solver import solve, solve_from_root_cuts


def _solve_with_cuts(instance):
    root = solve_root_cuts(instance)
    return solve_from_root_cuts(instance, root), root


def test_matches_hand_computed_tiny_instance():
    instance = KnapsackInstance(weights=(2, 3, 4, 5), values=(3, 4, 5, 6), capacity=5, correlation=0.0)
    result, _root = _solve_with_cuts(instance)
    assert result.best_value == 7
    assert result.best_selection == (True, True, False, False)


def test_matches_bruteforce_across_random_small_instances():
    for seed in range(30):
        instance = generate_instance(n_items=9, capacity_fraction=0.5, correlation=seed % 5 / 4, seed=seed)
        result, _root = _solve_with_cuts(instance)
        true_best, _ = solve_bruteforce(instance)
        assert result.best_value == true_best, f"seed={seed}"
        weight = sum(w for w, take in zip(instance.weights, result.best_selection) if take)
        assert weight <= instance.capacity


def test_cut_bound_invariant_never_raises_across_many_instances():
    # cut_bound raises AssertionError if a root cut is ever violated by fixed
    # decisions alone - siehe bc_bounds.py. Das sollte bei include-vor-exclude-
    # Verzweigung strukturell unmöglich sein (der Kapazitäts-Check fängt eine
    # vollständig ausgewählte Deckung immer zuerst ab). Dieser Test läuft über eine
    # breite Mischung aus Größen/Korrelationen als empirischer Beleg dieser
    # Invariante - kein einziger Aufruf darf die Assertion auslösen.
    for n in (4, 6, 9, 12, 15):
        for seed in range(8):
            instance = generate_instance(n_items=n, capacity_fraction=0.5, correlation=seed % 5 / 4, seed=seed)
            _solve_with_cuts(instance)  # wirft, falls die Invariante verletzt wird


def test_three_way_node_count_ordering():
    # cut_bound schärfer als lp_bound (Schnitte können die LP nur einschränken, nie
    # lockern), lp_bound schärfer als weak_bound - also in dieser Reihenfolge nie
    # mehr Knoten, analog zu branch-bound-demos bestehendem Zwei-Wege-Test.
    for seed in range(15):
        instance = generate_instance(n_items=10, capacity_fraction=0.5, correlation=0.3, seed=seed)
        root = solve_root_cuts(instance)
        cut_result = solve_from_root_cuts(instance, root)
        lp_result = solve(instance, lp_bound, cuts=())
        weak_result = solve(instance, weak_bound, cuts=())
        assert len(cut_result.nodes) <= len(lp_result.nodes), f"seed={seed}"
        assert len(lp_result.nodes) <= len(weak_result.nodes), f"seed={seed}"


def test_root_node_bound_matches_root_cuts_final_bound():
    # Der Wurzelknoten des Suchbaums (mit cut_bound + den Wurzel-Schnitten) muss
    # exakt dieselbe Schranke liefern wie bc_root_cuts.solve_root_cuts's letzte
    # Iteration - beide lösen dieselbe LP mit denselben Schnitten, ohne fixierte
    # Entscheidungen.
    for seed in range(10):
        instance = generate_instance(n_items=8, capacity_fraction=0.5, correlation=0.4, seed=seed)
        root = solve_root_cuts(instance)
        result = solve(instance, cut_bound, cuts=root.cuts)
        root_node = result.nodes[0]
        assert root_node.status == "root"
        assert root_node.bound == pytest.approx(root.root_bound, abs=1e-6)


def test_root_already_integral_shortcuts_to_a_single_node():
    # Ohne den Kurzschluss in solve_from_root_cuts würde solve() trotz bereits
    # ganzzahliger Wurzel-LP blind bis zu den Blättern hinabsteigen (das einfache
    # bound<=best-Pruning kennt "die LP-Lösung ist schon ganzzahlig" nicht) - genau
    # das wurde per Zeitmessung entdeckt, bevor "Schnitte reichen, kein Branchen
    # nötig" als falsche Behauptung in der App gelandet wäre.
    found_one = False
    for seed in range(30):
        instance = generate_instance(n_items=8, capacity_fraction=0.5, correlation=seed % 5 / 4, seed=seed)
        root = solve_root_cuts(instance)
        if not root.reached_integral:
            continue
        found_one = True
        result = solve_from_root_cuts(instance, root)
        assert len(result.nodes) == 1
        assert result.nodes[0].status == "root"
        true_best, _ = solve_bruteforce(instance)
        assert result.best_value == true_best
    assert found_one, "kein Seed mit reached_integral=True gefunden - Testdaten anpassen"


def test_max_nodes_cap_is_honored_and_flagged_as_truncated():
    instance = generate_instance(n_items=15, capacity_fraction=0.5, correlation=0.9, seed=1)
    result = solve(instance, weak_bound, cuts=(), max_nodes=50)
    assert len(result.nodes) <= 50 + 2
    assert result.truncated


@pytest.mark.parametrize("name", list(PRESETS.keys()))
def test_presets_solve_correctly(name):
    instance = generate_instance(**PRESETS[name])
    result, _root = _solve_with_cuts(instance)
    true_best, _ = solve_bruteforce(instance)
    assert result.best_value == true_best
