# Branch & Cut am Rucksackproblem – Streamlit-Demo

Viertes Stück der "Konzepte"-Reihe für die Website "Sebastian Hanisch – Operations
Research und Machine Learning", **Exakte-Suche-Linie** - und die erste **Konvergenz**
dieser Linie: kombiniert das Verzweigen aus
[branch-bound-demo](../branch-bound-demo) mit den Schnitten aus
[cutting-planes-demo](../cutting-planes-demo) zum echten Branch & Cut, dem Verfahren,
das reale Solver (CPLEX, Gurobi) tatsächlich einsetzen - dieselbe Rolle wie HDBSCAN in
der Clustering-Linie, nur für die Exakte-Suche-Linie.

## Cut-and-Branch statt vollständigem Branch & Cut

Schnitte werden **einmalig an der Wurzel** gesucht (exakt der Algorithmus aus
`cutting-planes-demo`), danach bleiben sie für den gesamten Suchbaum fix - "Cut-and-
Branch", eine reale, einfachere Variante des vollständigen Branch & Cut (das an jedem
Knoten frische Schnitte generiert). Diese Demo eigene, bewusst in Kauf genommene
Schwäche: tiefere Knoten könnten von neuen, lokal generierten Schnitten profitieren,
die Cut-and-Branch nie findet.

## Ein Ergebnis, das man zunächst nicht erwarten würde

Man könnte vermuten, Schnitte an einem Suchbaum-Knoten liefern einen komplett neuen
Pruning-Grund ("dieser Knoten ist durch einen Schnitt allein schon unzulässig"). Das
ist bei include-vor-exclude-Verzweigung **mathematisch unmöglich**: sobald alle
Pakete einer Deckung ausgewählt wären, hat der gewöhnliche Kapazitäts-Check den
Knoten schon vorher abgeschnitten (siehe `bc_bounds.cut_bound`, das dies als
Invariante prüft, nicht als normalen Codepfad, plus
[tests/test_solver.py](tests/test_solver.py)s empirischer Beleg über viele
Instanzen). Der eigentliche Nutzen der Schnitte: eine **schärfere Schranke an jedem
Knoten**, die den bestehenden Bound-Pruning-Mechanismus aus `branch-bound-demo` viel
öfter greifen lässt.

## Ein zweiter, während der Implementierung gefundener Fehler

Ohne besonderen Kurzschluss würde der Suchbaum trotz einer bereits ganzzahligen
Wurzel-LP (Schnitte allein reichen) blind bis zu den Blättern hinabsteigen - das
einfache `bound <= best_value`-Pruning kennt "die LP-Lösung ist schon ganzzahlig"
nicht, es sieht nur Zahlen. Per Zeitmessung entdeckt (die erste Preset-Instanz zeigte
11 Knoten statt der erwarteten 1), bevor "Schnitte reichen, kein Branchen nötig" als
falsche Behauptung in der App gelandet wäre. Fix: `bc_solver.solve_from_root_cuts`
prüft `root.reached_integral` und liefert in diesem Fall direkt einen Ein-Knoten-Baum
zurück, siehe `tests/test_solver.py::test_root_already_integral_shortcuts_to_a_single_node`.

## Verifikation

- **Bruteforce-Cross-Check**: über alle drei Schranken (schwach, LP, LP+Schnitte).
- **Drei-Wege-Bound-Ordnung**: `cut_bound`-Knotenzahl $\le$ `lp_bound`-Knotenzahl
  $\le$ `weak_bound`-Knotenzahl - Erweiterung von branch-bound-demos bestehendem
  Zwei-Wege-Test.
- **Invarianten-Test**: `cut_bound`s Assertion ("Schnitt allein durch fixierte
  Entscheidungen verletzt") darf über eine breite Mischung an Instanzen nie auslösen.
- **Wurzel-Konsistenz**: der Wurzelknoten des Suchbaums muss exakt dieselbe Schranke
  liefern wie `bc_root_cuts.solve_root_cuts`s letzte Iteration.
- **Kurzschluss-Test**: bei bereits ganzzahliger Wurzel-LP genau ein Knoten, korrekt
  markiert, mit dem richtigen (bruteforce-geprüften) Optimalwert.
- **Sicherheitsgrenzen**: `MAX_NODES_EXPLORED` (5.000, kalibriert per Stresstest über
  ~170 Instanzen, worst case 665 Knoten/0,33s) für die teure `cut_bound`-Suche,
  `MAX_NODES_EXPLORED_COMPARISON` (200.000, wie branch-bound-demo) für die günstigen
  `weak_bound`/`lp_bound`-Vergleichsläufe.

## Dateistruktur

| Datei | Inhalt |
|---|---|
| `app.py` | Streamlit-Hauptablauf: Presets, Einstellungen, Wurzel-Zusammenfassung, Suchbaum-Animation, Drei-Wege-Vergleich, Formulierungs-Expander |
| `bc_constants.py` | Defaults, Regler-Grenzen, Sicherheitsgrenzen, `PRESETS` |
| `bc_presets.py` | `SettingSpec`/`SETTING_SPECS`, Permalink-Logik, Presets, Zufalls-Seed-Button |
| `bc_scenario.py` | Zufällige Rucksack-Instanzen mit einstellbarer Korrelation |
| `bc_lp.py` | Verallgemeinerter LP-Solver-Wrapper (Wurzel- UND Knoten-LP, Schnitt-Projektion) |
| `bc_cuts.py` | Greedy-Trennungsheuristik (unverändert aus cutting-planes-demo) |
| `bc_root_cuts.py` | Phase 1: Wurzel-Schnitte finden |
| `bc_bounds.py` | Drei Schranken: `weak_bound`, `lp_bound`, `cut_bound` |
| `bc_solver.py` | Phase 2: Tiefensuche-Branch-and-Bound, `solve_from_root_cuts` (mit Kurzschluss) |
| `bc_bruteforce.py` | Unabhängige Referenzlösung (vollständige Enumeration) |
| `bc_evaluation.py` | Kennzahlen, Drei-Wege-Bound-Vergleich |
| `bc_visualization.py` | Suchbaum-Diagramm (Plotly) |
| `tests/` | Bruteforce-Cross-Check, Bound-Ordnung, Invarianten, Kurzschluss, Sicherheitsgrenzen |

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

---

Teil des [Operations-Research-Demo-Portfolios](https://sebastianhanisch.net/demos.html) von
[Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning.
Interesse an einer maßgeschneiderten Lösung? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html).
