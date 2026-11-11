"""Eigenschaftstests (ORACLE-PLAYBOOK §5.2): Aussagen, die für das Verfahren gelten müssen, ohne dass man das richtige Ergebnis kennt.

Jede Eigenschaft ist eine belegte Aussage über das Verfahren (die Wegmengen der Gedächtnisse liegen ineinander, die Dominanz ändert das Ergebnis nicht, Umnummerieren und Skalieren
ändern nur Namen und Einheiten), keine Beschreibung des heutigen Verhaltens. Instanzen: feste Zufalls-Seeds, kleine Kundenzahl (unter 10 Sekunden)."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import ngr_algorithm as A
import ngr_scenario as S
from ngr_scenario import Instance

ROOT = Path(__file__).resolve().parent.parent
pytest.importorskip("scipy")


def instances(n=8, seeds=range(8), widths=(60, 100)):
    for seed in seeds:
        for width in widths:
            yield seed, width, S.make_instance(n, seed, width)


def test_bounds_rise_with_k_and_never_exceed_the_elementary_bound():
    """Die Wegmengen der Gedächtnisse liegen ineinander (k Nachbarn ⊆ k + 1 Nachbarn, k = n ist elementar): z(1) <= z(2) <= ... <= z(n)."""
    for seed, width, inst in instances():
        bounds = [A.colgen(inst, A.ng(k), A.solve_master_lp).bound for k in (1, 2, 3, 5, 8)]
        assert all(a <= b + 1e-6 for a, b in zip(bounds, bounds[1:])), (seed, width, bounds)


def test_k_cycles_never_exceed_the_elementary_bound_and_are_not_ordered_against_ng():
    """k-Zyklen erlauben mehr Wege als elementar, also Schranke <= elementar. Mit ng sind sie nicht vergleichbar (keine Aussage, nur dieser Test der schwachen Richtung)."""
    for seed, width, inst in instances(n=7, seeds=range(6)):
        elementary = A.colgen(inst, A.ng(7), A.solve_master_lp).bound
        for K in (2, 3):
            assert A.colgen(inst, A.kcyc(K), A.solve_master_lp).bound <= elementary + 1e-6, (seed, width, K)


def test_k_cycles_with_k_equal_to_one_behave_like_ng_with_k_one():
    for seed, width, inst in instances(n=8, seeds=range(5), widths=(100,)):
        a = A.colgen(inst, A.kcyc(1), A.solve_master_lp)
        b = A.colgen(inst, A.ng(1), A.solve_master_lp)
        assert a.bound == pytest.approx(b.bound, abs=1e-6), (seed, width)


def test_wider_windows_never_raise_the_bound():
    """Gleiche Kunden und Lasten, breitere Fenster (um dieselbe Mitte, gleiche Zufallszahlen): mehr zulässige Wege, also eine Schranke, die nicht steigt."""
    for seed in range(8):
        for k in (1, 3):
            narrow = A.colgen(S.make_instance(9, seed, 40), A.ng(k), A.solve_master_lp).bound
            wide = A.colgen(S.make_instance(9, seed, 100), A.ng(k), A.solve_master_lp).bound
            assert wide <= narrow + 1e-6, (seed, k)


def renumbered(inst: Instance, perm):
    """Kunden umnummerieren: neuer Kunde i ist der alte Kunde perm[i - 1] (perm ist eine Anordnung von 1..n)."""
    order = [0] + list(perm)
    pts = tuple(inst.points[o] for o in order)
    d = tuple(tuple(inst.d[a][b] for b in order) for a in order)
    return Instance(inst.n, pts, d, tuple(inst.demand[o] for o in order), tuple(inst.ready[o] for o in order), tuple(inst.due[o] for o in order),
                    inst.service, inst.horizon, inst.capacity)


def test_renumbering_the_customers_changes_only_names():
    """Zufällige Abstände haben keine Gleichstände; dann hängen Nachbarschaften, Schranken und der beste Wert nicht an der Nummerierung."""
    import random

    rng = random.Random(3)
    for seed, width, inst in instances(n=8, seeds=range(5), widths=(100,)):
        perm = list(range(1, 9))
        rng.shuffle(perm)
        other = renumbered(inst, perm)
        pi = [0.0] + [20 + 5 * j + (seed % 3) for j in range(1, 9)]
        pi_other = [0.0] + [pi[o] for o in perm]
        for memory in (A.ng(2), A.ng(5), A.kcyc(2)):
            a = A.routes_of(inst, A.price(inst, pi, memory), 1)
            b = A.routes_of(other, A.price(other, pi_other, memory), 1)
            assert (a[0][0] if a else 0) == pytest.approx(b[0][0] if b else 0, abs=1e-9), (seed, memory)
        assert A.colgen(inst, A.ng(3), A.solve_master_lp).bound == pytest.approx(A.colgen(other, A.ng(3), A.solve_master_lp).bound, abs=1e-6)


def test_scaling_lengths_times_and_dual_prices_by_two_scales_the_values_and_keeps_the_counts():
    """Alle Entfernungen, Zeiten, Fenster, Bedienzeit, Horizont und Dualpreise mit 2 multipliziert (exakt in Gleitkomma): dieselben Labels, doppelte reduzierte Kosten."""
    for seed, width, inst in instances(n=8, seeds=range(5), widths=(60,)):
        big = Instance(inst.n, inst.points, tuple(tuple(2 * x for x in row) for row in inst.d), inst.demand, tuple(2 * x for x in inst.ready),
                       tuple(2 * x for x in inst.due), 2 * inst.service, 2 * inst.horizon, inst.capacity)
        pi = [0.0] + [30.0 + 3 * j for j in range(1, 9)]
        for memory in (A.ng(1), A.ng(3), A.kcyc(2)):
            a, b = A.price(inst, pi, memory), A.price(big, [2 * x for x in pi], memory)
            assert (a.generated, a.discarded, a.displaced) == (b.generated, b.discarded, b.displaced), (seed, memory)
            best_a, best_b = A.routes_of(inst, a, 1), A.routes_of(big, b, 1)
            assert [w for _, w in best_a] == [w for _, w in best_b]
            assert [2 * rc for rc, _ in best_a] == pytest.approx([rc for rc, _ in best_b], abs=1e-9)


def test_label_counts_add_up_and_alive_labels_are_not_dead():
    for seed, width, inst in instances(n=8, seeds=range(5)):
        pi = [0.0] + [25.0 + 4 * j for j in range(1, 9)]
        for memory in (A.ng(2), A.kcyc(2)):
            res = A.price(inst, pi, memory)
            assert res.generated == len(res.labels) + res.discarded and res.displaced == sum(res.dead)
            assert res.alive == sum(1 for d in res.dead if not d)


def test_a_larger_memory_never_finds_a_better_best_route_than_a_smaller_one():
    """Wegmengen ineinander: das Preisproblem mit größerem k hat Wege nur verloren, der beste Wert steigt (zu 0, wenn kein Weg verbessert)."""
    for seed, width, inst in instances(n=7, seeds=range(6)):
        pi = [0.0] + [22.0 + 6 * j for j in range(1, 8)]
        values = []
        for k in (1, 2, 3, 5, 7):
            found = A.routes_of(inst, A.price(inst, pi, A.ng(k)), 1)
            values.append(found[0][0] if found else 0.0)
        assert all(a <= b + 1e-9 for a, b in zip(values, values[1:])), (seed, width, values)


def test_same_input_same_output_in_a_second_process_with_other_hash_seeds():
    """Kein Ergebnis hängt an der Reihenfolge von Mengen oder Wörterbüchern: dieselbe Rechnung in zwei Prozessen mit PYTHONHASHSEED = 1 und 2."""
    code = ("import json, ngr_algorithm as A, ngr_scenario as S;"
            "i = S.make_instance(14, 4, 100.0); r = A.colgen(i, A.ng(3), A.solve_master_lp); r2 = A.colgen(i, A.kcyc(2), A.solve_master_lp);"
            "print(json.dumps([r.bound, r.iterations, r.labels, r2.bound, r2.labels]))")
    out = []
    for hash_seed in ("1", "2"):
        env = {**os.environ, "PYTHONHASHSEED": hash_seed, "PYTHONPATH": str(ROOT)}
        out.append(json.loads(subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, cwd=ROOT, check=True).stdout))
    assert out[0] == out[1]
