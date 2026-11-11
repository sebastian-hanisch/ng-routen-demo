"""Randfälle, an denen Kernroutinen erfahrungsgemäß brechen (DEMO-PLAYBOOK §12): ein und zwei Kunden, k an den Rändern, Gleichstand der Abstände, die Asymmetrie der Nachbarschaft,
Grenzen inklusive, Dualpreise 0, Fenster, die nie einen zweiten Besuch zulassen, Eingabe des Wegs."""

import pytest
from conftest import as_set

import ngr_algorithm as A
import ngr_evaluation as ev
import ngr_scenario as S
from ngr_scenario import Instance


def one_customer(due=3, horizon=8):
    """Depot (0, 0), ein Kunde im Abstand 3 (Fenster [0, due], Bedienzeit 2): Ankunft 3, Rückkehr 3 + 2 + 3 = 8."""
    pts = ((0, 0), (3, 0))
    d = ((0, 3), (3, 0))
    return Instance(1, pts, d, (0, 1), (0, 0), (horizon, due), 2, horizon, 5)


def two_customers():
    pts = ((0, 0), (3, 0), (6, 0))
    d = tuple(tuple(abs(a[0] - b[0]) for b in pts) for a in pts)
    return Instance(2, pts, d, (0, 1, 1), (0, 0, 0), (60, 60, 60), 2, 60, 5)


def test_one_customer_every_memory_gives_the_single_trip():
    inst = one_customer()
    pi = (0, 10)
    for memory in (A.ng(1), A.ng(5), A.kcyc(1), A.kcyc(2)):
        res = A.price(inst, pi, memory, exact=True)
        assert A.routes_of(inst, res, exact=True) == [(3 + 3 - 10, (1,))], memory
    cg = A.colgen(inst, A.ng(1), A.solve_master_exact, exact=True)
    assert (cg.bound, cg.iterations, cg.columns) == (6, 1, ((1,),))   # die Einzelfahrt ist schon im Master (2 x 3 = 6), Dualpreis 6, reduzierte Kosten 0: nichts verbessert


def test_exactly_two_customers():
    """n = 2: der kleinste Fall, in dem ein Kreis 1-2-1 möglich ist; k = 1 erlaubt ihn, k = 2 (elementar) verbietet ihn."""
    inst = two_customers()
    pi = (0, 20, 20)
    walks1 = {w for _, w in A.enumerate_walks(inst, pi, A.ng(1), exact=True)}
    walks2 = {w for _, w in A.enumerate_walks(inst, pi, A.ng(2), exact=True)}
    assert (1, 2, 1) in walks1 and (1, 2, 1) not in walks2
    assert walks2 == {(1,), (2,), (1, 2), (2, 1)}
    assert A.ng_masks(inst, 5) == A.ng_masks(inst, 2)                  # k > n zählt wie k = n


def test_k_greater_than_n_counts_like_n(hand):
    inst, pi = hand
    a = A.price(inst, pi, A.ng(7), exact=True)
    b = A.price(inst, pi, A.ng(50), exact=True)
    assert (a.generated, a.discarded, a.displaced) == (b.generated, b.discarded, b.displaced)
    assert A.ng_masks(inst, 50) == A.ng_masks(inst, 7)


def test_ties_in_the_distances_are_resolved_by_the_smaller_number():
    """Kunden 1, 2 und 3 stehen im gleichen Abstand zu Kunde 4: Bei k = 2 gehört der mit der kleinsten Nummer (1) zur Nachbarschaft, nicht 2 oder 3."""
    pts = ((0, 0), (10, 0), (0, 10), (-10, 0), (0, 0))   # Kunde 4 im Depot; Kunden 1, 2, 3 jeweils Abstand 10 (Manhattan)
    d = tuple(tuple(abs(a[0] - b[0]) + abs(a[1] - b[1]) for b in pts) for a in pts)
    inst = Instance(4, pts, d, (0, 1, 1, 1, 1), (0,) * 5, (100,) * 5, 1, 100, 9)
    assert as_set(A.ng_masks(inst, 2)[4]) == {1, 4}
    assert as_set(A.ng_masks(inst, 3)[4]) == {1, 2, 4}


def test_the_asymmetry_of_the_neighbourhood(hand):
    inst, _ = hand
    masks = A.ng_masks(inst, 2)
    assert (masks[5] >> 3) & 1 == 1 and (masks[3] >> 5) & 1 == 0
    assert A.walk_allowed(inst, A.ng(2), (5, 3, 5)) and not A.walk_allowed(inst, A.ng(2), (3, 5, 3))   # 3-5-3: Kunde 5 hat 3, also bleibt 3 im Gedächtnis


def test_window_end_and_horizon_are_inclusive():
    """Ankunft genau zum Fensterende und Rückkehr genau zum Horizont sind erlaubt, ein bisschen mehr nicht."""
    pi = (0, 10)
    assert A.routes_of(one_customer(3, 8), A.price(one_customer(3, 8), pi, A.ng(1), exact=True), exact=True)
    assert A.walk_value(one_customer(3, 8), pi, (1,), eps=0) is not None
    assert A.walk_value(one_customer(2.99, 8), pi, (1,), eps=0) is None            # Fenster endet vor der Ankunft
    assert A.walk_value(one_customer(3, 7.99), pi, (1,), eps=0) is None            # Rückkehr nach dem Horizont
    assert A.routes_of(one_customer(2.99, 8), A.price(one_customer(2.99, 8), pi, A.ng(1), exact=True), exact=True) == []


def test_dual_prices_zero_find_nothing_and_the_column_generation_stops_in_round_one(hand):
    inst, _ = hand
    zero = (0,) * 8
    assert A.routes_of(inst, A.price(inst, zero, A.ng(3), exact=True), exact=True) == []
    cg = A.colgen(inst, A.ng(3), lambda i, cols: (zero, 0), exact=True)
    assert cg.iterations == 1 and cg.rounds[0].new_columns == 0 and cg.bound == 0


def test_windows_that_never_allow_a_second_visit_give_the_same_bound_for_every_k():
    """Enge Fenster (Breite 1) und sehr früher Horizont: Kein Weg hat zwei Besuche desselben Kunden, jedes Gedächtnis liefert dieselbe Schranke und dieselbe Labelzahl."""
    inst = S.make_instance(8, 3, 1.0)
    runs = [A.colgen(inst, A.ng(k), A.solve_master_lp) for k in (1, 2, 4, 8)]
    assert len({round(r.bound, 6) for r in runs}) == 1
    walks_k1 = {w for _, w in A.enumerate_walks(inst, [0.0] + [50.0] * 8, A.ng(1))}
    assert all(len(set(w)) == len(w) for w in walks_k1)                              # auch bei k = 1 gibt es keinen Kreis


def test_make_instance_is_deterministic_and_clustered_differs():
    assert S.make_instance(10, 4, 40) == S.make_instance(10, 4, 40)
    assert S.make_instance(10, 4, 40) != S.make_instance(10, 5, 40)
    assert S.make_instance(10, 4, 40).points != S.make_instance(10, 4, 40, clustered=True).points
    inst = S.make_instance(12, 2, 100)
    assert all(inst.ready[i] <= inst.due[i] for i in range(1, 13)) and all(inst.d[i][i] == 0 for i in range(13))


def test_parse_walk_accepts_and_rejects(hand):
    assert ev.parse_walk("5-3-5-1", 7) == (5, 3, 5, 1)
    assert ev.parse_walk(" 7, 6 ,7 ", 7) == (7, 6, 7)
    assert ev.parse_walk("7 6 1 7", 7) == (7, 6, 1, 7)
    assert ev.parse_walk("1", 7) == (1,)
    for bad in ("", "  ", "-", "8-1", "0-1", "a-b", "1--x", "7-7", "1-2-2-3", "1.5-2"):
        assert ev.parse_walk(bad, 7) is None, bad
    assert ev.parse_walk("-".join(["1", "2"] * 6), 7) is not None and ev.parse_walk("-".join(["1", "2"] * 7), 7) is None     # 12 Besuche erlaubt, 14 nicht


def test_empty_walk_and_single_visit_have_no_forbidden_step(hand):
    inst, _ = hand
    assert A.memory_trace(inst, 2, ()) == []
    assert A.walk_allowed(inst, A.ng(1), ()) and A.walk_allowed(inst, A.kcyc(3), (4,))
    a = ev.analyse_walk(2, (4,))
    assert a.allowed and a.feasible is True


def test_formatting_helpers():
    from fractions import Fraction as Fr

    assert ev.fmt_bound(Fr(83, 3)) == "83/3 (≈ 27,67)" and ev.fmt_bound(Fr(30)) == "30" and ev.fmt_bound(27.5) == "27,50"
    assert ev.fmt_num(-18) == "−18" and ev.fmt_num(Fr(-10)) == "−10" and ev.fmt_num(1.5) == "1,50"
    assert ev.fmt_int(1234567) == "1 234 567"
    assert ev.fmt_set(0b1010, 3) == "{1,3}" and ev.fmt_set(0, 3) == "{}"
    assert ev.gap_percent(30, 30) == 0 and ev.gap_percent(0, 5) == 0 and ev.gap_percent(100, 99) == pytest.approx(1.0)
    assert ev.gap_percent(100, 100 - 1e-9) == 0.0                                    # Rauschen unter ZERO_GAP_PERCENT gilt als 0
