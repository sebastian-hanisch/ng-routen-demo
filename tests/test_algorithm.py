"""Kern gegen Handrechnung (DEMO-PLAYBOOK §1b): jede Einheit an der Mini-Instanz (Handbeispiel) aus conftest.py.

Die Nachbarschaften, die Gedächtnisspuren und die reduzierten Kosten der drei Beispielwege sind hier von Hand gerechnet (als Rechnung). Die Labelzahlen der Runde 1 und der
Spaltenerzeugung (Tabelle unten) stammen aus dem unabhängigen Handskript der Planung (Standardbibliothek, Brüche); `test_oracle_ng_routen.py` rechnet die Wege und die Schranken
noch einmal durch Aufzählung ohne Labels."""

from fractions import Fraction as Fr

import pytest
from conftest import HAND_TABLE, as_set

import ngr_algorithm as A
import ngr_constants as C
import ngr_evaluation as ev
import ngr_scenario as S

MEMORIES = {"ng1": A.ng(1), "ng2": A.ng(2), "ng3": A.ng(3), "ng4": A.ng(4), "ng5": A.ng(5), "ng6": A.ng(6), "ng7": A.ng(7), "kc2": A.kcyc(2), "kc3": A.kcyc(3)}

# Runde 1 (ein Aufruf des Preisproblems, Dualpreise 2 x Abstand): bester Weg, reduzierte Kosten, erzeugt, verworfen, verdrängt, übrig, Zahl der zulässigen Wege (Aufzählung)
ROUND1 = {
    "ng1": ((7, 6, 7, 6), -18, 62, 27, 5, 30, 89),
    "ng2": ((5, 3, 5, 1), -14, 58, 27, 3, 28, 82),
    "ng3": ((2, 7, 6), -10, 55, 25, 3, 27, 79),
    "ng4": ((2, 7, 6), -10, 55, 22, 6, 27, 79),
    "ng5": ((2, 7, 6), -10, 56, 23, 3, 30, 79),
    "ng6": ((2, 7, 6), -10, 56, 22, 0, 34, 79),
    "ng7": ((2, 7, 6), -10, 56, 20, 0, 36, 79),
    "kc2": ((2, 7, 6), -10, 57, 14, 1, 42, 79),
    "kc3": ((2, 7, 6), -10, 57, 11, 0, 46, 79),
}
# Spaltenerzeugung bis zum Ende (je Runde die beste Spalte, exakter Master): Schranke, Runden, Labels, neue Spalten
COLGEN = {
    "ng1": (Fr(83, 3), 8, 416, 7), "ng2": (Fr(86, 3), 8, 382, 7), "ng3": (Fr(30), 8, 370, 7), "ng4": (Fr(30), 8, 370, 7), "ng5": (Fr(30), 7, 326, 6),
    "ng6": (Fr(30), 7, 326, 6), "ng7": (Fr(30), 7, 326, 6), "kc2": (Fr(30), 7, 328, 6), "kc3": (Fr(30), 7, 328, 6),
}


def test_the_hand_instance_of_the_app_equals_the_table_here(hand):
    inst, pi = hand
    app = S.hand_instance()
    assert app == inst
    assert S.first_round_duals(app) == pi == (0, 6, 6, 10, 6, 6, 6, 10)


def test_neighbourhoods_k1_to_k4_by_hand(hand):
    """Nachbarschaft = der Kunde und seine k - 1 nächsten Kunden nach Manhattan-Abstand; Gleichstand: kleinere Nummer (z. B. Kunde 5: Abstand 2 zu 3 und 4 und 6)."""
    inst, _ = hand
    expected = {
        1: [{1}, {2}, {3}, {4}, {5}, {6}, {7}],
        2: [{1, 2}, {1, 2}, {3, 4}, {3, 4}, {3, 5}, {6, 7}, {6, 7}],
        3: [{1, 2, 4}, {1, 2, 6}, {3, 4, 5}, {3, 4, 5}, {3, 4, 5}, {1, 6, 7}, {1, 6, 7}],
        4: [{1, 2, 4, 5}, {1, 2, 6, 7}, {1, 3, 4, 5}, {1, 3, 4, 5}, {1, 3, 4, 5}, {1, 2, 6, 7}, {1, 2, 6, 7}],
    }
    for k, sets in expected.items():
        masks = A.ng_masks(inst, k)
        assert masks[0] == 0
        assert [as_set(m) for m in masks[1:]] == sets, k


def test_the_neighbourhood_is_not_symmetric_at_k2(hand):
    inst, _ = hand
    masks = A.ng_masks(inst, 2)
    assert (masks[5] >> 3) & 1 and not (masks[3] >> 5) & 1      # Kunde 5 hat Kunde 3 als Nachbarn, Kunde 3 aber Kunde 4
    mutual = [(i, j) for i in range(1, 8) for j in range(i + 1, 8) if (masks[i] >> j) & 1 and (masks[j] >> i) & 1]
    assert mutual == [(1, 2), (3, 4), (6, 7)]


def test_neighbourhoods_are_nested_and_k_n_is_elementary(hand):
    inst, _ = hand
    for k in range(1, 7):
        small, big = A.ng_masks(inst, k), A.ng_masks(inst, k + 1)
        assert all(s & ~b == 0 for s, b in zip(small, big))
    assert all(as_set(m) == set(range(1, 8)) for m in A.ng_masks(inst, 7)[1:])
    assert A.ng_masks(inst, 99) == A.ng_masks(inst, 7)          # k > n zählt wie k = n
    assert A.ng_masks(inst, 0) == A.ng_masks(inst, 1)           # k < 1 zählt wie k = 1


# Gedächtnisspur: (Weg, k) -> Gedächtnis nach jedem Kunden (von Hand: Gedächtnis geschnitten mit NG(j), plus j) und Urteil
TRACES = [
    ((7, 6, 7), 1, [{7}, {6}, {7}], False),
    ((7, 6, 7), 2, [{7}, {6, 7}], True),          # nach 6: {7} ∩ NG(6) = {7}, plus 6 = {6,7}; dann steht 7 im Gedächtnis
    ((7, 6, 7), 3, [{7}, {6, 7}], True),
    ((5, 3, 5, 1), 1, [{5}, {3}, {5}, {1}], False),
    ((5, 3, 5, 1), 2, [{5}, {3}, {3, 5}, {1}], False),   # nach 3: {5} ∩ NG(3) = {5} ∩ {3,4} = {}, plus 3; nach 5: {3} ∩ {3,5} = {3}, plus 5
    ((5, 3, 5, 1), 3, [{5}, {3, 5}], True),
    ((7, 6, 1, 7), 2, [{7}, {6, 7}, {1}, {7}], False),   # nach 1: {6,7} ∩ NG(1) = {6,7} ∩ {1,2} = {}, plus 1 = {1}
]


@pytest.mark.parametrize("walk,k,memories,forbidden", TRACES)
def test_memory_trace_by_hand(hand, walk, k, memories, forbidden):
    inst, _ = hand
    steps = A.memory_trace(inst, k, walk)
    assert [as_set(s.after) for s in steps if not s.forbidden] == memories
    assert len(steps) == len(memories) + (1 if forbidden else 0)            # die Spur endet mit dem ersten verbotenen Besuch
    assert steps[-1].forbidden is forbidden
    if forbidden:
        assert steps[-1].customer in as_set(steps[-1].before)
    assert A.walk_allowed(inst, A.ng(k), walk) is (not forbidden)


def test_each_step_of_the_trace_is_intersection_plus_customer(hand):
    inst, _ = hand
    masks = A.ng_masks(inst, 2)
    for step in A.memory_trace(inst, 2, (5, 3, 5, 1)):
        assert step.kept == step.before & masks[step.customer] == step.before & step.neighbourhood
        assert step.after == step.kept | (1 << step.customer)


def test_kcyc_trace_and_walk_rule(hand):
    inst, _ = hand
    assert A.kcyc_trace(inst, 2, (7, 6, 7))[0] is False
    assert A.kcyc_trace(inst, 2, (7, 6, 1, 7))[0] is True       # Kreis mit drei Kanten
    assert A.kcyc_trace(inst, 3, (7, 6, 1, 7))[0] is False
    assert A.kcyc_trace(inst, 1, (7, 6, 7))[0] is True
    for walk in ((7, 6, 7), (5, 3, 5, 1), (7, 6, 1, 7), (1, 2, 3)):
        for size in (1, 2, 3):
            assert A.walk_allowed(inst, A.kcyc(size), walk) is A.kcyc_trace(inst, size, walk)[0]


def test_reduced_costs_of_the_three_best_walks_by_hand(hand):
    """Länge minus Dualpreise aller Besuche (ein Kunde im Kreis zählt jedes Mal)."""
    inst, pi = hand
    assert A.walk_value(inst, pi, (7, 6, 7, 6), eps=0) == (5 + 2 + 2 + 2 + 3) - (10 + 6 + 10 + 6) == -18
    assert A.walk_value(inst, pi, (5, 3, 5, 1), eps=0) == (3 + 2 + 2 + 4 + 3) - (6 + 10 + 6 + 6) == -14
    assert A.walk_value(inst, pi, (2, 7, 6), eps=0) == (3 + 4 + 2 + 3) - (6 + 10 + 6) == -10
    assert A.route_cost(inst, (7, 6, 7, 6)) == 14


def test_infeasible_walks_have_no_value(hand):
    inst, pi = hand
    assert A.walk_value(inst, pi, (1, 2), eps=0) is None            # Kunde 2 (Fenster bis 16) nach Kunde 1 (ab 18): zu spät
    assert A.walk_value(inst, pi, (2, 3, 4), eps=0) is None         # Last 3 + 3 + 3 = 9 > 6
    assert A.walk_value(inst, pi, (), eps=0) == 0


@pytest.mark.parametrize("name", list(ROUND1))
def test_round_one_table_by_hand_script(hand, name):
    inst, pi = hand
    walk, rc, generated, discarded, displaced, alive, count = ROUND1[name]
    res = A.price(inst, pi, MEMORIES[name], exact=True)
    best_rc, best_walk = A.routes_of(inst, res, 1, exact=True)[0]
    assert (best_walk, best_rc) == (walk, rc)
    assert (res.generated, res.discarded, res.displaced, res.alive) == (generated, discarded, displaced, alive)
    assert res.generated == res.discarded + res.displaced + res.alive and res.dominated == discarded + displaced and not res.aborted
    assert len(A.enumerate_walks(inst, pi, MEMORIES[name], exact=True)) == count


@pytest.mark.parametrize("name", list(COLGEN))
def test_column_generation_on_the_hand_example(hand, name):
    inst, _ = hand
    bound, rounds, labels, new = COLGEN[name]
    cg = A.colgen(inst, MEMORIES[name], A.solve_master_exact, per_round=1, exact=True)
    assert (cg.bound, cg.iterations, cg.labels) == (bound, rounds, labels)
    assert len(cg.columns) - inst.n == new and cg.rounds[-1].new_columns == 0 and cg.rounds[-1].best_walk == ()
    assert not cg.aborted


def test_the_ladder_of_gaps_by_calculation():
    """Lücke zur elementaren Schranke 30 als Rechnung: (30 − 83/3) / 30 = 7/90, (30 − 86/3) / 30 = 4/90."""
    rows = {r.name: r for r in ev.hand_ladder()}
    assert rows["ng k = 1"].gap == pytest.approx(100 * (30 - 83 / 3) / 30) == pytest.approx(100 * 7 / 90)
    assert rows["ng k = 2"].gap == pytest.approx(100 * (30 - 86 / 3) / 30) == pytest.approx(100 * 4 / 90)
    assert round(rows["ng k = 1"].gap, 2) == 7.78 and round(rows["ng k = 2"].gap, 2) == 4.44
    assert all(r.gap == 0 for r in ev.hand_ladder() if r.memory not in (A.ng(1), A.ng(2)))
    assert [r.bound for r in ev.hand_ladder() if r.memory.kind == "ng"] == sorted(r.bound for r in ev.hand_ladder() if r.memory.kind == "ng")


def test_k_cycles_find_the_elementary_bound_with_fewer_labels_than_ng_on_this_one_instance():
    """Nur diese Instanz (kein Befund über k-Zyklen allgemein): K = 2 hat schon die elementare Schranke 30, ng k = 2 erst 86/3."""
    rows = {r.memory: r for r in ev.hand_ladder()}
    assert rows[A.kcyc(2)].bound == 30 and rows[A.ng(2)].bound == Fr(86, 3)
    assert (rows[A.kcyc(2)].labels, rows[A.ng(2)].labels) == (328, 382)


def test_floating_point_run_equals_the_exact_run_on_the_hand_example(hand):
    inst, pi = hand
    for name, memory in MEMORIES.items():
        exact = A.price(inst, pi, memory, exact=True)
        approx = A.price(inst, pi, memory)
        assert (approx.generated, approx.discarded, approx.displaced) == (exact.generated, exact.discarded, exact.displaced), name


def test_exact_master_equals_the_lp_master(hand):
    inst, _ = hand
    cols = [(j,) for j in range(1, 8)]
    pi, value = A.solve_master_exact(inst, cols)
    assert value == sum(2 * inst.d[0][j] for j in range(1, 8)) == 50 and list(pi) == [0] + [2 * inst.d[0][j] for j in range(1, 8)]
    cols += [(2, 7, 6), (5, 3, 5, 1)]
    pi_e, value_e = A.solve_master_exact(inst, cols)
    pi_l, value_l = A.solve_master_lp(inst, cols)
    assert float(value_e) == pytest.approx(value_l, abs=1e-9)
    # Dualzulässigkeit des exakten Masters: Summe der Dualpreise einer Spalte höchstens ihre Länge
    assert all(sum(pi_e[j] for j in w) <= A.route_cost(inst, w) for w in cols)


# --- Einheiten ------------------------------------------------------------------------------------------------------------------------------

def test_next_memory_rules(hand):
    inst, _ = hand
    masks = A.ng_masks(inst, 2)
    bit = lambda *xs: sum(1 << x for x in xs)  # noqa: E731
    assert A.next_memory(A.ng(2), bit(7), 6, masks) == bit(6, 7)       # {7} ∩ NG(6) = {7}, plus 6
    assert A.next_memory(A.ng(2), bit(6, 7), 1, masks) == bit(1)       # {6,7} ∩ NG(1) = {}, plus 1
    assert A.next_memory(A.kcyc(3), (bit(7), bit(6, 7), bit(1, 6, 7)), 5, None) == (bit(5), bit(5, 7), bit(5, 6, 7))
    assert A.start_memory(A.ng(3)) == 0 and A.start_memory(A.kcyc(3)) == (0, 0, 0)
    assert A.forbidden_mask(A.ng(3), bit(2, 4)) == bit(2, 4)
    assert A.forbidden_mask(A.kcyc(3), (bit(7), bit(6, 7), bit(1, 6, 7))) == bit(1, 6, 7)


def test_dominates_needs_every_condition():
    L = A.Label
    memory = A.ng(2)
    base = L(10, 5, 3, 0b0110, 2, 0)
    assert A.dominates(base, L(10, 5, 3, 0b0110, 2, 1), memory)            # Gleichstand in allem: dominiert (das ältere bleibt, entscheidet price)
    assert not A.dominates(base, L(10, 4.9, 3, 0b0110, 2, 1), memory)      # Kosten des anderen kleiner
    assert not A.dominates(base, L(9, 5, 3, 0b0110, 2, 1), memory)         # Zeit des anderen früher
    assert not A.dominates(base, L(10, 5, 2, 0b0110, 2, 1), memory)        # Last des anderen kleiner
    assert not A.dominates(base, L(10, 5, 3, 0b0010, 2, 1), memory)        # Gedächtnis von base keine Teilmenge
    assert A.dominates(L(10, 5, 3, 0b0010, 2, 0), L(10, 5, 3, 0b0110, 2, 1), memory)   # Teilmenge genügt
    # k-Zyklen: jeder Suffix außer dem ersten (der Kunde selbst) muss Teilmenge sein
    a = L(1, 1, 1, (0b100, 0b0110, 0b1110), 2, 0)
    b = L(1, 1, 1, (0b100, 0b0110, 0b1111), 2, 1)
    assert A.dominates(a, b, A.kcyc(3)) and not A.dominates(b, a, A.kcyc(3))
    c = L(1, 1, 1, (0b100, 0b1000, 0b1110), 2, 1)
    assert not A.dominates(a, c, A.kcyc(3))                                # Suffix der Länge 2 von a nicht in dem von c


def test_dominates_uses_the_tolerance_only_in_float_mode():
    L = A.Label
    near = L(10, 5 + 1e-12, 3, 0, 2, 0)
    assert A.dominates(L(10, 5, 3, 0, 2, 0), near, A.ng(1))
    assert not A.dominates(L(10, 5 + 1e-12, 3, 0, 2, 0), L(10, 5, 3, 0, 2, 1), A.ng(1), eps=0)


def test_extend_checks_memory_load_and_window(hand):
    inst, pi = hand
    masks = A.ng_masks(inst, 2)
    ng2 = A.ng(2)
    start = A.Label(0, 0, 0, 0, 0, -1)
    at2 = A.extend(inst, pi, ng2, masks, start, 0, 2, eps=0)               # Depot -> 2: Ankunft 3 (keine Bedienzeit am Depot), Fenster ab 3
    assert at2 == A.Label(3, 3 - 6, 3, 1 << 2, 2, 0)
    assert A.extend(inst, pi, ng2, masks, start, 0, 1, eps=0).time == 18   # Ankunft 3, Fenster ab 18: Warten bis 18
    at1 = A.extend(inst, pi, ng2, masks, at2, 1, 1, eps=0)                 # 2 -> 1: Ankunft 3 + 2 + 2 = 7, Warten bis 18; Last 3 + 1; Gedächtnis {2} ∩ NG(1) plus 1
    assert at1 == A.Label(18, (3 - 6) + 2 - 6, 4, (1 << 1) | (1 << 2), 1, 1)
    assert A.extend(inst, pi, ng2, masks, at2, 1, 2, eps=0) is None        # derselbe Kunde direkt wieder
    assert A.extend(inst, pi, ng2, masks, at1, 2, 3, eps=0) is None        # Last 4 + 3 = 7 > 6
    assert A.extend(inst, pi, ng2, masks, at1, 2, 5, eps=0) is None        # Ankunft 18 + 2 + 4 = 24 > Fensterende 12
    assert A.extend(inst, pi, ng2, masks, at2, 1, 3, eps=0).time == 13     # Ankunft 3 + 2 + 8 = 13 <= 15, Last 6 = Kapazität (inklusive Grenze)
    at7 = A.extend(inst, pi, ng2, masks, start, 0, 7, eps=0)
    at6 = A.extend(inst, pi, ng2, masks, at7, 1, 6, eps=0)
    assert at6.mem == (1 << 6) | (1 << 7)
    assert A.extend(inst, pi, ng2, masks, at6, 2, 7, eps=0) is None        # 7 steht im Gedächtnis: Kreis 7-6-7 bei k = 2 verboten
    assert A.extend(inst, pi, A.ng(1), A.ng_masks(inst, 1), A.extend(inst, pi, A.ng(1), A.ng_masks(inst, 1), at7, 1, 6, eps=0), 2, 7, eps=0) is not None   # bei k = 1 erlaubt


def test_route_cost_and_walk_of(hand):
    inst, pi = hand
    assert A.route_cost(inst, (7,)) == 10 and A.route_cost(inst, ()) == 0
    res = A.price(inst, pi, A.ng(2), exact=True)
    rc, li = min(res.ended)
    assert A.walk_of(res.labels, li)[-1] == res.labels[li].node and A.walk_value(inst, pi, A.walk_of(res.labels, li), eps=0) == rc


def test_aborting_at_max_labels_is_reported(hand):
    inst, pi = hand
    res = A.price(inst, pi, A.ng(7), max_labels=10, exact=True)
    assert res.aborted and res.generated < 20
    cg = A.colgen(inst, A.ng(7), A.solve_master_exact, max_labels=10, exact=True)
    assert cg.aborted and cg.bound is None


def test_worst_case_at_the_slider_maximum_does_not_hang_or_abort():
    """Kein Zeitvergleich (DEMO-PLAYBOOK §1c): Der Versuch mit den größten Reglerwerten (30 Kunden, Breite 100, größtes k = 12) endet ohne Abbruch bei MAX_LABELS_PER_CALL,
    und die Schranken steigen mit k."""
    rows = ev.live_ladder(C.N_MAX, max(C.WIDTH_OPTIONS), C.DEFAULT_SEED, max(C.KMAX_OPTIONS))
    assert [r.k for r in rows] == list(C.LIVE_LADDER)
    assert not any(r.aborted for r in rows)
    bounds = [r.bound for r in rows]
    assert all(a <= b + 1e-6 for a, b in zip(bounds, bounds[1:]))
    assert max(r.labels for r in rows) < C.MAX_LABELS_PER_CALL * len(rows)


def test_hand_table_and_the_scenario_module_agree_on_every_customer():
    app = S.hand_instance()
    for j, (point, load, early, late) in HAND_TABLE.items():
        assert (app.points[j], app.demand[j], app.ready[j], app.due[j]) == (point, load, early, late)
