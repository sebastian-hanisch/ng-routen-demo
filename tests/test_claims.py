"""Jede Zahl der README und der App-Texte wird hier nachgerechnet oder gegen die Daten gehalten (DEMO-PLAYBOOK §4, §11a). Zeiten stehen in keinem Test.

Die festen Messreihen (data/*.json) stammen aus den Rohausgaben der Messungen der Planung (Quelle `Datei:Zeile` je Zeile). Hier wird
- das Handbeispiel exakt gerechnet (Tabellen der README wörtlich geprüft),
- eine Stichprobe jeder Messreihe **mit dem Kern dieser Demo neu gerechnet** (Schranke immer; die Zahl der Labels exakt, wenn die Umgebung die der Messung ist, sonst in einem Band,
  denn der Weg des LP-Lösers und damit Runden und Labels können mit der SciPy-Version abweichen),
- die vollständige Nachrechnung (tools/nachrechnen.py, Ergebnis data/nachrechnung.json) auf Konsistenz geprüft (nicht im Test neu gerechnet: Stunden),
- jede Tabelle der README aus den Daten berechnet und wörtlich in der README gesucht (tools/readme_tabellen.py).
Die DSSR-Reihe ist nicht neu gerechnet; ihre Zählungen sind aus den Zeilen berechnet."""

import json
import statistics
import sys
from pathlib import Path

import pytest

import ngr_algorithm as A
import ngr_constants as C
import ngr_evaluation as ev
import ngr_scenario as S
import readme_tabellen as RT

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")
PLANNING = ROOT.parent / "label-setting-planung" / "vormessung"
MEASURED_ENVIRONMENT = sys.platform == "win32" and __import__("scipy").__version__ == "1.18.1"   # Umgebung der Messung: exakte Labels, sonst Band


def rows(name):
    return ev.load_rows(name)


# --- Handbeispiel ---------------------------------------------------------------------------------------------------------------------------

def test_the_hand_example_tables_are_in_the_readme():
    for table in (RT.round1_table(), RT.ladder_table(), RT.walks_table()):
        assert table in README
    inst, _ = ev.hand()
    masks = A.ng_masks(inst, 2)
    sets = ", ".join("{" + ",".join(str(i) for i in range(1, 8) if (masks[j] >> i) & 1) + "}" for j in range(1, 8))
    assert f"Bei k = 2 sind die Nachbarschaften {sets} für die Kunden 1 bis 7; Kunde 5 hat Kunde 3 als Nachbarn, Kunde 3 aber den Kunden 4." in README


def test_the_counterproof_over_all_walks():
    checks = ev.hand_check_all_walks()
    assert [c.walks for c in checks] == [89, 82, 79, 79, 79, 79, 79, 79, 79]
    assert all(c.same_best and c.same_bound for c in checks) and len(checks) == 9
    assert "(9 von 9 Gedächtnissen)" in README and "Für jedes Gedächtnis ergibt der Master über **alle** zulässigen Wege" in README


def test_the_gaps_of_the_ladder_are_calculated_from_the_bounds():
    ladder = {r.name: r for r in ev.hand_ladder()}
    assert ladder["ng k = 1"].gap == pytest.approx(100 * (30 - 83 / 3) / 30) and ladder["ng k = 2"].gap == pytest.approx(100 * (30 - 86 / 3) / 30)
    assert "Lücke = (30 − Schranke) / 30" in README


# --- 24 Instanzen, n = 30 -------------------------------------------------------------------------------------------------------------------

def test_knick_table_and_pairs():
    knick = rows("knick_n30")
    assert RT.knick_table(knick) in README and RT.pairs_table(knick) in README
    t = {(r["art"], r["k"]): r for r in ev.knick_table(knick)}
    assert [round(t[("ng", k)]["luecke_mittel"], 3) for k in range(1, 6)] == [3.563, 0.920, 0.460, 0.199, 0.115]
    assert [round(t[("ng", k)]["luecke_max"], 3) for k in range(1, 6)] == [7.157, 2.365, 1.116, 0.938, 0.898]
    assert [round(t[("ng", k)]["labels_verhaeltnis"], 2) for k in range(1, 6)] == [0.50, 0.59, 0.69, 0.73, 0.80]
    assert [(t[("kcyc", K)]["instanzen"], t[("kcyc", K)]["abgebrochen"]) for K in (2, 3, 4)] == [(24, 0), (22, 2), (15, 9)]
    assert [round(t[("kcyc", K)]["luecke_mittel"], 3) for K in (2, 3, 4)] == [0.469, 0.073, -0.004]
    assert [round(t[("kcyc", K)]["labels_verhaeltnis"], 2) for K in (2, 3, 4)] == [1.69, 3.52, 3.39]
    assert "Die mittlere Lücke sinkt von 3,563 % bei k = 1 auf 0,920 % bei k = 2 (der größte Sprung) und weiter auf 0,460 %, 0,199 % und 0,115 % bei k = 3, 4 und 5." in README


def test_k_cycles_above_the_ng_8_bound_and_the_pairs():
    knick = rows("knick_n30")
    by = {}
    for r in knick:
        by.setdefault((r["typ"], r["seed"]), {})[(r["art"], r["k"])] = r
    over = {K: [(key, ev.gap_percent(c[("ng", 8)]["schranke"], c[("kcyc", K)]["schranke"])) for key, c in by.items()
                if ev._finished(c[("kcyc", K)]) and ev.gap_percent(c[("ng", 8)]["schranke"], c[("kcyc", K)]["schranke"]) < 0] for K in (3, 4)}
    assert [key for key, _ in over[3]] == [("cluster", 1)] and sorted(key for key, _ in over[4]) == [("cluster", 1), ("cluster", 6)]
    assert round(-min(g for _, g in over[4]), 3) == 0.055
    assert "in 2 der 15 fertigen Instanzen über der von ng k = 8 (größte Überschreitung 0,055 %), die von K = 3 in 1 der 22 (derselben Instanz)" in README
    pairs = {p["K"]: p for p in ev.knick_pairs(knick)}
    assert [(pairs[K]["paare"], pairs[K]["hoeher"], pairs[K]["gleich"], pairs[K]["tiefer"]) for K in (2, 3, 4)] == [(24, 23, 0, 1), (22, 20, 2, 0), (15, 7, 8, 0)]
    assert [round(pairs[K]["labels_verhaeltnis"], 2) for K in (2, 3, 4)] == [2.91, 5.02, 4.60]
    k2 = ev.knick_compare_k2_ng5(knick)
    assert (k2["paare"], k2["tiefer"], k2["gleich"], k2["hoeher"], round(k2["labels_verhaeltnis"], 2)) == (24, 20, 2, 2, 2.12)
    assert "K = 2 gegen ng k = 5 (24 Paare): Schranke der k-Zyklen tiefer in 20, gleich in 2, höher in 2 Paaren, das 2,12-Fache der Labels." in README
    cluster = {(r["art"], r["k"]): r for r in ev.knick_table(knick, "cluster")}
    zufall = {(r["art"], r["k"]): r for r in ev.knick_table(knick, "zufall")}
    assert (cluster[("kcyc", 4)]["abgebrochen"], zufall[("kcyc", 4)]["abgebrochen"]) == (9, 0)
    assert "in 9 von 12 Fällen an der Zeitgrenze der Messung abgebrochen (zufällig: 0 von 12)" in README


def test_the_24_instances_are_12_random_and_12_clustered_with_the_seeds_0_to_11():
    knick = rows("knick_n30")
    assert len(knick) == 24 * 9
    for typ in ("zufall", "cluster"):
        assert sorted({r["seed"] for r in knick if r["typ"] == typ}) == list(range(12))
    assert json.loads((ROOT / "data" / "knick_n30.json").read_text(encoding="utf-8"))["kontrolle_ng1_ng5_gegen_v12a"] == 48


# --- Bezug elementar ------------------------------------------------------------------------------------------------------------------------

def test_elementary_reference_tables():
    elem = rows("elementar")
    assert RT.elementar30_table(elem) in README and RT.small_n_table(elem) in README
    t30 = {(r["breite"], r["k"]): r for r in ev.elementar_table(elem, 30)}
    assert (t30[(100, 30)]["laeufe"], t30[(100, 1)]["mit_bezug"], t30[(40, 1)]["mit_bezug"]) == (3, 3, 6)
    assert [round(t30[(100, k)]["luecke_mittel"], 2) for k in (1, 3, 5, 8, 12)] == [4.82, 0.52, 0.0, 0.0, 0.0]
    assert [round(t30[(100, k)]["luecke_max"], 2) for k in (1, 3)] == [6.80, 0.96]
    assert [round(t30[(40, k)]["luecke_mittel"], 2) for k in (1, 3, 5, 8, 12)] == [0.24, 0.0, 0.0, 0.0, 0.0] and round(t30[(40, 1)]["luecke_max"], 2) == 0.72
    for n in (10, 15, 20, 25):
        t = {(r["breite"], r["k"]): r for r in ev.elementar_table(elem, n)}
        assert t[(100, n)]["laeufe"] == 6 and t[(40, n)]["laeufe"] == 6                  # alle elementaren Läufe fertig
        assert t[(40, 5)]["luecke_null"] == 6                                           # Breite 40: k = 5 gleich elementar in 6 von 6
        with_gap = 6 - t[(100, 5)]["luecke_null"]
        assert with_gap == (2 if n >= 20 else 0), n
    t20, t25 = ({(r["breite"], r["k"]): r for r in ev.elementar_table(elem, n)} for n in (20, 25))
    assert (round(t20[(100, 5)]["luecke_mittel"], 2), round(t20[(100, 5)]["luecke_max"], 2), round(t25[(100, 5)]["luecke_mittel"], 2), round(t25[(100, 5)]["luecke_max"], 2)) == (0.07, 0.25, 0.18, 0.64)
    assert "bei n = 20 und 25 und Breite 100 in je 2 von 6 Instanzen nicht" in README
    assert "bei 20 und 25 Kunden und Breite 100 aber in 2 von 6 Instanzen darunter" in README


# --- 50 und 100 Kunden ----------------------------------------------------------------------------------------------------------------------

def test_scaling_tables_and_headline_numbers():
    skal = rows("skalierung")
    assert RT.skalierung_table(skal) in README
    assert ev.skalierung_elementar(skal) == {"laeufe": 96, "fertig": 2, "abgebrochen": 94}
    elementary_done = [r for r in skal if r["k"] == r["n"] and not r["abgebrochen"]]
    assert [(r["typ"], r["n"], r["breite"]) for r in elementary_done] == [("zufall", 50, 40)] * 2
    t = ev.skalierung_table(skal)
    cells = {(r["typ"], r["n"], r["breite"], r["k"]): r for r in t}
    assert len({(r["typ"], r["n"], r["breite"]) for r in t}) == 8 and all(r["laeufe"] == 12 for r in t)
    assert round(max(r["luecke_mittel"] for r in t if r["k"] == 5), 3) == 0.244 and round(max(r["luecke_max"] for r in t if r["k"] == 5), 3) == 0.666
    assert round(max(r["luecke_mittel"] for r in t if r["k"] == 8), 3) == 0.066 and round(max(r["luecke_max"] for r in t if r["k"] == 8), 3) == 0.304
    assert max(cells[("cluster", 50, 100, 8)]["luecke_max"], 0) == pytest.approx(0.238, abs=5e-4)            # größte Einzellücke k = 8 der gruppierten Zelle (frühere Fassung: 0,24 %)
    assert "im Mittel je Zelle bis 0,24 % unter der Schranke bei k = 16 (in Prozent dieser Schranke), im Einzelfall bis 0,67 %; bei k = 8 im Mittel je Zelle bis 0,07 %, im Einzelfall bis 0,30 %" in README
    assert "die zufällige Zelle (n = 50, Breite 100) hat 0,30 %" in README
    assert (round(min(r["dominiert_anteil"] for r in t), 1), round(max(r["dominiert_anteil"] for r in t), 1)) == (77.7, 96.0)
    assert (round(min(r["faktor_16_zu_5"] for r in t), 2), round(max(r["faktor_16_zu_5"] for r in t), 2)) == (1.48, 2.37)
    assert cells[("zufall", 50, 40, 16)]["dominiert_anteil"] == pytest.approx(77.74, abs=0.01)
    assert "sinkt bei k = 16 auf 77,7 %, der größte Wert ist 96,0 %" in README
    assert "zwischen 77,7 und 96,0 % und sinkt mit k" in README and "im Median das 1,48- bis 2,37-Fache der Labels von k = 5" in README
    # Breite 20 bei 100 Kunden: Lücke 0 für jedes k in 24 von 24 Instanzen
    flat = [r for r in t if (r["n"], r["breite"]) == (100, 20)]
    assert all(r["luecke_mittel"] == 0 and r["luecke_max"] == 0 and r["luecke_null"] == 12 for r in flat) and len(flat) == 12
    assert "(24 von 24 Instanzen)" in README
    # sinkende Anteile dominierter Labels mit k: in jeder Zelle nimmt der Anteil von k = 1 bis k = 16 ab
    for typ, n, width in ev.skalierung_cells(skal):
        shares = [cells[(typ, n, width, k)]["dominiert_anteil"] for k in ev.SKALIERUNG_KS]
        assert shares == sorted(shares, reverse=True), (typ, n, width)
    # die genannten Zellen der Planung
    assert [round(cells[("cluster", 50, 100, k)]["luecke_mittel"], 2) for k in (1, 3, 5, 8, 12)] == [2.52, 0.50, 0.24, 0.07, 0.03]
    assert [round(cells[("zufall", 50, 100, k)]["luecke_mittel"], 2) for k in (1, 5, 8)] == [3.23, 0.12, 0.03]
    assert [round(cells[("zufall", 100, 40, k)]["luecke_mittel"], 2) for k in (1, 5, 8)] == [0.88, 0.0, 0.0]


# --- DSSR -----------------------------------------------------------------------------------------------------------------------------------

def test_dssr_numbers():
    dssr = rows("dssr")
    assert RT.dssr_table(dssr) in README
    s = ev.dssr_summary(dssr)
    assert (s["saetze"], s["dssr_abgebrochen"], s["ng5_verfehlt"], s["ng5_verfehlt_runde2"], s["ng5_verfehlt_runde4"], s["ng5_verfehlt_ende"], s["saetze_ende"]) == (72, 0, 24, 13, 11, 0, 24)
    assert (round(s["faktor_ng5"], 1), round(s["faktor_ng8"], 1), round(s["faktor_ng5_ende"], 1)) == (6.3, 5.2, 11.6)
    assert sorted({r["duals"] for r in dssr}) == ["ende", "runde2", "runde4"] and len([r for r in dssr if r["typ"] == "zufall"]) == 36
    assert "dort kostet meine DSSR-Variante das 11,6-Fache der Labels" in README and "Andere Runden und andere DSSR-Fassungen sind nicht gemessen" in README
    assert (s["mit_elem"], s["gleich_elem"]) == (66, 66) and "| DSSR liefert denselben Wert wie die elementare Rechnung | 66 von 66 Sätzen (in 6 Sätzen war die elementare Rechnung abgebrochen) |" in README
    # der DSSR-Weg ist in jedem Satz mindestens so gut wie ng 5 und ng 8 (ng ist eine Relaxation, DSSR liefert den elementaren Wert)
    assert all(r["dssr"]["rc"] >= r["ng5"]["rc"] - 1e-6 and r["dssr"]["rc"] >= r["ng8"]["rc"] - 1e-6 for r in dssr)


# --- Zufallsinstanz live --------------------------------------------------------------------------------------------------------------------

def test_live_instance_numbers():
    live = ev.live_ladder(30, 100, 1, 12)
    assert [r.k for r in live] == [1, 2, 3, 4, 5, 8, 12]
    assert round(live[0].gap, 2) == 5.45 and [r.k for r in live if r.gap == 0.0][0] == 4
    assert (live[0].labels, live[-1].labels) == ((44946, 131082) if MEASURED_ENVIRONMENT else (live[0].labels, live[-1].labels))
    assert "um 5,45 % unter der bei k = 12 und ist ab k = 4 gleich (Einzelfall, erzeugte Labels 44 946 bei k = 1 und 131 082 bei k = 12)" in README
    assert abs(live[0].labels - 44946) / 44946 < 0.1 and abs(live[-1].labels - 131082) / 131082 < 0.1       # Band, falls die Umgebung eine andere ist
    for seed in range(1, 9):
        narrow = ev.live_ladder(30, 20, seed, 5)
        assert [r.gap for r in narrow] == [0.0] * 5, seed
    assert "bei den Zufalls-Seeds 1 bis 8 in 8 von 8 Instanzen schon bei k = 1 gleich 0 (größtes k = 5)" in README


def test_the_app_statements_about_the_elementary_reference():
    """Zahlen aus Experiment 3 und 5 der App: 3 von 6 Instanzen mit fertigem elementarem Lauf bei 30 Kunden und Breite 100; 6 Instanzen je Breite."""
    t = {(r["breite"], r["k"]): r for r in ev.elementar_table(rows("elementar"), 30)}
    assert t[(100, 30)]["mit_bezug"] == 3 and t[(100, 1)]["laeufe"] == 6 and t[(40, 30)]["laeufe"] == 6
    assert sorted({r["seed"] for r in rows("elementar") if r["n"] == 30}) == list(range(6))
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    assert sorted(r["seed"] for r in rows("elementar") if r["n"] == 30 and r["breite"] == 100 and r["k"] == 30 and not r["abgebrochen"]) == [0, 1, 5]
    assert "bei Breite 100 sind das 3 von 6, die Zufalls-Seeds 0, 1 und 5; mit allen 6 Instanzen liegt die mittlere Lücke bei k = 1 bei 3,33 % (Maximum 6,80 %)" in README
    for piece in ("die Zufalls-Seeds 0, 1 und 5. Die Mittel der Tabelle gelten nur für diese 3 Instanzen", "bei Breite 100 sind das **3 von 6**", "in 3 von 6 Instanzen nicht zu Ende", "(24 von 24 Instanzen)", "6 Instanzen je Fensterbreite (Zufalls-Seeds 0 bis 5)"):
        assert piece in app, piece


# --- Stichproben mit dem Kern neu gerechnet -------------------------------------------------------------------------------------------------

def _recompute(row):
    clustered = row.get("typ") == "cluster"
    inst = S.make_instance(row.get("n", 30), row["seed"], float(row.get("breite", 100)), clustered=clustered)
    return A.colgen(inst, A.Memory(row.get("art", "ng"), row["k"]), A.solve_master_lp)


def _same_labels(result, row):
    if MEASURED_ENVIRONMENT:
        return result.labels == row["labels"]
    return abs(result.labels - row["labels"]) <= 0.15 * row["labels"]


def _pick(series, **where):
    return [r for r in rows(series) if all(r.get(k) == v for k, v in where.items()) and not r["abgebrochen"]]


def test_sample_rows_are_recomputed_with_the_kernel():
    sample = []
    sample += [r for r in _pick("knick_n30", typ="zufall", seed=0) if (r["art"], r["k"]) in {("ng", 1), ("ng", 5), ("ng", 8), ("kcyc", 2)}]
    sample += [r for r in _pick("knick_n30", typ="cluster", seed=1) if (r["art"], r["k"]) in {("ng", 2), ("ng", 4)}]
    sample += _pick("elementar", n=15, breite=100, seed=2) + _pick("elementar", n=25, breite=100, seed=0, k=5) + _pick("elementar", n=30, breite=40, seed=3, k=5)
    sample += _pick("skalierung", typ="zufall", n=50, breite=40, seed=0, k=1) + _pick("skalierung", typ="zufall", n=50, breite=40, seed=0, k=16)
    assert len(sample) == 13
    tolerance = {"knick_n30": 6e-6, "elementar": 6e-5, "skalierung": 6e-6}
    for series, tol in tolerance.items():
        for row in [r for r in sample if r in rows(series)]:
            res = _recompute(row)
            assert not res.aborted and res.bound == pytest.approx(row["schranke"], abs=tol), row["quelle"]
            assert _same_labels(res, row), (row["quelle"], res.labels, row["labels"])


def test_recomputed_sample_dominated_counts_for_the_scaling_series():
    row = _pick("skalierung", typ="zufall", n=50, breite=40, seed=1, k=3)[0]
    res = _recompute(row)
    assert res.bound == pytest.approx(row["schranke"], abs=6e-6)
    if MEASURED_ENVIRONMENT:
        assert (res.labels, res.dominated, res.iterations) == (row["labels"], row["dominiert"], row["runden"])
    else:
        assert abs(res.dominated - row["dominiert"]) <= 0.15 * row["dominiert"]


# --- Nachrechnung (vollständig, Ergebnis der Werkzeuge) -------------------------------------------------------------------------------------

def test_the_recomputation_report_is_consistent():
    report = ev.load_check()
    assert set(report) == {"knick", "elementar", "skalierung"}
    names = {"knick": "knick_n30", "elementar": "elementar", "skalierung": "skalierung"}
    for key, c in report.items():
        data = rows(names[key])
        jsonl = [json.loads(line) for line in (ROOT / "tools" / "nachrechnung" / f"{key}.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
        assert c["zeilen"] == len(data) and c["in_vormessung_abgebrochen"] == sum(1 for r in data if r["abgebrochen"] or r["schranke"] is None)
        assert c["neu_gerechnet"] == len(jsonl) == len({x["quelle"] for x in jsonl})
        assert c["abweichungen"] == [] and c["schranke_gleich"] == c["labels_gleich"] == c["runden_gleich"] == c["neu_gerechnet"]
        assert c["dominiert_gleich"] == c["dominiert_verglichen"]
        assert {x["quelle"] for x in jsonl} <= {r["quelle"] for r in data}
        assert not any(x["abgebrochen"] for x in jsonl)
    assert (report["knick"]["in_vormessung_abgebrochen"], report["elementar"]["in_vormessung_abgebrochen"], report["skalierung"]["in_vormessung_abgebrochen"]) == (11, 3, 94)
    assert RT.check_table() in README
    assert "(11 + 3 + 94 Läufe)" in README


def test_the_recomputation_covers_what_the_readme_says():
    report = ev.load_check()
    done = {s: report[s]["neu_gerechnet"] for s in report}
    finished = {s: report[s]["zeilen"] - report[s]["in_vormessung_abgebrochen"] for s in report}
    assert done["elementar"] == finished["elementar"] and done["knick"] == finished["knick"]
    skal = [r for r in rows("skalierung") if not r["abgebrochen"]]
    n50 = [r for r in skal if r["n"] == 50]
    jsonl = {json.loads(line)["quelle"] for line in (ROOT / "tools" / "nachrechnung" / "skalierung.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()}
    assert {r["quelle"] for r in n50} <= jsonl
    n100 = [r for r in skal if r["n"] == 100]
    assert len(n100) == 288 and sum(1 for r in n100 if r["quelle"] in jsonl) == 72 and {r["seed"] for r in n100 if r["quelle"] in jsonl} == {0, 1, 2}
    assert sum(report[s]["neu_gerechnet"] for s in report) == 780 and sum(finished.values()) == 996
    assert "(72 von 288 fertigen Läufen)" in README and "die übrigen 216 Läufe (Zufalls-Seeds 3 bis 11)" in README and "(780 von 996)" in README


# --- Zeilen und Rohdateien ------------------------------------------------------------------------------------------------------------------

def test_every_row_names_its_source_and_sources_are_unique():
    for name in ("knick_n30", "elementar", "skalierung", "dssr"):
        quellen = [r["quelle"] for r in rows(name)]
        assert all(":" in q and q.split(":")[1].isdigit() and q.startswith(("out_", "run_")) for q in quellen), name
        assert len(set(quellen)) == len(quellen), name
        assert json.loads((ROOT / "data" / f"{name}.json").read_text(encoding="utf-8"))["quelle_ordner"] == "label-setting-planung/vormessung"


def test_literal_values_of_a_few_rows_equal_the_raw_output_lines():
    """Von Hand aus den Rohausgaben abgeschrieben (die Zeilen standen in run_p09.log, out_v8_cluster_n50_w100.txt, out_v1_n30.txt und out_v12b_zufall_0.txt)."""
    by = {r["quelle"]: r for name in ("knick_n30", "elementar", "skalierung", "dssr") for r in rows(name)}
    p09 = next(r for r in rows("knick_n30") if r["quelle"].startswith("run_p09.log") and (r["typ"], r["seed"], r["k"]) == ("zufall", 0, 1))
    assert (p09["schranke"], p09["runden"], p09["labels"], p09["abgebrochen"]) == (756.121435, 15, 52481, 0)
    v8 = next(r for r in rows("skalierung") if (r["typ"], r["n"], r["breite"], r["seed"], r["k"]) == ("cluster", 50, 100, 0, 1))
    assert (v8["schranke"], v8["runden"], v8["labels"], v8["dominiert"], v8["abgebrochen"], v8["quelle"]) == (587.687653, 27, 638138, 602313, 0, "out_v8_cluster_n50_w100.txt:2")
    v1 = next(r for r in rows("elementar") if (r["n"], r["breite"], r["seed"], r["k"]) == (30, 40, 0, 1))
    assert (v1["schranke"], v1["runden"], v1["labels"], v1["quelle"]) == (856.3526, 13, 13224, "out_v1_n30.txt:2")
    v12b = next(r for r in rows("dssr") if (r["typ"], r["seed"], r["duals"]) == ("zufall", 0, "runde2"))
    assert (v12b["dssr"]["rc"], v12b["dssr"]["labels"], v12b["ng5"]["rc"], v12b["ng5"]["labels"], v12b["elem"]["labels"]) == (-216.641450602, 24391, -230.148197371, 5799, 17717)
    assert by  # keine leere Menge


@pytest.mark.skipif(not PLANNING.exists(), reason="Ordner label-setting-planung/vormessung liegt nicht neben der Demo")
def test_rows_equal_what_the_builder_derives_from_the_raw_files():
    """Der Bau der data/*.json aus den Rohdateien (tools/baender_bauen.py) ergibt dieselben Zeilen wie die abgelegten Dateien."""
    import baender_bauen as B

    for name, builder in (("knick_n30", B.build_knick), ("elementar", B.build_elementar), ("skalierung", B.build_skalierung), ("dssr", B.build_dssr)):
        assert builder(PLANNING)["zeilen"] == rows(name), name


# --- Zahlen in App-Texten, die nicht aus der Rechnung kommen -------------------------------------------------------------------------------

def test_static_numbers_in_the_app_texts_match_the_data():
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "Horizont 300" in app and C.MAX_LABELS_PER_CALL == 2_000_000 and "2 Millionen erzeugte Labels" in app
    assert "10 bis 30" in app and (C.N_MIN, C.N_MAX) == (10, 30) and C.WALK_MAX_LENGTH == 12 and "höchstens 12 Besuche" in app
    assert [k for k in C.LIVE_LADDER] == [1, 2, 3, 4, 5, 8, 12] and "k = 1, 2, 3, 4, 5, 8, 12" in app
    inst, duals = ev.hand()
    assert (inst.service, inst.horizon, inst.capacity) == (2, 38, 6) and "Rückkehr bis 38" in README and "Kapazität 6" in README
    assert statistics.mean([2 * inst.d[0][j] == duals[j] for j in range(1, 8)]) == 1                   # Dualpreis der ersten Runde = zweimal der Abstand zum Depot


# --- Aussagen mit Voraussetzungen (Korrektur nach der Prüfung der Erklärseite) ---------------------------------------------------------------

def test_the_readme_intro_names_where_cycles_are_cheap_and_where_not():
    """Kreise erlaubt = k = 1: bei den 24 Zufallsinstanzen billig (0,50-Fache von k = 8), im Handbeispiel aber teurer (416 statt 326, Runde 1: 62 statt 56)."""
    ladder = {r.name: r for r in ev.hand_ladder()}
    assert (ladder["ng k = 1"].labels, ladder["ng k = 7 (elementar)"].labels, ladder["ng k = 1"].generated, ladder["ng k = 7 (elementar)"].generated) == (416, 326, 62, 56)
    t = {(r["art"], r["k"]): r for r in ev.knick_table(rows("knick_n30"))}
    assert round(t[("ng", 1)]["labels_verhaeltnis"], 2) == 0.50 and t[("ng", 1)]["instanzen"] == 24
    assert "im Mittel das 0,50-Fache der Labels von k = 8), im Handbeispiel aber nicht (k = 1 braucht dort mehr Labels: 416 statt 326 in der ganzen Spaltenerzeugung bei einer neuen Spalte je Runde, 62 statt 56 in Runde 1)" in README
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "wird sie bei den Zufallsinstanzen mit 30 Kunden billig (im Handbeispiel nicht, siehe Punkt 4 unten)" in app


def test_the_labels_of_the_hand_example_fall_with_k_only_for_one_new_column_per_round():
    inst, _ = ev.hand()
    ladder = ev.hand_ladder()
    labels15 = []
    for row in [r for r in ladder if r.memory.kind == "ng"]:
        cg = A.colgen(inst, row.memory, A.solve_master_exact, per_round=15, exact=True)
        assert cg.bound == row.bound                                    # die Schranke hängt nicht von der Zahl der Spalten je Runde ab
        labels15.append(cg.labels)
    assert labels15 == [209, 199, 147, 146, 148, 149, 151]
    assert [r.labels for r in ladder if r.memory.kind == "ng"] == [416, 382, 370, 370, 326, 326, 326] and [r.rounds for r in ladder if r.memory.kind == "ng"] == [8, 8, 8, 8, 7, 7, 7]
    assert "sind es 209, 199, 147, 146, 148, 149 und 151 Labels für k = 1 bis 7, also nicht fallend; die Schranken sind dieselben" in README
    assert "k = 1 bis 4 brauchen 8 Runden, k = 5 bis 7 nur 7" in README
    assert "| Gedächtnis | Schranke | Runden | Labels (eine neue Spalte je Runde) | Lücke zur elementaren Schranke |" in README
    assert "Labels gesamt (eine neue Spalte je Runde)" in (ROOT / "app.py").read_text(encoding="utf-8")


def test_erlaubt_and_zulaessig_are_told_apart_and_the_hand_data_are_in_the_readme():
    """„erlaubt“ = Gedächtnisregel; „zulässig“ = erlaubt und Last, Zeitfenster, Horizont. Beispiel: 7-6-1-7 ist bei k = 3 erlaubt, aber nicht zulässig."""
    inst, pi = ev.hand()
    assert A.walk_allowed(inst, A.ng(3), (7, 6, 1, 7)) and A.walk_value(inst, pi, (7, 6, 1, 7), 0) is None
    all_walks = {w for _, w in A.enumerate_walks(inst, pi, A.ng(7), exact=True)}
    assert (7, 6, 1, 7) not in all_walks and all(A.walk_allowed(inst, A.ng(3), w) for w in all_walks if len(set(w)) == len(w))
    assert "„erlaubt“ heißt nur: Der Weg erfüllt die Gedächtnisregel, „zulässig“ heißt: erlaubt und zusätzlich Last, Zeitfenster und Horizont eingehalten" in README
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "zulässig: die Gedächtnisregel gilt für den ganzen Weg, und Last, Zeitfenster und Horizont sind eingehalten" in app and "**zulässig** ist ein Weg erst, wenn zusätzlich Last, Zeitfenster und Horizont stimmen" in app
    # die Daten des Handbeispiels stehen in der README (Tabelle aus dem Kern, wie in der App) und stimmen mit ngr_scenario.py überein
    assert RT.hand_table() in README
    assert list(zip(S.HAND_POINTS[1:], S.HAND_DEMAND[1:], S.HAND_READY[1:], S.HAND_DUE[1:], pi[1:])) == [
        ((-1, 2), 1, 18, 28, 6), ((0, 3), 3, 3, 16, 6), ((-3, -2), 3, 5, 15, 10), ((-1, -2), 3, 20, 28, 6), ((-2, -1), 1, 3, 12, 6), ((2, 1), 1, 11, 21, 6), ((3, 2), 2, 8, 20, 10)]


def test_the_statements_about_30_customers_name_their_instances():
    t30 = {(r["breite"], r["k"]): r for r in ev.elementar_table(rows("elementar"), 30)}
    assert (t30[(40, 5)]["mit_bezug"], t30[(40, 5)]["luecke_null"], t30[(100, 5)]["mit_bezug"], t30[(100, 5)]["luecke_null"]) == (6, 6, 3, 3)
    assert "bei Breite 40 in 6 von 6 Instanzen und bei Breite 100 in 3 von 3 Instanzen mit fertigem elementarem Lauf (bei den anderen 3 brach die elementare Rechnung in der Messung ab) gleich der elementaren Schranke" in README


def test_the_scaling_side_statements_dominated_share_and_cost_at_width_20():
    skal = rows("skalierung")
    t = {(r["typ"], r["n"], r["breite"], r["k"]): r for r in ev.skalierung_table(skal)}
    # Breite 20, 100 Kunden: die Schranke ist gleich, die Labels wachsen trotzdem mit k (Median der Verhältnisse k = 16 gegen k = 5)
    assert (round(t[("cluster", 100, 20, 16)]["faktor_16_zu_5"], 2), round(t[("zufall", 100, 20, 16)]["faktor_16_zu_5"], 2)) == (1.87, 1.72)
    assert "im Median das 1,87-Fache (gruppiert) bzw. 1,72-Fache (zufällig) der Labels von k = 5" in README
    # Anteil dominierter Labels: 77,7 bis 96,0 % gilt für k = 1 bis 16; die 2 fertigen elementaren Läufe (n = 50, Breite 40, zufällig, k = 50) liegen bei 50,4 %
    assert sorted({r["k"] for r in t.values()}) == [1, 3, 5, 8, 12, 16]
    done = [r for r in skal if r["k"] == r["n"] and not r["abgebrochen"]]
    assert len(done) == 2 and {(r["typ"], r["n"], r["breite"], r["k"]) for r in done} == {("zufall", 50, 40, 50)}
    assert round(100.0 * sum(r["dominiert"] for r in done) / sum(r["labels"] for r in done), 1) == 50.4
    assert "für k = 1 bis 16 zwischen 77,7 und 96,0 % und sinkt mit k; die 2 fertigen elementaren Läufe (50 Kunden, Breite 40, zufällig, k = 50) haben zusammen 50,4 %" in README


def test_the_k_cycle_contrast_names_its_instance_sets():
    knick = rows("knick_n30")
    t = {(r["art"], r["k"]): r for r in ev.knick_table(knick)}
    assert [t[key]["instanzen"] for key in (("ng", 3), ("kcyc", 2), ("ng", 5), ("kcyc", 3))] == [24, 24, 24, 22]
    pairs = ev.knick_pairs(knick)
    _, text = ev.verdict_contrast_series(ev.knick_table(knick), pairs, ev.knick_compare_k2_ng5(knick), ev.knick_table(knick, "cluster"))
    assert "nicht immer höher als die von ng: bei K = 2 in 23 von 24 Paaren und bei K = 3 in 20 von 22, bei K = 4 nur in 7 von 15 Paaren (gleich in 8)" in text
    assert "(Mittel über die fertigen Instanzen: ng k = 3: 24, K = 2: 24, ng k = 5: 24, K = 3: 22)" in text


def test_app_texts_of_the_correction_round():
    """Stellen im Weg heißen a und b (nicht q, das ist die Last), die Besuchszahl im Master β; Schranke mit ihren zwei Rollen, Dominanz der k-Zyklen begründet, keine Aussage über
    Rechenzeit in Experiment 3, Abbruchgrenze und Dreiecksungleichung stehen auch in der README (über den gemeinsamen Annahmen-Text)."""
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "frühere Stelle $a$, spätere Stelle $b$" in app and "$j_a = j_b$ mit $a < b$" in app and "$q$" not in app and "$q_j$" in app
    assert r"\beta_{jr}" in app and "$a_{jr}$" not in app and " a_{jr} " not in app
    assert "Das ist eine einzige Zahl mit zwei Rollen" in app
    assert "**Warum diese Dominanz nichts verliert:**" in app and "folgt aus der Begründung im Expander" in app and "beweist es aber nicht" in app
    assert "dauert die Rechnung am größten k" not in app and "Mehr als 2 Millionen erzeugte Labels" in app
    assert "mit mehr neuen Spalten je Runde sind sie nicht fallend" in app
    assert "mehr als 2 Millionen Labels erzeugt" in C.ASSUMPTIONS_MARKDOWN and C.MAX_LABELS_PER_CALL == 2_000_000 and "die Dreiecksungleichung gilt" in C.ASSUMPTIONS_MARKDOWN
    assert C.ASSUMPTIONS_MARKDOWN.strip() in README
    inst, _ = ev.hand()
    assert all(inst.d[i][k] <= inst.d[i][j] + inst.d[j][k] for i in range(inst.n + 1) for j in range(inst.n + 1) for k in range(inst.n + 1))      # Manhattan: Dreiecksungleichung
