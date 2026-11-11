"""Kennzahlen, Verdikte (reine Funktionen) und Messreihen der Demo.

Jedes Verdikt ist eine reine Funktion `verdict_*(...) -> (Art, Text)`; die App ruft `getattr(st, Art)(Text)`, `tests/test_verdicts.py` prüft Schwellen und jede Zahl
im Text an handgesetzten Werten. Die festen Messreihen (data/*.json) laden `load_*`; jede Zeile nennt ihre Quelle (Datei und Zeile der Messausgabe der Planung).
Alle Tabellen der Messreihen werden hier aus den Zeilen berechnet, nicht abgelegt."""

import json
import statistics
from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
from typing import NamedTuple

import ngr_algorithm as A
import ngr_constants as C
from ngr_scenario import Instance, first_round_duals, hand_instance, make_instance

DATA_DIR = Path(__file__).resolve().parent / "data"


# --- Zahlen und Mengen als Text -------------------------------------------------------------------------------------------------------------

def fmt_num(x, digits: int = 2) -> str:
    """Zahl mit deutschem Dezimalkomma und echtem Minuszeichen; ganze Zahlen ohne Nachkommastellen."""
    if isinstance(x, Fraction):
        x = float(x)
    if float(x).is_integer():
        text = f"{int(x)}"
    else:
        text = f"{x:.{digits}f}".replace(".", ",")
    return text.replace("-", "−")


def fmt_dec(x: float, digits: int = 2) -> str:
    """Dezimalzahl mit immer gleich vielen Nachkommastellen und deutschem Komma (1,00 statt 1)."""
    return f"{float(x):.{digits}f}".replace(".", ",").replace("-", "−")


def fmt_int(n: int) -> str:
    """Ganze Zahl mit geschütztem Leerzeichen als Tausendertrenner (4 424 statt 4424)."""
    return f"{n:,}".replace(",", " ")


def fmt_pct(x: float, digits: int = 1) -> str:
    """Prozentwert mit deutschem Dezimalkomma (x ist schon in Prozent)."""
    return fmt_dec(x, digits) + " %"


def fmt_bound(x) -> str:
    """Schranke: ganze Zahl, Bruch mit Näherung (83/3 ≈ 27,67) oder Dezimalzahl."""
    if isinstance(x, Fraction) and x.denominator != 1:
        return f"{x.numerator}/{x.denominator} (≈ {fmt_dec(float(x), 2)})"
    return fmt_num(x)


def fmt_set(mask: int, n: int) -> str:
    """Menge der Kunden (Bitmaske) als {1,3,5}."""
    return "{" + ",".join(str(i) for i in range(1, n + 1) if (mask >> i) & 1) + "}"


def fmt_walk(walk) -> str:
    return "-".join(str(i) for i in walk) if walk else "keiner"


def parse_walk(text: str, n: int) -> tuple[int, ...] | None:
    """Weg aus Text wie „5-3-5-1“ (auch Komma oder Leerzeichen als Trenner); None bei ungültiger Eingabe (Zeichen, Kunde außerhalb 1..n, leer, zwei gleiche Kunden direkt hintereinander)."""
    parts = [p for p in text.replace(",", "-").replace(" ", "-").split("-") if p != ""]
    if not parts or not all(p.isdigit() for p in parts):
        return None
    walk = tuple(int(p) for p in parts)
    if len(walk) > C.WALK_MAX_LENGTH or any(not 1 <= j <= n for j in walk) or any(a == b for a, b in zip(walk, walk[1:])):
        return None
    return walk


def gap_percent(reference: float, bound: float) -> float:
    """Lücke in Prozent der Bezugsschranke: (Bezug − Schranke) / Bezug; 0, wenn der Bezug 0 ist oder die Lücke betragsmäßig unter C.ZERO_GAP_PERCENT liegt
    (Rundung der Messdateien und Rauschen des LP-Lösers)."""
    if reference == 0:
        return 0.0
    gap = 100.0 * float(reference - bound) / float(reference)
    return 0.0 if abs(gap) < C.ZERO_GAP_PERCENT else gap


# --- Handbeispiel ---------------------------------------------------------------------------------------------------------------------------

@lru_cache(maxsize=None)
def hand() -> tuple[Instance, tuple]:
    """(Instanz, Dualpreise der ersten Runde) des Handbeispiels."""
    inst = hand_instance()
    return inst, first_round_duals(inst)


def hand_memories() -> list[tuple[str, A.Memory]]:
    """Die Gedächtnisse der Leiter: ng k = 1 bis 7 (k = 7 ist elementar) und k-Zyklen K = 2 und 3, mit Anzeigenamen."""
    return [(f"ng k = {k}" + (" (elementar)" if k == 7 else ""), A.ng(k)) for k in range(1, 8)] + [(f"k-Zyklen K = {K}", A.kcyc(K)) for K in (2, 3)]


class LadderRow(NamedTuple):
    name: str
    memory: A.Memory
    best_walk: tuple[int, ...]
    best_rc: Fraction
    generated: int
    discarded: int
    displaced: int
    alive: int
    bound: Fraction
    rounds: int
    labels: int
    gap: float          # Lücke zur elementaren Schranke in Prozent


@lru_cache(maxsize=None)
def hand_ladder() -> tuple[LadderRow, ...]:
    """Die Leiter der Schranke am Handbeispiel: Runde 1 (ein Pricing-Aufruf) und die ganze Spaltenerzeugung mit exakten Brüchen, je Gedächtnis."""
    inst, pi = hand()
    rows = []
    results = []
    for name, memory in hand_memories():
        res = A.price(inst, pi, memory, exact=True)
        best_rc, best_walk = A.routes_of(inst, res, 1, exact=True)[0]
        cg = A.colgen(inst, memory, A.solve_master_exact, per_round=1, exact=True)
        results.append((name, memory, best_walk, best_rc, res, cg))
    elementary = next(cg.bound for name, memory, _, _, _, cg in results if memory == A.ng(7))
    for name, memory, best_walk, best_rc, res, cg in results:
        rows.append(LadderRow(name, memory, best_walk, best_rc, res.generated, res.discarded, res.displaced, res.alive, cg.bound, cg.iterations, cg.labels,
                              gap_percent(elementary, cg.bound)))
    return tuple(rows)


class WalkCheck(NamedTuple):
    name: str
    walks: int            # Zahl der zulässigen Wege laut Aufzählung
    best_value: Fraction  # bester Wert der Aufzählung
    bound_all: Fraction   # Schranke des Masters über alle zulässigen Wege
    same_best: bool       # bester Wert gleich dem des Labelings in Runde 1
    same_bound: bool      # Schranke gleich der der Spaltenerzeugung


def hand_check_all_walks() -> tuple[WalkCheck, ...]:
    """Gegenprobe ohne Labels: alle zulässigen Wege aufzählen (Gedächtnisregel auf dem ganzen Weg), den besten Wert und den Master über alle Wege mit der
    Leiter vergleichen."""
    inst, pi = hand()
    out = []
    for row in hand_ladder():
        walks = A.enumerate_walks(inst, pi, row.memory, exact=True)
        _, bound_all = A.solve_master_exact(inst, [(j,) for j in range(1, inst.n + 1)] + [w for _, w in walks])
        out.append(WalkCheck(row.name, len(walks), walks[0][0], bound_all, walks[0][0] == row.best_rc, bound_all == row.bound))
    return tuple(out)


WALKS_TO_COMPARE = ((7, 6, 7), (5, 3, 5, 1), (7, 6, 1, 7))
CONTRAST_MEMORIES = (("ng k = 1", A.ng(1)), ("ng k = 2", A.ng(2)), ("ng k = 3", A.ng(3)), ("k-Zyklen K = 2", A.kcyc(2)), ("k-Zyklen K = 3", A.kcyc(3)))


def contrast_walks() -> list[dict]:
    """Welches Gedächtnis erlaubt welchen der drei Beispielwege? Eigenschaft des ganzen Wegs (`walk_allowed`)."""
    inst, _ = hand()
    return [{"walk": walk, **{name: A.walk_allowed(inst, memory, walk) for name, memory in CONTRAST_MEMORIES}} for walk in WALKS_TO_COMPARE]


class WalkAnalysis(NamedTuple):
    steps: list
    allowed: bool
    first_forbidden: int | None   # Stelle (ab 1) des ersten verbotenen Besuchs
    feasible: bool | None         # Last, Zeitfenster, Rückkehr eingehalten? (None, wenn schon verboten)
    value: Fraction | None        # reduzierte Kosten des Wegs, wenn erlaubt und zulässig


def analyse_walk(k: int, walk) -> WalkAnalysis:
    """Gedächtnisspur, Urteil erlaubt/verboten und (falls erlaubt) Zulässigkeit und reduzierte Kosten des Wegs im Handbeispiel."""
    inst, pi = hand()
    steps = A.memory_trace(inst, k, walk)
    forbidden = [i for i, s in enumerate(steps, start=1) if s.forbidden]
    if forbidden:
        return WalkAnalysis(steps, False, forbidden[0], None, None)
    value = A.walk_value(inst, pi, walk, eps=0)
    return WalkAnalysis(steps, True, None, value is not None, value)


# --- Zufallsinstanz, live -------------------------------------------------------------------------------------------------------------------

def ladder_ks(kmax: int) -> tuple[int, ...]:
    """Gedächtnisse des Live-Versuchs: die Stufen aus C.LIVE_LADDER unterhalb von kmax, dazu kmax."""
    return tuple(k for k in C.LIVE_LADDER if k < kmax) + (kmax,)


class LiveRow(NamedTuple):
    k: int
    bound: float | None
    labels: int
    rounds: int
    dominated: int
    aborted: bool
    gap: float | None      # Lücke zu kmax in Prozent (None, wenn Lauf oder Bezug abgebrochen)


def live_ladder(n: int, width: int, seed: int, kmax: int) -> list[LiveRow]:
    """Spaltenerzeugung (ng) für k aus `ladder_ks(kmax)` an der Zufallsinstanz (n, Breite, Zufalls-Seed). Bezug der Lücke ist das größte k."""
    inst = make_instance(n, seed, float(width))
    runs = []
    for k in ladder_ks(kmax):
        r = A.colgen(inst, A.ng(k), A.solve_master_lp, max_labels=C.MAX_LABELS_PER_CALL)
        runs.append((k, r))
    ref = runs[-1][1].bound
    return [LiveRow(k, r.bound, r.labels, r.iterations, r.dominated, r.aborted,
                    None if (r.bound is None or ref is None) else gap_percent(ref, r.bound)) for k, r in runs]


# --- Messreihen laden -----------------------------------------------------------------------------------------------------------------------

@lru_cache(maxsize=None)
def _load(name: str) -> dict:
    return json.loads((DATA_DIR / f"{name}.json").read_text(encoding="utf-8"))


def load_rows(name: str) -> list[dict]:
    """Zeilen einer festen Messreihe: 'knick_n30', 'elementar', 'skalierung' oder 'dssr'."""
    return _load(name)["zeilen"]


def load_check() -> dict:
    """Ergebnis der Nachrechnung mit dem Kern der Demo (tools/nachrechnen.py)."""
    path = DATA_DIR / "nachrechnung.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _finished(row: dict) -> bool:
    return not row["abgebrochen"] and row["schranke"] is not None


# --- Band: n = 30, 24 Instanzen, Bezug ng k = 8 ---------------------------------------------------------------------------------------------

KNICK_CONFIGS = (("ng", 1), ("ng", 2), ("ng", 3), ("ng", 4), ("ng", 5), ("kcyc", 2), ("kcyc", 3), ("kcyc", 4))


def _knick_by_instance(rows):
    by = {}
    for r in rows:
        by.setdefault((r["typ"], r["seed"]), {})[(r["art"], r["k"])] = r
    return by


def knick_table(rows, scope: str = "beide") -> list[dict]:
    """Lücke zur Schranke ng k = 8 (Mittel, Maximum), Labels im Verhältnis zu ng k = 8 (Mittel der je Instanz gebildeten Verhältnisse), Zahl der fertigen und der
    abgebrochenen Läufe, je Gedächtnis. scope: 'zufall', 'cluster' oder 'beide'."""
    by = _knick_by_instance(rows)
    out = []
    for art, k in KNICK_CONFIGS:
        gaps, ratios, aborted = [], [], 0
        for (typ, _seed), conf in by.items():
            if scope != "beide" and typ != scope:
                continue
            ref, row = conf[("ng", 8)], conf[(art, k)]
            if not _finished(row):
                aborted += 1
                continue
            gaps.append(gap_percent(ref["schranke"], row["schranke"]))
            ratios.append(row["labels"] / ref["labels"])
        out.append({"art": art, "k": k, "instanzen": len(gaps), "abgebrochen": aborted,
                    "luecke_mittel": statistics.mean(gaps) if gaps else None, "luecke_max": max(gaps) if gaps else None,
                    "labels_verhaeltnis": statistics.mean(ratios) if ratios else None})
    return out


def knick_pairs(rows) -> list[dict]:
    """Paarvergleich k-Zyklen K gegen ng k = K an derselben Instanz (beide fertig): Schranke der k-Zyklen höher / gleich / tiefer (Toleranz 1e-6), Labels im Mittel."""
    by = _knick_by_instance(rows)
    out = []
    for K in (2, 3, 4):
        hi = eq = lo = 0
        ratios = []
        for conf in by.values():
            a, b = conf[("kcyc", K)], conf[("ng", K)]
            if not (_finished(a) and _finished(b)):
                continue
            if a["schranke"] > b["schranke"] + 1e-6:
                hi += 1
            elif a["schranke"] < b["schranke"] - 1e-6:
                lo += 1
            else:
                eq += 1
            ratios.append(a["labels"] / b["labels"])
        out.append({"K": K, "paare": hi + eq + lo, "hoeher": hi, "gleich": eq, "tiefer": lo, "labels_verhaeltnis": statistics.mean(ratios)})
    return out


def knick_compare_k2_ng5(rows) -> dict:
    """k-Zyklen K = 2 gegen ng k = 5 an derselben Instanz: Schranke der k-Zyklen tiefer / gleich / höher, Labels-Verhältnis im Mittel."""
    lo = eq = hi = 0
    ratios = []
    for conf in _knick_by_instance(rows).values():
        a, b = conf[("kcyc", 2)], conf[("ng", 5)]
        if a["schranke"] < b["schranke"] - 1e-6:
            lo += 1
        elif a["schranke"] > b["schranke"] + 1e-6:
            hi += 1
        else:
            eq += 1
        ratios.append(a["labels"] / b["labels"])
    return {"paare": lo + eq + hi, "tiefer": lo, "gleich": eq, "hoeher": hi, "labels_verhaeltnis": statistics.mean(ratios)}


# --- Band: Bezug elementar (n = 10 bis 30) --------------------------------------------------------------------------------------------------

def elementar_table(rows, n: int) -> list[dict]:
    """Je Fensterbreite und Gedächtnis k: fertige Läufe, Instanzen mit fertigem elementarem Bezug, Lücke zur elementaren Schranke (Mittel, Maximum, Zahl der
    Instanzen mit Lücke 0), Median der Labels (nur fertige Läufe). Der Bezug ist k = n; eine Instanz zählt nur, wenn ihr elementarer Lauf fertig wurde."""
    sub = [r for r in rows if r["n"] == n]
    out = []
    for width in sorted({r["breite"] for r in sub}):
        cell = [r for r in sub if r["breite"] == width]
        ref = {r["seed"]: r for r in cell if r["k"] == n and _finished(r)}
        for k in sorted({r["k"] for r in cell}):
            runs = [r for r in cell if r["k"] == k and _finished(r)]
            gaps = [gap_percent(ref[r["seed"]]["schranke"], r["schranke"]) for r in runs if r["seed"] in ref]
            out.append({"breite": width, "k": k, "elementar": k == n, "laeufe": len(runs), "mit_bezug": len(gaps),
                        "luecke_mittel": statistics.mean(gaps) if gaps else None, "luecke_max": max(gaps) if gaps else None,
                        "luecke_null": sum(1 for g in gaps if g == 0.0),
                        "labels_median": statistics.median(r["labels"] for r in runs) if runs else None})
    return out


# --- Band: n = 50 und 100, Bezug k = 16 -----------------------------------------------------------------------------------------------------

SKALIERUNG_KS = (1, 3, 5, 8, 12, 16)
TYP_NAMES = {"zufall": "zufällig", "cluster": "gruppiert"}


def skalierung_cells(rows) -> list[tuple[str, int, int]]:
    """Zellen (Art, n, Breite) der Messreihe in fester Reihenfolge."""
    return sorted({(r["typ"], r["n"], r["breite"]) for r in rows}, key=lambda c: (c[1], c[2], c[0] != "cluster"))


def skalierung_table(rows) -> list[dict]:
    """Je Zelle (Art, n, Breite) und Gedächtnis k (1, 3, 5, 8, 12, 16): Läufe, Lücke zu k = 16 (Mittel, Maximum, Instanzen mit Lücke 0), Median der Labels,
    Anteil dominierter Labels (über die fertigen Läufe zusammengezählt) und der Median des Verhältnisses der Labels von k = 16 zu k = 5."""
    out = []
    for typ, n, width in skalierung_cells(rows):
        cell = [r for r in rows if (r["typ"], r["n"], r["breite"]) == (typ, n, width)]
        ref = {r["seed"]: r for r in cell if r["k"] == 16 and _finished(r)}
        five = {r["seed"]: r for r in cell if r["k"] == 5 and _finished(r)}
        factor = [ref[s]["labels"] / five[s]["labels"] for s in ref if s in five]
        for k in SKALIERUNG_KS:
            runs = [r for r in cell if r["k"] == k and _finished(r)]
            gaps = [gap_percent(ref[r["seed"]]["schranke"], r["schranke"]) for r in runs if r["seed"] in ref]
            generated = sum(r["labels"] for r in runs)
            out.append({"typ": typ, "n": n, "breite": width, "k": k, "laeufe": len(runs),
                        "luecke_mittel": statistics.mean(gaps) if gaps else None, "luecke_max": max(gaps) if gaps else None,
                        "luecke_null": sum(1 for g in gaps if g == 0.0),
                        "labels_median": statistics.median(r["labels"] for r in runs) if runs else None,
                        "dominiert_anteil": 100.0 * sum(r["dominiert"] for r in runs) / generated if generated else None,
                        "faktor_16_zu_5": statistics.median(factor) if factor else None})
    return out


def skalierung_elementar(rows) -> dict:
    """Elementare Läufe der Messreihe (k = n): Zahl der Läufe, fertige, abgebrochene."""
    el = [r for r in rows if r["k"] == r["n"]]
    done = [r for r in el if _finished(r)]
    return {"laeufe": len(el), "fertig": len(done), "abgebrochen": len(el) - len(done)}


# --- Absatz DSSR (feste Dualpreis-Sätze) ----------------------------------------------------------------------------------------------------

def dssr_summary(rows) -> dict:
    """Kennzahlen der 72 Dualpreis-Sätze: DSSR gegen ng k = 5 und ng k = 8. Verfehlt = andere reduzierte Kosten als DSSR (Toleranz 1e-6). Labels-Verhältnisse als
    Mittel der je Satz gebildeten Verhältnisse."""
    def missed(method, duals=None):
        return sum(1 for r in rows if (duals is None or r["duals"] == duals) and abs(r[method]["rc"] - r["dssr"]["rc"]) > 1e-6)

    def ratio(method, duals=None):
        return statistics.mean(r["dssr"]["labels"] / r[method]["labels"] for r in rows if duals is None or r["duals"] == duals)

    mit_elem = [r for r in rows if not r["elem"]["abgebrochen"]]
    return {"saetze": len(rows), "dssr_abgebrochen": sum(r["dssr"]["abgebrochen"] for r in rows),
            "mit_elem": len(mit_elem), "gleich_elem": sum(1 for r in mit_elem if abs(r["elem"]["rc"] - r["dssr"]["rc"]) <= 1e-6),
            "ng5_verfehlt": missed("ng5"), "ng5_verfehlt_runde2": missed("ng5", "runde2"), "ng5_verfehlt_runde4": missed("ng5", "runde4"), "ng5_verfehlt_ende": missed("ng5", "ende"),
            "saetze_ende": sum(1 for r in rows if r["duals"] == "ende"),
            "ng8_verfehlt": missed("ng8"),
            "faktor_ng5": ratio("ng5"), "faktor_ng8": ratio("ng8"), "faktor_ng5_ende": ratio("ng5", "ende")}


# --- Verdikte -------------------------------------------------------------------------------------------------------------------------------

def verdict_walk(k: int, walk, a: WalkAnalysis, n: int) -> tuple[str, str]:
    """Verdikt zu Experiment 1: Ist der Weg bei ng k erlaubt? Nennt die Stelle des ersten verbotenen Besuchs oder (erlaubt) ob der Weg zulässig ist."""
    text_walk = fmt_walk(walk)
    if not a.allowed:
        step = a.steps[-1]
        return "warning", (f"Der Weg {text_walk} ist bei k = {k} **verboten**: An Stelle {a.first_forbidden} steht Kunde {step.customer}, und er liegt noch im Gedächtnis "
                           f"{fmt_set(step.before, n)}. Das Gedächtnis hat ihn nach dem letzten Besuch nicht vergessen, weil jeder Kunde dazwischen ihn in seiner Nachbarschaft hat.")
    repeated = len(set(walk)) < len(walk)
    if repeated:
        base = f"Der Weg {text_walk} ist bei k = {k} **erlaubt**, obwohl er einen Kunden mehrmals besucht: Zwischen den beiden Besuchen kam ein Kunde, in dessen Nachbarschaft er nicht liegt, das Gedächtnis hat ihn vergessen."
    else:
        base = f"Der Weg {text_walk} ist bei k = {k} **erlaubt** (jeder Kunde höchstens einmal, das ist bei jedem k erlaubt)."
    if a.feasible:
        return ("info" if repeated else "success"), base + f" Er hält Last, Zeitfenster und Rückkehr ein, seine reduzierten Kosten in der ersten Runde sind {fmt_num(a.value)}."
    return "info", base + " Er verletzt aber Last, Zeitfenster oder die Rückkehrzeit und käme als Route nicht in Frage."


def verdict_ladder(rows) -> tuple[str, str]:
    """Verdikt der Kernfrage am Handbeispiel (Leiter der Schranke): ab welchem k die Schranke gleich der elementaren ist, mit Schranken und Lücken von k = 1 und k = 2."""
    ng_rows = [r for r in rows if r.memory.kind == "ng"]
    elementary = next(r for r in ng_rows if r.memory.size == len(ng_rows))
    first_equal = next(r for r in ng_rows if r.bound == elementary.bound)
    k1, k2 = ng_rows[0], ng_rows[1]
    if first_equal.memory.size == 1:
        return "success", f"Schon bei k = 1 ist die Schranke {fmt_bound(k1.bound)} gleich der elementaren Schranke {fmt_bound(elementary.bound)}."
    return "info", (f"Die Schranke steigt mit k: {fmt_bound(k1.bound)} bei k = 1 (Lücke {fmt_pct(k1.gap, 2)} zur elementaren Schranke {fmt_bound(elementary.bound)}), "
                    f"{fmt_bound(k2.bound)} bei k = 2 (Lücke {fmt_pct(k2.gap, 2)}), ab **k = {first_equal.memory.size}** gleich der elementaren (Lücke 0). "
                    "Das gilt für dieses eine Handbeispiel mit 7 Kunden.")


def verdict_live(rows: list[LiveRow], n: int, width: int) -> tuple[str, str]:
    """Verdikt zu Experiment 3 (Zufallsinstanz): Lücke von k = 1, kleinstes k mit Lücke 0, Zahl der Labels beim größten k gegen k = 1."""
    done = [r for r in rows if r.gap is not None]
    if len(done) < 2:
        return "warning", f"Mindestens ein Lauf wurde bei {fmt_int(C.MAX_LABELS_PER_CALL)} erzeugten Labels je Pricing-Aufruf abgebrochen; ohne zwei fertige Läufe gibt es keinen Vergleich."
    top, first = done[-1], done[0]
    zero = next(r for r in done if r.gap == 0.0)
    note = "" if len(done) == len(rows) else " Läufe mit Abbruch sind nicht eingerechnet."
    if first.k == top.k:
        return "info", "Es gibt nur ein Gedächtnis zu vergleichen." + note
    if zero.k == first.k:
        return "success", (f"Bei {n} Kunden und Fensterbreite {width} ist die Schranke schon bei k = {first.k} gleich der bei k = {top.k}; "
                           f"k = {top.k} braucht das {fmt_dec(top.labels / first.labels, 1)}-Fache der Labels von k = {first.k}." + note)
    return "info", (f"Bei {n} Kunden und Fensterbreite {width} liegt die Schranke bei k = {first.k} um {fmt_pct(first.gap, 2)} unter der bei k = {top.k}; "
                    f"**ab k = {zero.k}** ist die Lücke 0. Der Bezug ist k = {top.k}, nicht die elementare Schranke. "
                    f"Die Labels wachsen von {fmt_int(first.labels)} auf {fmt_int(top.labels)} (das {fmt_dec(top.labels / first.labels, 1)}-Fache)." + note)


def verdict_contrast_hand(ladder_rows) -> tuple[str, str]:
    """Verdikt zu Experiment 4 am Handbeispiel: k-Zyklen K = 2 gegen ng k = 2, K = 3 gegen ng k = 3 (Schranke und Labels der Spaltenerzeugung)."""
    by = {r.memory: r for r in ladder_rows}
    k2, g2 = by[A.kcyc(2)], by[A.ng(2)]
    k3, g3 = by[A.kcyc(3)], by[A.ng(3)]
    if k2.bound > g2.bound:
        return "info", (f"Im Handbeispiel ist die Schranke der k-Zyklen K = 2 mit {fmt_bound(k2.bound)} höher (schärfer) als die von ng k = 2 mit {fmt_bound(g2.bound)}; "
                        f"sie braucht dafür {k2.labels} statt {g2.labels} Labels (K = 3 gegen ng k = 3: {fmt_bound(k3.bound)} gegen {fmt_bound(g3.bound)}, {k3.labels} gegen {g3.labels} Labels). "
                        "Das ist eine Instanz, kein Befund über k-Zyklen allgemein.")
    return "info", (f"Im Handbeispiel haben k-Zyklen K = 2 und ng k = 2 dieselbe Schranke {fmt_bound(k2.bound)}; die Labels: {k2.labels} gegen {g2.labels}. "
                    "Das ist eine Instanz, kein Befund über k-Zyklen allgemein.")


def verdict_knick(rows) -> tuple[str, str]:
    """Verdikt zu Experiment 5 (n = 30, 24 Instanzen, Bezug ng k = 8): Lücke von k = 1 und der größte k mit Mittel über 0,5 %; ab welchem k das Mittel darunter bleibt."""
    table = {(r["art"], r["k"]): r for r in knick_table(rows) if r["art"] == "ng"}
    first = table[("ng", 1)]
    above = [k for k in range(1, 6) if table[("ng", k)]["luecke_mittel"] >= 0.5]
    last_above = max(above)
    nxt = table[("ng", last_above + 1)] if last_above < 5 else None
    text = (f"Bei 30 Kunden und Fensterbreite 100 liegt die Schranke bei k = 1 im Mittel {fmt_pct(first['luecke_mittel'], 2)} unter der von k = 8 "
            f"(größter Einzelwert {fmt_pct(first['luecke_max'], 2)}, {first['instanzen']} Instanzen)")
    if nxt is not None:
        text += f"; ab k = {last_above + 1} liegt das Mittel unter 0,5 % ({fmt_pct(nxt['luecke_mittel'], 2)}, größter Einzelwert {fmt_pct(nxt['luecke_max'], 2)}); "
    else:
        text += "; "
    five = table[("ng", 5)]
    text += f"bei k = 5 sind es {fmt_pct(five['luecke_mittel'], 2)} im Mittel und höchstens {fmt_pct(five['luecke_max'], 2)} im Einzelfall."
    return "info", text


def verdict_skalierung(table) -> tuple[str, str]:
    """Verdikt zu Experiment 5 (n = 50 und 100, Bezug k = 16): größtes Mittel und größte Einzellücke für k = 5 und k = 8 über die Zellen mit Lücke bei k = 1 über 0."""
    def worst(k):
        rows = [r for r in table if r["k"] == k]
        return max(r["luecke_mittel"] for r in rows), max(r["luecke_max"] for r in rows)

    m5, x5 = worst(5)
    m8, x8 = worst(8)
    zero_cells = sorted({(r["n"], r["breite"], r["typ"]) for r in table if r["k"] == 1 and r["luecke_max"] == 0})
    return "info", (f"Über die {len({(r['typ'], r['n'], r['breite']) for r in table})} Zellen (je 12 Instanzen) liegt k = 5 im Mittel höchstens {fmt_pct(m5, 2)} unter k = 16, "
                    f"im Einzelfall bis {fmt_pct(x5, 2)}; k = 8 im Mittel höchstens {fmt_pct(m8, 2)}, im Einzelfall bis {fmt_pct(x8, 2)}. "
                    f"Bei {len(zero_cells)} Zellen (n = 100, Breite 20) ist die Lücke schon bei k = 1 gleich 0.")


def verdict_elementar(table, n: int) -> tuple[str, str]:
    """Verdikt zu Experiment 5 (k = 5 gegen elementar): Zahl der Instanzen mit Lücke bei k = 5 je Breite."""
    parts = []
    for width in sorted({r["breite"] for r in table}):
        row = next(r for r in table if r["breite"] == width and r["k"] == 5)
        parts.append(f"Breite {width}: {row['mit_bezug'] - row['luecke_null']} von {row['mit_bezug']} Instanzen mit Lücke (Mittel {fmt_pct(row['luecke_mittel'], 2)}, größter Einzelwert {fmt_pct(row['luecke_max'], 2)})")
    return "info", f"Bei {n} Kunden, k = 5 gegen elementar: " + "; ".join(parts) + "."


def verdict_round1(rows) -> tuple[str, str]:
    """Verdikt zu Experiment 2 (Runde 1): bester Weg bei k = 1, k = 2 und ab welchem k der elementare beste Weg gefunden wird; ob die Wege der kleinen k einen Kunden wiederholen."""
    ng_rows = [r for r in rows if r.memory.kind == "ng"]
    elementary = ng_rows[-1]
    first_el = next(r for r in ng_rows if r.best_walk == elementary.best_walk)
    k1, k2 = ng_rows[0], ng_rows[1]

    def repeats(r) -> str:
        return "wiederholt einen Kunden" if len(set(r.best_walk)) < len(r.best_walk) else "wiederholt keinen Kunden"

    return "info", (f"In Runde 1 findet ng k = 1 den Weg {fmt_walk(k1.best_walk)} mit reduzierten Kosten {fmt_num(k1.best_rc)} ({repeats(k1)}), ng k = 2 den Weg {fmt_walk(k2.best_walk)} "
                    f"({fmt_num(k2.best_rc)}; {repeats(k2)}), ab k = {first_el.memory.size} den elementaren besten Weg {fmt_walk(elementary.best_walk)} ({fmt_num(elementary.best_rc)}; {repeats(elementary)}). "
                    + ("Bei einem Weg mit Kreis zählt der Dualpreis eines Kunden bei jedem Besuch erneut (reduzierte Kosten = Länge minus die Dualpreise aller Besuche); ein größeres Gedächtnis verbietet das."
                       if len(set(k1.best_walk)) < len(k1.best_walk) else ""))


def verdict_walkcheck(checks) -> tuple[str, str]:
    """Verdikt zur Gegenprobe: in wie vielen Gedächtnissen stimmen bester Wert und Schranke der Aufzählung mit den Labels überein."""
    same = sum(1 for c in checks if c.same_best and c.same_bound)
    if same == len(checks):
        return "success", f"In {same} von {len(checks)} Gedächtnissen stimmen bester Wert der Aufzählung und Schranke des Masters über alle Wege mit dem Labeling überein."
    return "error", f"Nur in {same} von {len(checks)} Gedächtnissen stimmen die Aufzählung und das Labeling überein: Das ist ein Fehler im Kern."


def verdict_contrast_series(table, pairs, k2_ng5, table_cluster) -> tuple[str, str]:
    """Verdikt zu Experiment 4 (24 Instanzen): bei gleichem k schärfer, aber mehr Labels; Zahlen je Gedächtnis gegen ng k = 8."""
    by = {(r["art"], r["k"]): r for r in table}
    p = {q["K"]: q for q in pairs}
    ratio = lambda a, b: fmt_dec(by[(a, b)]["labels_verhaeltnis"], 2)  # noqa: E731
    gap = lambda a, b: fmt_pct(by[(a, b)]["luecke_mittel"], 2)  # noqa: E731
    k4 = by[("kcyc", 4)]
    k4_cluster = next(r for r in table_cluster if (r["art"], r["k"]) == ("kcyc", 4))
    return "info", (
        f"Bei gleichem k ist die Schranke der k-Zyklen nicht immer höher als die von ng: bei K = 2 in {p[2]['hoeher']} von {p[2]['paare']} Paaren und bei K = 3 in {p[3]['hoeher']} von {p[3]['paare']}, "
        f"bei K = 4 nur in {p[4]['hoeher']} von {p[4]['paare']} Paaren (gleich in {p[4]['gleich']}). Die k-Zyklen brauchen dafür das {fmt_dec(p[2]['labels_verhaeltnis'], 2)}-, {fmt_dec(p[3]['labels_verhaeltnis'], 2)}- und "
        f"{fmt_dec(p[4]['labels_verhaeltnis'], 2)}-Fache der Labels. **Pro Label gerechnet** (mit meiner Dominanz der k-Zyklen; je Gedächtnis erst die Labels im Verhältnis zu ng k = 8, dann die Lücke zu ng k = 8): "
        f"ng k = 3 {ratio('ng', 3)} und {gap('ng', 3)}, K = 2 {ratio('kcyc', 2)} und {gap('kcyc', 2)}; ng k = 5 {ratio('ng', 5)} und {gap('ng', 5)}, K = 3 {ratio('kcyc', 3)} und {gap('kcyc', 3)} "
        f"(Mittel über die fertigen Instanzen: ng k = 3: {by[('ng', 3)]['instanzen']}, K = 2: {by[('kcyc', 2)]['instanzen']}, ng k = 5: {by[('ng', 5)]['instanzen']}, K = 3: {by[('kcyc', 3)]['instanzen']}). "
        f"K = 2 gegen ng k = 5: Schranke tiefer in {k2_ng5['tiefer']}, gleich in {k2_ng5['gleich']}, höher in {k2_ng5['hoeher']} von {k2_ng5['paare']} Paaren, das {fmt_dec(k2_ng5['labels_verhaeltnis'], 2)}-Fache der Labels. "
        f"K = 4 ist bei {k4['abgebrochen']} von {k4['abgebrochen'] + k4['instanzen']} Instanzen an der Zeitgrenze der Messung abgebrochen (bei gruppierten Instanzen {k4_cluster['abgebrochen']} von {k4_cluster['abgebrochen'] + k4_cluster['instanzen']})."
    )


def verdict_small_n(by_n) -> tuple[str, str]:
    """Verdikt zu Experiment 5 (n = 10 bis 25, k = 5 gegen elementar): je Fensterbreite die Zahl der Instanzen mit Lücke, je n."""
    parts = []
    for width in sorted({r["breite"] for r in by_n[10]}):
        cells = []
        for n in (10, 15, 20, 25):
            row = next(r for r in by_n[n] if r["breite"] == width and r["k"] == 5)
            cells.append((n, row["mit_bezug"] - row["luecke_null"], row["mit_bezug"], row["luecke_mittel"], row["luecke_max"]))
        none = [str(n) for n, g, _, _, _ in cells if g == 0]
        some = [f"n = {n}: {g} von {m} Instanzen (Mittel {fmt_pct(mean, 2)}, größter Einzelwert {fmt_pct(mx, 2)})" for n, g, m, mean, mx in cells if g > 0]
        text = f"Breite {width}: "
        if none:
            text += f"keine Lücke bei n = {', '.join(none)}"
        if some:
            text += ("; " if none else "") + "Lücke bei " + "; ".join(some)
        parts.append(text)
    return "info", "k = 5 gegen elementar (6 Instanzen je Zelle). " + ". ".join(parts) + ". „k = 5 ist immer gleich elementar“ gilt in dieser Messreihe also nur bis n = 15 und bei Breite 40."


def verdict_check(check: dict) -> tuple[str, str]:
    """Verdikt zur Nachrechnung: Zahl der neu gerechneten Läufe und der Läufe mit gleicher Schranke und gleicher Labelzahl (Läufe, die in der Messung abbrachen, sind nicht dabei)."""
    series = [check[s] for s in ("knick", "elementar", "skalierung")]
    rows = sum(s["zeilen"] - s["in_vormessung_abgebrochen"] for s in series)
    done = sum(s["neu_gerechnet"] for s in series)
    bound = sum(s["schranke_gleich"] for s in series)
    labels = sum(s["labels_gleich"] for s in series)
    text = (f"Von {fmt_int(rows)} in der Messung fertigen Läufen hat die Demo {fmt_int(done)} mit ihrem Kern neu gerechnet: Die Schranke ist in {fmt_int(bound)}, die Zahl der erzeugten Labels in {fmt_int(labels)} dieser Läufe gleich. "
            f"{fmt_int(rows - done)} Läufe sind nicht neu gerechnet, ihre Zeilen stammen nur aus der Messdatei der Planung.")
    return ("success" if bound == done and labels == done else "warning"), text
