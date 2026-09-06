"""
Branch & Cut am Rucksackproblem – interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Viertes Stück der "Konzepte"-Reihe, Exakte-Suche-Linie - und die erste KONVERGENZ
dieser Linie: kombiniert das Verzweigen aus branch-bound-demo mit den Schnitten aus
cutting-planes-demo zum echten Branch & Cut, dem Verfahren, das reale Solver (CPLEX,
Gurobi) tatsächlich einsetzen.

Lauffähig mit: streamlit run app.py
"""

import time

import streamlit as st

import bc_constants as C
from bc_bruteforce import solve_bruteforce
from bc_evaluation import stats_up_to_step, three_way_bound_comparison
from bc_presets import (
    apply_preset,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sync_query_params,
)
from bc_root_cuts import solve_root_cuts
from bc_scenario import generate_instance
from bc_solver import solve_from_root_cuts
from bc_visualization import build_tree_figure

st.set_page_config(page_title="Branch & Cut – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _compute_solve(n_items, capacity_fraction, correlation, seed):
    instance = generate_instance(n_items, capacity_fraction, correlation, seed)
    root = solve_root_cuts(instance)
    result = solve_from_root_cuts(instance, root)
    true_optimum, _true_selection = solve_bruteforce(instance)
    return instance, root, result, true_optimum


@st.cache_data(show_spinner=False)
def _compute_comparison(n_items, capacity_fraction, correlation, seed):
    instance = generate_instance(n_items, capacity_fraction, correlation, seed)
    return three_way_bound_comparison(instance)


st.title("🌳✂️ Branch & Cut am Rucksackproblem")
st.markdown(
    """
Die erste **Konvergenz** der Exakte-Suche-Linie: dasselbe 0/1-Rucksackproblem, aber
jetzt beide bisherigen Mechanismen zusammen - **Branch & Cut** schärft zunächst die
LP-Relaxierung an der Wurzel mit Schnittebenen (wie in
[cutting-planes-demo](https://github.com/sebastian-hanisch/cutting-planes-demo)),
und verzweigt danach einen Suchbaum (wie in
[branch-bound-demo](https://github.com/sebastian-hanisch/branch-bound-demo)) - aber
mit der geschärften Schranke statt der einfachen LP-Relaxierung. Genau **wie** das
zusammenspielt, erklärt der aufgeklappte Abschnitt direkt darunter.
"""
)
st.caption(
    "Anders als die Fall-Demos im Portfolio, die an einem Anwendungsfall mehrere Verfahren "
    "vergleichen, zeigt diese Demo - wie die übrigen drei Stücke der Exakte-Suche-Linie - "
    "ein wachsendes Beispiel. Diesmal aber keine Fortsetzung EINES Vorgängers, sondern die "
    "Konvergenz von zweien: **branch-bound-demo** UND **cutting-planes-demo** kommen hier "
    "zusammen, genau wie HDBSCAN in der Clustering-Linie zwei eigenständige Vorläufer vereint."
)

with st.expander("So funktioniert Branch & Cut", expanded=True):
    st.markdown(
        r"""
Branch & Cut läuft in zwei Phasen ab:

1. **Schnitte an der Wurzel** (exakt der Ablauf aus cutting-planes-demo): LP lösen,
   ganzzahlig? Dann fertig, ganz ohne Verzweigung. Sonst eine verletzte Deckung
   suchen, als Schnitt hinzufügen, wiederholen - bis entweder Ganzzahligkeit erreicht
   ist oder keine weitere verletzte Deckung mehr gefunden wird.
2. **Verzweigen ab der geschärften Wurzel** (wie in branch-bound-demo): Paket für
   Paket, "aufgenommen" vor "ausgelassen". Der einzige Unterschied: die Schranke an
   jedem Knoten löst jetzt eine LP über die noch offenen Pakete, unter Kapazität
   **und** allen Wurzel-Schnitten - dadurch bricht sie öfter und früher ab als
   branch-bound-demos einfache LP-Schranke.

**Bewusste Vereinfachung, diese Demo eigene ehrliche Schwäche**: die Schnitte werden
nur **einmal an der Wurzel** gesucht ("Cut-and-Branch"), nicht an jedem einzelnen
Suchbaum-Knoten neu ("vollständiges" Branch & Cut, wie es reale Solver einsetzen).
Tiefere Knoten könnten von frischen, lokal generierten Schnitten profitieren, die
diese Demo nie findet - der Preis für einen deutlich einfacheren, schnelleren Ablauf.

**Ein Ergebnis, das man zunächst nicht erwarten würde**: man könnte vermuten, dass
ein Schnitt an einem tieferen Knoten einen KOMPLETT NEUEN Grund liefert, den Knoten
abzuschneiden ("dieser Schnitt ist hier schon verletzt"). Das passiert bei dieser
Verzweigungsreihenfolge aber nie - sobald alle Pakete einer Deckung ausgewählt
wären, hat der gewöhnliche Kapazitäts-Check (wie in branch-bound-demo) den Knoten
schon vorher abgeschnitten. Der eigentliche Nutzen der Schnitte liegt woanders: eine
**schärfere Schranke an jedem einzelnen Knoten**, die den bestehenden
Bound-Pruning-Mechanismus viel öfter greifen lässt. Siehe
"📐 Mathematische Formulierung" für den Beweis.
        """
    )

st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
PRESET_HELP = {
    "Schnitte reichen bereits vollständig (kein Branchen nötig)": "5 Pakete - ein einziger Wurzel-Schnitt macht die LP-Lösung bereits ganzzahlig, Phase 2 hat nur den Wurzelknoten.",
    "Schnitte allein reichten nicht (hier reicht wenig Branchen)": "Dieselbe Instanz wie cutting-planes-demos Härtefall - dort blieb eine Lücke offen, hier schließt sie ein winziger Restbaum.",
    "Stark korrelierte Instanz (auch hier nicht spurlos)": "branch-bound-demos eigener Härtefall - auch Branch & Cut braucht hier spürbar mehr Knoten als die anderen Presets, nur weniger als reines Branch & Bound.",
}
preset_cols = st.columns(len(C.PRESETS))
for i, name in enumerate(C.PRESETS.keys()):
    with preset_cols[i]:
        st.button(name, use_container_width=True, on_click=apply_preset, args=(name,), help=PRESET_HELP[name])

st.caption(
    "🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, "
    "um ein Szenario zu teilen."
)

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    n_items = st.slider("Anzahl Pakete", *bounds("n_items_slider"), key="n_items_slider")
    capacity_fraction = st.slider(
        "Gewichtslimit (Anteil der Gesamtmenge)", *bounds("capacity_fraction_slider"), key="capacity_fraction_slider"
    )
    correlation = st.slider(
        "Korrelation Wert/Gewicht", *bounds("correlation_slider"), key="correlation_slider",
        help="0 = Wert unabhängig vom Gewicht. 1 = wertvolle Pakete sind auch die schweren "
        "(branch-bound-demos Härtefall) - auch Branch & Cut wird davon nicht verschont, nur "
        "weniger hart getroffen als reines Branch & Bound.",
    )
    seed = st.number_input("Zufalls-Seed", *bounds("seed_input"), key="seed_input", step=1)

    st.button(
        "🎲 Neue Instanz generieren",
        use_container_width=True,
        on_click=randomize_seed,
        help="Würfelt einen neuen Zufalls-Seed für Paketgewichte und -werte.",
    )

sync_query_params(n_items, capacity_fraction, correlation, seed)

scenario_key = (int(n_items), capacity_fraction, correlation, int(seed))

with st.spinner("Schneide an der Wurzel, dann verzweige..."):
    instance, root, result, true_optimum = _compute_solve(*scenario_key)

st.markdown("## ✂️ Phase 1: Schnitte an der Wurzel")
rc1, rc2, rc3 = st.columns(3)
rc1.metric(
    "Schnitte gefunden", f"{len(root.cuts):,}",
    help="Genau der Ablauf aus cutting-planes-demo, hier als kompakte Zusammenfassung statt "
    "vollständigem Replay - das volle Schritt-für-Schritt-Erlebnis zeigt cutting-planes-demo "
    "selbst.",
)
rc2.metric(
    "Wurzel-Schranke", f"{root.root_bound:.2f}",
    help="Die LP-Schranke nach allen an der Wurzel gefundenen Schnitten - der Startpunkt für "
    "Phase 2.",
)
rc3.metric(
    "Bereits ganzzahlig?", "Ja ✅" if root.reached_integral else "Nein",
    help="Ja bedeutet: die Schnitte allein reichten bereits zum bewiesenen Optimum, Phase 2 "
    "verzweigt dann gar nicht erst.",
)
if root.reached_integral:
    st.success("✅ Schnitte allein reichten bis zum bewiesenen Optimum - der Suchbaum unten hat nur die Wurzel.")

st.markdown("---")

st.markdown("## 🎯 Phase 2: Der Suchbaum ab der geschärften Wurzel")

if "bc_step" not in st.session_state or st.session_state.get("bc_step_owner") != scenario_key:
    st.session_state["bc_step"] = len(result.nodes) - 1
    st.session_state["bc_step_owner"] = scenario_key

max_step = len(result.nodes) - 1
step_col, play_col = st.columns([5, 1])
with step_col:
    if max_step == 0:
        step = 0
        st.caption("Nur der (bereits geschärfte) Wurzelknoten - kein Regler nötig.")
    else:
        step = st.slider(
            "Schritt (Knoten)", 0, max_step, key="bc_step",
            help="Ein Schritt = ein besuchter Suchbaum-Knoten, in Besuchsreihenfolge.",
        )
with play_col:
    auto_play = st.button("▶️ Abspielen", use_container_width=True)

render_note = (
    f" (zeigt die ersten {C.MAX_NODES_RENDERED:,} von {len(result.nodes):,} Knoten)"
    if len(result.nodes) > C.MAX_NODES_RENDERED
    else ""
)
st.caption(f"{len(result.nodes):,} Knoten insgesamt besucht{render_note}.")

tree_slot = st.empty()


def _render(current_step):
    tree_slot.plotly_chart(
        build_tree_figure(instance, result, current_step, C.MAX_NODES_RENDERED),
        use_container_width=True, key=f"tree_{current_step}",
    )


if auto_play:
    n_frames = min(max_step + 1, 60)
    frame_skip = max(1, (max_step + 1) // n_frames)
    for s in list(range(0, max_step, frame_skip)) + [max_step]:
        _render(s)
        time.sleep(0.08)
    step = max_step
else:
    _render(step)

live = stats_up_to_step(result, step)
lm1, lm2, lm3, lm4 = st.columns(4)
lm1.metric("Besuchte Knoten (bisher)", f"{live['nodes_so_far']:,}")
lm2.metric(
    "Gestutzt (Bound)", f"{live['pruned_bound']:,}",
    help="Dank der Schnitte schärfer als branch-bound-demos einfache LP-Schranke - greift "
    "dadurch öfter und früher.",
)
lm3.metric("Gestutzt (zu schwer)", f"{live['pruned_infeasible']:,}")
lm4.metric("Bester Fund bisher", live["current_best"])

if result.truncated:
    st.error(
        f"⛔ Abgebrochen bei {C.MAX_NODES_EXPLORED:,} untersuchten Knoten - das gezeigte "
        f"Ergebnis ist die beste bislang gefundene, nicht garantiert optimale Lösung."
    )
else:
    st.caption(
        f"Bewiesenes Optimum: **{result.best_value}** - stimmt mit der unabhängigen "
        f"Bruteforce-Referenz überein ({true_optimum})."
        if result.best_value == true_optimum
        else f"⚠️ Optimum {result.best_value} weicht von der Bruteforce-Referenz {true_optimum} ab - bitte melden."
    )

st.markdown("---")

st.subheader("📐 Wie viel bringt die Kombination wirklich?")
st.markdown(
    """
Live für Ihre aktuelle Instanz: dieselbe Suche, dreimal mit unterschiedlich scharfer
Schranke - schwach (ignoriert das Gewichtslimit), rein LP-basiert (wie in
branch-bound-demo) und LP mit Wurzel-Schnitten (diese Demo).
"""
)

cmp = _compute_comparison(*scenario_key)
cc1, cc2, cc3 = st.columns(3)
cc1.metric(
    "Schwache Bound", f"{cmp['weak_stats']['nodes_explored']:,} Knoten" + (" (abgebrochen)" if cmp["weak_stats"]["truncated"] else ""),
    help="Ignoriert das Gewichtslimit komplett - gültig, aber sehr locker.",
)
cc2.metric(
    "LP-Bound (branch-bound-demo)", f"{cmp['lp_stats']['nodes_explored']:,} Knoten",
    delta=f"{cmp['lp_stats']['nodes_explored'] - cmp['weak_stats']['nodes_explored']:,} ggü. schwach",
    delta_color="inverse",
    help="Dieselbe LP-Relaxierungs-Schranke wie in branch-bound-demo, ohne jeden Schnitt.",
)
cc3.metric(
    "LP + Wurzel-Schnitte (Branch & Cut)", f"{cmp['cut_stats']['nodes_explored']:,} Knoten",
    delta=f"{cmp['cut_stats']['nodes_explored'] - cmp['lp_stats']['nodes_explored']:,} ggü. LP",
    delta_color="inverse",
    help="Dieselbe LP-Schranke, zusätzlich verschärft durch die an der Wurzel gefundenen "
    "Schnitte - kann nie mehr Knoten brauchen als die reine LP-Bound.",
)

lp_nodes = cmp["lp_stats"]["nodes_explored"]
cut_nodes = cmp["cut_stats"]["nodes_explored"]
if lp_nodes > 0 and cut_nodes < lp_nodes:
    factor = lp_nodes / cut_nodes if cut_nodes else float("inf")
    st.success(
        f"✅ Die Wurzel-Schnitte allein senken die benötigte Knotenzahl um den Faktor "
        f"**{factor:.1f}×** gegenüber der reinen LP-Bound aus branch-bound-demo - für "
        f"dasselbe bewiesene Optimum."
    )
else:
    st.info(
        "ℹ️ Bei dieser Instanz halfen die Wurzel-Schnitte kaum oder gar nicht (kein oder fast "
        "kein Schnitt gefunden) - probieren Sie ein Preset mit mehr Paketen oder anderer "
        "Korrelation."
    )

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Schnitt-Projektion auf einen Suchbaum-Knoten**: an einem Knoten mit bereits
fixierten Entscheidungen (Paket $i$ auf $d_i \in \{0,1\}$ festgelegt für
$i \in F$) wird jeder Wurzel-Schnitt $\sum_{i \in C} x_i \le |C|-1$ projiziert:

$$
\sum_{i \in C \setminus F} x_i \;\le\; \underbrace{(|C|-1) - \sum_{i \in C \cap F} d_i}_{\text{rhs}'}
$$

Nur die noch **freien** Pakete aus $C$ tauchen in der projizierten Restriktion auf,
die rechte Seite schrumpft um die Anzahl bereits aufgenommener $C$-Pakete.

**Warum $\text{rhs}' < 0$ bei dieser Verzweigungsreihenfolge nie vorkommt**: das
würde $\sum_{i \in C \cap F} d_i \ge |C|$ bedeuten - also ALLE Pakete aus $C$ bereits
aufgenommen. Da $C$ per Definition eine Deckung ist ($\sum_{i \in C} w_i > W$), hätte
der gewöhnliche Kapazitäts-Check (identisch zu branch-bound-demo) den Knoten schon
beim letzten dieser Pakete als "Gestutzt (zu schwer)" abgeschnitten - lange bevor
`cut_bound` überhaupt aufgerufen wird. `bc_bounds.cut_bound` prüft genau das als
Invariante (nicht als normaler Codepfad) und schlägt laut Alarm, sollte sie je
verletzt werden.

**Der eigentliche Nutzen der Schnitte** liegt also nicht in einem neuen
Pruning-Grund, sondern darin, dass die LP-Schranke an JEDEM Knoten enger wird -
der bestehende "Gestutzt (Bound)"-Mechanismus aus branch-bound-demo greift dadurch
insgesamt viel öfter.

**Cut-and-Branch vs. vollständiges Branch & Cut**: diese Demo sucht Schnitte nur
einmal an der Wurzel. Reale Solver generieren an tieferen Knoten oft neue,
lokal gültige Schnitte - mehr Pruning-Potenzial, aber ein LP-Solver-Aufruf plus
Trennungsheuristik pro Knoten statt nur an der Wurzel. Diese Demos eigene,
bewusst in Kauf genommene Schwäche.

Implementiert in `bc_root_cuts.py` (Phase 1), `bc_lp.py` (Schnitt-Projektion +
Knoten-LP), `bc_bounds.py` (die drei Schranken) und `bc_solver.py`
(Tiefensuche, direkte Portierung von branch-bound-demo/bb_solver.py).
        """
    )

st.markdown("---")

st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning. Interesse an einer maßgeschneiderten Lösung für "
    "Ihr Unternehmen? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html)"
)
