"""Defaults, slider bounds und Presets für die Branch-&-Cut-Demo."""

DEFAULT_N_ITEMS = 6
DEFAULT_CAPACITY_FRACTION = 0.5
DEFAULT_CORRELATION = 0.0
DEFAULT_SEED = 7

N_ITEMS_MIN, N_ITEMS_MAX = 3, 18
CAPACITY_FRACTION_MIN, CAPACITY_FRACTION_MAX = 0.2, 0.8
CORRELATION_MIN, CORRELATION_MAX = 0.0, 1.0

WEIGHT_RANGE = (5, 30)
VALUE_BASE_RANGE = (5, 30)
VALUE_NOISE_RANGE = (-8, 8)

EPS = 1e-6

# Wurzelphase (Schnitte) - wie in cutting-planes-demo.
MAX_CUT_ITERATIONS = 30

# Suchbaum-Phase mit cut_bound (löst pro Knoten ein LP via scipy, deutlich teurer
# als eine geschlossene Formel) - Stresstest über ~170 Instanzen (n=16-18, Korrelation
# 0.5-0.95) ergab maximal 665 Knoten / 0.33s; 5.000 lässt reichlich Sicherheitsabstand,
# bleibt aber selbst im Extremfall unter ~5s.
MAX_NODES_EXPLORED = 5_000
MAX_NODES_RENDERED = 800

# Nur für weak_bound/lp_bound im Drei-Wege-Vergleich (bc_evaluation.py) - beide sind
# reine Arithmetik ohne LP-Aufruf, genauso günstig pro Knoten wie in
# branch-bound-demo, daher derselbe großzügige Wert wie dort. Getrennt von
# MAX_NODES_EXPLORED, damit die schwache Bound (die absichtlich viel mehr Knoten
# braucht) im Vergleich nicht künstlich früh abgeschnitten wird.
MAX_NODES_EXPLORED_COMPARISON = 200_000

PRESETS = {
    "Schnitte reichen bereits vollständig (kein Branchen nötig)": {
        "n_items": 5, "capacity_fraction": 0.5, "correlation": 0.0, "seed": 6,
    },
    "Schnitte allein reichten nicht (hier reicht wenig Branchen)": {
        "n_items": 4, "capacity_fraction": 0.5, "correlation": 0.0, "seed": 4,
    },
    "Stark korrelierte Instanz (auch hier nicht spurlos)": {
        "n_items": 17, "capacity_fraction": 0.5, "correlation": 0.95, "seed": 3,
    },
}
