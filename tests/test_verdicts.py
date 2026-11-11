"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Zahl im Text und jede Schwelle der Art steht hier.

Ein Verdikt ist eine reine Funktion (Art, Text) und bekommt Zeilen, nicht Zufalls-Seeds. Damit prüft der Test die Grenzen und jede genannte Zahl direkt."""

from fractions import Fraction as Fr

import pytest

import ngr_algorithm as A
import ngr_evaluation as ev


def ladder_row(name, memory, walk, rc, bound, gap, rounds=7, labels=300):
    return ev.LadderRow(name, memory, walk, rc, 50, 20, 3, 27, bound, rounds, labels, gap)


def ladder(bounds=(Fr(83, 3), Fr(86, 3), 30, 30, 30, 30, 30), kc=(Fr(30), Fr(30))):
    el = Fr(bounds[-1])
    rows = []
    for k, b in enumerate(bounds, start=1):
        walk = {1: (7, 6, 7, 6), 2: (5, 3, 5, 1)}.get(k, (2, 7, 6))
        rows.append(ladder_row(f"ng k = {k}", A.ng(k), walk, {1: -18, 2: -14}.get(k, -10), Fr(b), float(100 * (el - Fr(b)) / el), labels=400 - 10 * k))
    for K, b in zip((2, 3), kc):
        rows.append(ladder_row(f"k-Zyklen K = {K}", A.kcyc(K), (2, 7, 6), -10, Fr(b), float(100 * (el - Fr(b)) / el), labels=328))
    return rows


def test_verdict_walk_forbidden_names_position_customer_and_memory():
    a = ev.analyse_walk(2, (7, 6, 7))
    kind, text = ev.verdict_walk(2, (7, 6, 7), a, 7)
    assert kind == "warning"
    assert "Der Weg 7-6-7 ist bei k = 2 **verboten**" in text and "An Stelle 3 steht Kunde 7" in text and "Gedächtnis {6,7}" in text


def test_verdict_walk_allowed_with_a_repetition_and_feasible_is_info_with_the_value():
    a = ev.analyse_walk(2, (5, 3, 5, 1))
    kind, text = ev.verdict_walk(2, (5, 3, 5, 1), a, 7)
    assert kind == "info" and "**erlaubt**, obwohl er einen Kunden mehrmals besucht" in text and "reduzierten Kosten in der ersten Runde sind −14" in text


def test_verdict_walk_allowed_without_repetition_is_success():
    a = ev.analyse_walk(1, (2, 7, 6))
    kind, text = ev.verdict_walk(1, (2, 7, 6), a, 7)
    assert kind == "success" and "jeder Kunde höchstens einmal" in text and "reduzierten Kosten in der ersten Runde sind −10" in text


def test_verdict_walk_allowed_but_infeasible_says_so():
    a = ev.analyse_walk(2, (1, 2))                    # Kunde 2 kommt nach Kunde 1 zu spät
    assert a.allowed and a.feasible is False
    kind, text = ev.verdict_walk(2, (1, 2), a, 7)
    assert kind == "info" and "verletzt aber Last, Zeitfenster oder die Rückkehrzeit" in text


def test_verdict_ladder_names_bounds_gaps_and_first_equal_k():
    kind, text = ev.verdict_ladder(ladder())
    assert kind == "info"
    assert "83/3 (≈ 27,67) bei k = 1 (Lücke 7,78 %" in text and "86/3 (≈ 28,67) bei k = 2 (Lücke 4,44 %)" in text and "ab **k = 3**" in text and "elementaren Schranke 30" in text
    assert ev.verdict_ladder(ladder(bounds=(30,) * 7))[0] == "success"
    kind, text = ev.verdict_ladder(ladder(bounds=(Fr(83, 3), 30, 30, 30, 30, 30, 30)))
    assert "ab **k = 2**" in text


def live(gaps, ks=(1, 2, 3, 4, 5, 8), labels=None, aborted=()):
    labels = labels or [1000 * (i + 1) for i in range(len(ks))]
    return [ev.LiveRow(k, None if k in aborted else 800.0, lab, 10, 500, k in aborted, g) for k, lab, g in zip(ks, labels, gaps)]


def test_verdict_live_with_a_knee():
    rows = live([2.309, 0.172, 0.0, 0.0, 0.0, 0.0], labels=[10053, 11437, 13598, 15831, 13576, 14549])
    kind, text = ev.verdict_live(rows, 20, 100)
    assert kind == "info"
    assert "Bei 20 Kunden und Fensterbreite 100 liegt die Schranke bei k = 1 um 2,31 % unter der bei k = 8" in text and "**ab k = 3** ist die Lücke 0" in text
    assert "Der Bezug ist k = 8, nicht die elementare Schranke" in text and "von 10 053 auf 14 549 (das 1,4-Fache)" in text


def test_verdict_live_zero_from_the_start_and_threshold():
    kind, text = ev.verdict_live(live([0.0] * 6, labels=[1000, 1100, 1200, 1300, 1400, 2000]), 30, 20)
    assert kind == "success" and "schon bei k = 1 gleich der bei k = 8" in text and "das 2,0-Fache der Labels von k = 1" in text
    kind, text = ev.verdict_live(live([0.0001, 0.0, 0.0, 0.0, 0.0, 0.0]), 20, 100)
    assert "ab k = 2" in text                                                 # eine Lücke von 0,0001 % ist noch keine 0 (die Rundung auf 0 geschieht in gap_percent)


def test_verdict_live_with_aborted_runs():
    rows = live([None, 0.5, 0.0, 0.0, 0.0, 0.0], aborted=(1,))
    kind, text = ev.verdict_live(rows, 30, 100)
    assert kind == "info" and "Läufe mit Abbruch sind nicht eingerechnet" in text and "bei k = 2 um 0,50 % unter der bei k = 8" in text
    kind, text = ev.verdict_live(live([None, None, None, None, None, 0.0], aborted=(1, 2, 3, 4, 5)), 30, 100)
    assert kind == "warning" and "2 000 000 erzeugten Labels" in text.replace(" ", " ")


def test_verdict_round1_names_the_walks_and_the_first_elementary_k():
    kind, text = ev.verdict_round1(ladder())
    assert kind == "info"
    assert "ng k = 1 den Weg 7-6-7-6 mit reduzierten Kosten −18 (wiederholt einen Kunden)" in text and "ng k = 2 den Weg 5-3-5-1 (−14; wiederholt einen Kunden)" in text
    assert "ab k = 3 den elementaren besten Weg 2-7-6 (−10; wiederholt keinen Kunden)" in text and "zählt der Dualpreis eines Kunden bei jedem Besuch erneut" in text


def test_verdict_walkcheck_success_and_error():
    ok = ev.WalkCheck("ng k = 1", 89, Fr(-18), Fr(83, 3), True, True)
    bad = ev.WalkCheck("ng k = 2", 82, Fr(-14), Fr(29), True, False)
    kind, text = ev.verdict_walkcheck([ok, ok])
    assert kind == "success" and "In 2 von 2 Gedächtnissen stimmen" in text
    kind, text = ev.verdict_walkcheck([ok, bad])
    assert kind == "error" and "Nur in 1 von 2" in text


def test_verdict_contrast_hand_both_branches():
    kind, text = ev.verdict_contrast_hand(ladder())
    assert kind == "info" and "K = 2 mit 30 höher (schärfer) als die von ng k = 2 mit 86/3 (≈ 28,67)" in text and "328 statt 380 Labels" in text and "K = 3 gegen ng k = 3: 30 gegen 30, 328 gegen 370 Labels" in text
    same = ladder(bounds=(Fr(83, 3), 30, 30, 30, 30, 30, 30))
    kind, text = ev.verdict_contrast_hand(same)
    assert "dieselbe Schranke 30" in text and "328 gegen 380" in text


def knick_rows():
    """Zwei Instanzen (je eine zufällig, eine gruppiert) mit allen Gedächtnissen; Bezug ng k = 8 hat die Schranke 100."""
    def row(typ, seed, art, k, bound, labels, aborted=0):
        return {"typ": typ, "seed": seed, "art": art, "k": k, "schranke": None if aborted else bound, "runden": 5, "labels": labels, "abgebrochen": aborted, "quelle": "x"}

    out = []
    for typ, seed in (("zufall", 0), ("cluster", 0)):
        out += [row(typ, seed, "ng", 8, 100.0, 1000)]
        out += [row(typ, seed, "ng", k, 100.0 - gap, labels) for k, gap, labels in ((1, 4.0, 500), (2, 1.0, 600), (3, 0.5, 700), (4, 0.2, 800), (5, 0.1, 900))]
        out += [row(typ, seed, "kcyc", K, 100.0 - gap, labels, aborted=(typ == "cluster" and K == 4)) for K, gap, labels in ((2, 0.4, 1600), (3, 0.0, 3500), (4, -0.0, 3400))]
    return out


def test_knick_table_values_and_aborted_runs():
    t = {(r["art"], r["k"]): r for r in ev.knick_table(knick_rows())}
    assert t[("ng", 1)]["luecke_mittel"] == pytest.approx(4.0) and t[("ng", 1)]["luecke_max"] == pytest.approx(4.0) and t[("ng", 1)]["labels_verhaeltnis"] == 0.5 and t[("ng", 1)]["instanzen"] == 2
    assert t[("kcyc", 2)]["labels_verhaeltnis"] == 1.6
    assert (t[("kcyc", 4)]["instanzen"], t[("kcyc", 4)]["abgebrochen"]) == (1, 1)
    cluster = {(r["art"], r["k"]): r for r in ev.knick_table(knick_rows(), "cluster")}
    assert cluster[("kcyc", 4)]["instanzen"] == 0 and cluster[("kcyc", 4)]["luecke_mittel"] is None and cluster[("kcyc", 4)]["abgebrochen"] == 1


def test_verdict_knick_threshold_is_inclusive_at_half_a_percent():
    """Das Mittel von k = 3 ist genau 0,5 %: zählt als „nicht unter 0,5 %“, die Aussage beginnt also erst bei k = 4."""
    kind, text = ev.verdict_knick(knick_rows())
    assert kind == "info"
    assert "bei k = 1 im Mittel 4,00 % unter der von k = 8 (größter Einzelwert 4,00 %, 2 Instanzen)" in text
    assert "ab k = 4 liegt das Mittel unter 0,5 % (0,20 %, größter Einzelwert 0,20 %)" in text and "bei k = 5 sind es 0,10 % im Mittel und höchstens 0,10 % im Einzelfall" in text


def test_knick_pairs_counts_higher_equal_lower():
    pairs = {p["K"]: p for p in ev.knick_pairs(knick_rows())}
    # K = 2: 99,6 gegen ng 2: 99,0 -> höher; K = 3: 100 gegen 99,5 -> höher; K = 4: nur zufällig fertig, 100,0 gegen 99,8 -> höher
    assert (pairs[2]["paare"], pairs[2]["hoeher"], pairs[2]["gleich"], pairs[2]["tiefer"]) == (2, 2, 0, 0)
    assert (pairs[4]["paare"], pairs[4]["hoeher"]) == (1, 1)
    assert pairs[2]["labels_verhaeltnis"] == (1600 / 600)


def test_verdict_contrast_series_names_every_number():
    rows = knick_rows()
    kind, text = ev.verdict_contrast_series(ev.knick_table(rows), ev.knick_pairs(rows), ev.knick_compare_k2_ng5(rows), ev.knick_table(rows, "cluster"))
    assert kind == "info"
    assert "bei K = 2 in 2 von 2 Paaren und bei K = 3 in 2 von 2, bei K = 4 nur in 1 von 1 Paaren (gleich in 0)" in text and "(Mittel über die fertigen Instanzen: ng k = 3: 2, K = 2: 2, ng k = 5: 2, K = 3: 2)" in text and "2,67-, 5,00- und 4,25-Fache der Labels" in text
    assert "**Pro Label gerechnet**" in text and "ng k = 3 0,70 und 0,50 %, K = 2 1,60 und 0,40 %; ng k = 5 0,90 und 0,10 %, K = 3 3,50 und 0,00 %" in text
    assert "K = 4 ist bei 1 von 2 Instanzen an der Zeitgrenze der Messung abgebrochen (bei gruppierten Instanzen 1 von 1)" in text


def elementar_rows(n, width, gaps, k=5):
    """Sechs Instanzen: elementarer Bezug 100, Gedächtnis k mit den gegebenen Lücken (in Prozent)."""
    out = []
    for seed, gap in enumerate(gaps):
        out.append({"n": n, "breite": width, "seed": seed, "k": n, "schranke": 100.0, "runden": 5, "labels": 500, "abgebrochen": 0, "quelle": "x"})
        out.append({"n": n, "breite": width, "seed": seed, "k": k, "schranke": 100.0 - gap, "runden": 5, "labels": 400, "abgebrochen": 0, "quelle": "x"})
    return out


def test_elementar_table_counts_only_instances_with_a_finished_reference():
    rows = elementar_rows(20, 100, [0, 0, 0, 0, 0.25, 0.25])
    rows[0]["abgebrochen"], rows[0]["schranke"] = 1, None        # elementarer Lauf der Instanz 0 abgebrochen
    t = {r["k"]: r for r in ev.elementar_table(rows, 20)}
    assert t[5]["laeufe"] == 6 and t[5]["mit_bezug"] == 5 and t[5]["luecke_null"] == 3
    assert t[5]["luecke_mittel"] == pytest.approx(0.1) and t[5]["luecke_max"] == pytest.approx(0.25) and t[20]["elementar"] and t[20]["laeufe"] == 5


def test_verdict_elementar_and_small_n():
    t = ev.elementar_table(elementar_rows(20, 100, [0, 0, 0, 0, 0.25, 0.25]), 20)
    kind, text = ev.verdict_elementar(t, 20)
    assert kind == "info" and "Bei 20 Kunden, k = 5 gegen elementar: Breite 100: 2 von 6 Instanzen mit Lücke (Mittel 0,08 %, größter Einzelwert 0,25 %)" in text
    by_n = {}
    for n, gaps in ((10, [0] * 6), (15, [0] * 6), (20, [0, 0, 0, 0, 0.25, 0.25]), (25, [0, 0, 0, 0, 0.5, 0.75])):
        by_n[n] = ev.elementar_table(elementar_rows(n, 100, gaps) + elementar_rows(n, 40, [0] * 6), n)
    kind, text = ev.verdict_small_n(by_n)
    assert "Breite 40: keine Lücke bei n = 10, 15, 20, 25" in text
    assert "Breite 100: keine Lücke bei n = 10, 15; Lücke bei n = 20: 2 von 6 Instanzen (Mittel 0,08 %, größter Einzelwert 0,25 %); n = 25: 2 von 6 Instanzen (Mittel 0,21 %, größter Einzelwert 0,75 %)" in text
    assert text.endswith("gilt in dieser Messreihe also nur bis n = 15 und bei Breite 40.")


def skalierung_rows():
    """Zwei Zellen mit je zwei Instanzen; k = 16 ist der Bezug."""
    out = []
    for typ, n, width, gaps in (("zufall", 50, 100, {1: 4.0, 3: 1.0, 5: 0.3, 8: 0.1, 12: 0.0}), ("zufall", 100, 20, {1: 0.0, 3: 0.0, 5: 0.0, 8: 0.0, 12: 0.0})):
        for seed in range(2):
            for k in (1, 3, 5, 8, 12, 16):
                gap = gaps.get(k, 0.0)
                labels = 1000 * (1 + k)
                out.append({"typ": typ, "n": n, "breite": width, "seed": seed, "k": k, "schranke": 100.0 - gap, "runden": 3, "labels": labels, "dominiert": labels // 2,
                            "abgebrochen": 0, "quelle": "x"})
            out.append({"typ": typ, "n": n, "breite": width, "seed": seed, "k": n, "schranke": None, "runden": 1, "labels": None, "dominiert": None, "abgebrochen": 1, "quelle": "x"})
    return out


def test_skalierung_table_and_verdict():
    rows = skalierung_rows()
    t = ev.skalierung_table(rows)
    cell = {(r["n"], r["k"]): r for r in t}
    assert cell[(50, 1)]["luecke_mittel"] == pytest.approx(4.0) and cell[(50, 5)]["luecke_max"] == pytest.approx(0.3) and cell[(50, 16)]["luecke_null"] == 2 and cell[(100, 1)]["luecke_null"] == 2
    assert cell[(50, 5)]["faktor_16_zu_5"] == 17000 / 6000 and cell[(50, 5)]["dominiert_anteil"] == 50.0
    assert ev.skalierung_elementar(rows) == {"laeufe": 4, "fertig": 0, "abgebrochen": 4}
    kind, text = ev.verdict_skalierung(t)
    assert kind == "info" and "Über die 2 Zellen (je 12 Instanzen)" in text and "k = 5 im Mittel höchstens 0,30 % unter k = 16, im Einzelfall bis 0,30 %" in text
    assert "k = 8 im Mittel höchstens 0,10 %" in text and "Bei 1 Zellen (n = 100, Breite 20) ist die Lücke schon bei k = 1 gleich 0" in text


def test_dssr_summary_on_hand_set_rows():
    def row(duals, dssr, ng5, ng8, labels):
        m = lambda rc, lab: {"rc": rc, "labels": lab, "abgebrochen": 0}  # noqa: E731
        return {"typ": "zufall", "seed": 0, "duals": duals, "quelle": "x", "dssr": m(dssr, labels[0]), "ng5": m(ng5, labels[1]), "ng8": m(ng8, labels[2]), "elem": m(dssr, 9)}

    rows = [row("runde2", -10.0, -12.0, -10.0, (600, 100, 200)), row("runde4", -5.0, -5.0, -5.0, (200, 100, 100)), row("ende", 0.0, 0.0, 0.0, (1000, 100, 125))]
    s = ev.dssr_summary(rows)
    assert (s["saetze"], s["dssr_abgebrochen"], s["ng5_verfehlt"], s["ng5_verfehlt_runde2"], s["ng5_verfehlt_runde4"], s["ng5_verfehlt_ende"], s["saetze_ende"], s["ng8_verfehlt"]) == (3, 0, 1, 1, 0, 0, 1, 0) and (s["mit_elem"], s["gleich_elem"]) == (3, 3)
    assert s["faktor_ng5"] == (6 + 2 + 10) / 3 and s["faktor_ng8"] == (3 + 2 + 8) / 3 and s["faktor_ng5_ende"] == 10


def test_verdict_check_success_and_warning():
    def series(rows, aborted, done, same):
        return {"zeilen": rows, "in_vormessung_abgebrochen": aborted, "neu_gerechnet": done, "schranke_gleich": same, "labels_gleich": same, "runden_gleich": same, "dominiert_gleich": same}

    check = {"knick": series(216, 11, 205, 205), "elementar": series(216, 3, 213, 213), "skalierung": series(672, 94, 100, 100)}
    kind, text = ev.verdict_check(check)
    assert kind == "success" and "Von 996 in der Messung fertigen Läufen hat die Demo 518 mit ihrem Kern neu gerechnet" in text and "in 518, die Zahl der erzeugten Labels in 518" in text
    assert "478 Läufe sind nicht neu gerechnet" in text
    check["skalierung"] = series(672, 94, 100, 99)
    assert ev.verdict_check(check)[0] == "warning"
