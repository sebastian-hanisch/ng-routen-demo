"""Orakel-Test: das Label-Verfahren mit begrenztem Gedächtnis gegen einen unabhängigen Rechenweg (ORACLE-PLAYBOOK §2 und §5, DEMO-PLAYBOOK §12).

Orakel: Tiefensuche über **alle** zulässigen Wege (nicht nur die elementaren) mit eigenem Stapel. Jeder Weg wird von vorn nachgerechnet (Zeit, Last, Fenster, Kosten), ohne Labels,
ohne Dominanz und ohne Funktion aus dem Kern der Demo. Die Gedächtnisregel steht im Orakel als Mengen-Simulation (`set`), nicht als Bitmaske; die Nachbarschaften kommen aus
`numpy.argsort(kind="stable")` statt aus dem Kern. Für ng k = 1 prüft das Orakel nur „kein Kunde direkt nach sich selbst“, für k = n „jeder Kunde höchstens einmal“, für k-Zyklen den
Abstand der Wiederholungen. Das Orakel selbst ist am Handbeispiel geprüft (89, 82 und 79 zulässige Wege, wie die Aufzählung der Planung). Der Master über alle aufgezählten Wege wird
mit `scipy.optimize.linprog` gelöst (der Kern benutzt dafür die Spaltenerzeugung). Geprüft werden das Hauptergebnis, die angezeigten Zähler (Zahl der zulässigen Wege, Schranken) und die
Trennschärfe: Die Varianten müssen sich auf mindestens einer Instanz unterscheiden, sonst taugt der Vergleich nichts."""

import random

import numpy as np
import pytest
from conftest import as_set

import ngr_algorithm as A
import ngr_scenario as S

EPS = 1e-9


def oracle_neighbours(inst, k):
    """NG(j) als Menge: j und die k - 1 nächsten Kunden, mit numpy (stabile Sortierung: Gleichstand heißt kleinere Nummer)."""
    d = np.array(inst.d, dtype=float)
    out = {}
    for j in range(1, inst.n + 1):
        order = [i for i in np.argsort(d[j, 1:], kind="stable") + 1]
        out[j] = set(order[:k]) | {j}
    return out


def rule_ok(kind, size, nb, walk):
    """Darf der Weg die Gedächtnisregel erfüllen? Mengen-Simulation für ng, Positionsregel für k-Zyklen, Sonderfälle k = 1 und elementar."""
    if kind == "elem":
        return len(set(walk)) == len(walk)
    if kind == "kcyc":
        last = {}
        for pos, j in enumerate(walk):
            if j in last and pos - last[j] <= size:
                return False
            last[j] = pos
        return True
    if size == 1:                      # ng k = 1: nur derselbe Kunde direkt wieder verboten
        return all(a != b for a, b in zip(walk, walk[1:]))
    memory = set()
    for j in walk:
        if j in memory:
            return False
        memory = (memory & nb[j]) | {j}
    return True


def simulate(inst, pi, walk):
    """(reduzierte Kosten einschließlich Rückfahrt) oder None, wenn ein Fenster, die Last oder die Rückkehrzeit verletzt ist."""
    time, load, cost, at = 0, 0, 0, 0
    for j in walk:
        arrive = time + (inst.service if at != 0 else 0) + inst.d[at][j]
        load += inst.demand[j]
        if arrive > inst.due[j] + EPS or load > inst.capacity:
            return None
        time = max(arrive, inst.ready[j])
        cost += inst.d[at][j] - pi[j]
        at = j
    if time + inst.service + inst.d[at][0] > inst.horizon + EPS:
        return None
    return cost + inst.d[at][0]


def oracle_walks(inst, pi, kind, size):
    """Alle zulässigen Wege mit mindestens einem Kunden, die die Regel erfüllen, als {Weg: reduzierte Kosten}; Tiefensuche mit eigenem Stapel über die Präfixe."""
    nb = oracle_neighbours(inst, size) if kind == "ng" else None
    found = {}
    stack = [()]
    while stack:
        walk = stack.pop()
        if walk:
            value = simulate(inst, pi, walk)
            if value is not None:
                found[walk] = value
        for j in range(1, inst.n + 1):
            longer = walk + (j,)
            if not rule_ok(kind, size, nb, longer):
                continue
            # Präfix zulässig (ohne Rückkehr)? Sonst kann keine Verlängerung zulässig sein.
            time, load, at, ok = 0, 0, 0, True
            for c in longer:
                arrive = time + (inst.service if at != 0 else 0) + inst.d[at][c]
                load += inst.demand[c]
                if arrive > inst.due[c] + EPS or load > inst.capacity:
                    ok = False
                    break
                time, at = max(arrive, inst.ready[c]), c
            if ok:
                stack.append(longer)
    return found


def kernel_memory(kind, size, n):
    return A.ng(n) if kind == "elem" else A.ng(size) if kind == "ng" else A.kcyc(size)


def cases(n=6, seeds=range(10), widths=(40, 100)):
    for seed in seeds:
        for width in widths:
            inst = S.make_instance(n, seed, width)
            rng = random.Random(1000 + seed)
            yield seed, width, inst, (0.0,) + tuple(rng.uniform(20, 70) for _ in range(n))


VARIANTS = [("ng", 1), ("ng", 2), ("ng", 3), ("elem", 6), ("kcyc", 2), ("kcyc", 3)]


def test_oracle_on_the_hand_example(hand):
    """Das Orakel selbst: 89, 82, 79 zulässige Wege und die besten Wege der Handrechnung (Aufzählung der Planung)."""
    inst, pi = hand
    expected = {("ng", 1): (89, -18), ("ng", 2): (82, -14), ("ng", 3): (79, -10), ("elem", 7): (79, -10), ("kcyc", 2): (79, -10), ("kcyc", 3): (79, -10)}
    for (kind, size), (count, best) in expected.items():
        walks = oracle_walks(inst, pi, kind, size)
        assert len(walks) == count and min(walks.values()) == best, (kind, size)
    walks = oracle_walks(inst, pi, "ng", 1)
    assert min(walks, key=lambda w: (walks[w], w)) == (7, 6, 7, 6)


def test_neighbourhoods_equal_the_numpy_oracle_on_random_instances():
    for seed in range(20):
        inst = S.make_instance(12, seed, 60, clustered=seed % 2 == 1)
        for k in (1, 2, 3, 5, 8, 12):
            masks = A.ng_masks(inst, k)
            oracle = oracle_neighbours(inst, k)
            assert all(as_set(masks[j]) == oracle[j] for j in range(1, 13)), (seed, k)


def test_memory_rule_as_set_simulation_equals_the_whole_walk_property_of_the_kernel():
    """Die Mengen-Simulation des Orakels und die Wegeigenschaft des Kerns (`walk_allowed`) sagen für zufällige Folgen dasselbe."""
    rng = random.Random(5)
    inst = S.make_instance(8, 3, 100)
    for k in (2, 3, 5):
        nb = oracle_neighbours(inst, k)
        for _ in range(400):
            walk = tuple(rng.randint(1, 8) for _ in range(rng.randint(1, 9)))
            if any(a == b for a, b in zip(walk, walk[1:])):
                continue
            assert rule_ok("ng", k, nb, walk) is A.walk_allowed(inst, A.ng(k), walk), (k, walk)


@pytest.mark.parametrize("kind,size", VARIANTS)
def test_labeling_finds_the_oracle_best_route(kind, size):
    """Beste Route und ihre reduzierten Kosten: Label-Verfahren (mit Dominanz) gleich Aufzählung. Jede gelieferte Route steht in der Aufzählung mit denselben Kosten
    (Dominanz garantiert nur den besten Weg, nicht die zweit- und drittbesten, deshalb wird nur dieser verglichen)."""
    for seed, width, inst, pi in cases():
        walks = oracle_walks(inst, pi, kind, size)
        best_value = min(walks.values(), default=0)
        res = A.price(inst, pi, kernel_memory(kind, size, inst.n))
        found = A.routes_of(inst, res)
        if best_value >= -1e-7:
            assert found == [], (kind, size, seed, width)
            continue
        # Gleichstand der reduzierten Kosten ist möglich (ein Weg mit denselben Kanten in anderer Reihenfolge): verglichen werden die Kosten, und der gelieferte Weg muss
        # in der Aufzählung mit denselben Kosten stehen.
        assert found[0][0] == pytest.approx(best_value, abs=1e-6) and walks[found[0][1]] == pytest.approx(best_value, abs=1e-9), (kind, size, seed, width)
        assert len(found) <= 15 and [rc for rc, _ in found] == sorted(rc for rc, _ in found)
        for rc, walk in found:
            assert walk in walks and walks[walk] == pytest.approx(rc, abs=1e-9)
            assert A.walk_value(inst, pi, walk) == pytest.approx(rc, abs=1e-9)


def test_the_kernel_enumeration_equals_the_oracle_enumeration():
    for seed, width, inst, pi in cases(n=5, seeds=range(6)):
        for kind, size in (("ng", 1), ("ng", 2), ("kcyc", 2)):
            mine = A.enumerate_walks(inst, pi, kernel_memory(kind, size, inst.n))
            theirs = oracle_walks(inst, pi, kind, size)
            assert {w for _, w in mine} == set(theirs), (kind, size, seed, width)
            assert [v for v, _ in mine] == pytest.approx(sorted(theirs.values()), abs=1e-9)


@pytest.mark.parametrize("kind,size", [("ng", 1), ("ng", 2), ("elem", 5), ("kcyc", 2)])
def test_the_column_generation_bound_equals_the_master_over_all_oracle_walks(kind, size):
    """Schranke der Spaltenerzeugung = Zielwert des Masters über alle zulässigen Wege der Regel (Überdeckung, linprog)."""
    scipy_optimize = pytest.importorskip("scipy.optimize")
    for seed, width, inst, _ in cases(n=5, seeds=range(5), widths=(100,)):
        walks = list(oracle_walks(inst, (0.0,) * 6, kind, size))
        cols = [(j,) for j in range(1, 6)] + walks
        a = np.zeros((5, len(cols)))
        for c, w in enumerate(cols):
            for j in w:
                a[j - 1, c] += 1
        cost = [A.route_cost(inst, w) for w in cols]
        ref = scipy_optimize.linprog(cost, A_ub=-a, b_ub=-np.ones(5), bounds=(0, None), method="highs").fun
        cg = A.colgen(inst, kernel_memory(kind, size, 5), A.solve_master_lp)
        assert cg.bound == pytest.approx(ref, abs=1e-6), (kind, size, seed)


def test_selectivity_the_variants_differ_on_some_instance():
    """Trennschärfe (Nullspalte = Bug-Signal): jede Stufe weicht von der Nachbarstufe auf mindestens einer Instanz ab, sonst wäre der Vergleich oben für jede Variante bestanden."""
    pairs = [(("ng", 1), ("ng", 2)), (("ng", 2), ("ng", 3)), (("ng", 2), ("elem", 6)), (("ng", 2), ("kcyc", 2)), (("kcyc", 2), ("kcyc", 3))]
    for (ka, sa), (kb, sb) in pairs:
        differing = 0
        for seed, width, inst, pi in cases():
            a = A.routes_of(inst, A.price(inst, pi, kernel_memory(ka, sa, inst.n)), 1)
            b = A.routes_of(inst, A.price(inst, pi, kernel_memory(kb, sb, inst.n)), 1)
            differing += (a[0] if a else None) != (b[0] if b else None)
        assert differing > 0, ((ka, sa), (kb, sb))


def test_bounds_of_the_ladder_differ_between_k1_and_k_n_on_some_instance():
    gaps = 0
    for seed, width, inst, _ in cases(n=7, seeds=range(6), widths=(100,)):
        low = A.colgen(inst, A.ng(1), A.solve_master_lp).bound
        high = A.colgen(inst, A.ng(7), A.solve_master_lp).bound
        assert low <= high + 1e-6
        gaps += high - low > 1e-6
    assert gaps > 0


def test_oracle_with_dual_prices_zero_finds_no_improving_route():
    for seed, width, inst, _ in cases(n=5, seeds=range(4)):
        pi = (0.0,) * 6
        assert not [1 for v in oracle_walks(inst, pi, "ng", 2).values() if v < -1e-7]
        assert A.routes_of(inst, A.price(inst, pi, A.ng(2))) == []
