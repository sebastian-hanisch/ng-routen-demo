"""Erzeugt die Zahlentabellen der README (Markdown) aus dem Kern und den festen Messreihen.

Aufruf: python tools/readme_tabellen.py        (gibt alle Tabellen aus, zum Einfügen in die README)
`tests/test_claims.py` ruft dieselben Funktionen auf und prüft, dass jede Tabelle wörtlich in der README steht: Die README kann nicht von den Daten abweichen, ohne dass ein Test rot wird."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import ngr_algorithm as A  # noqa: E402
import ngr_evaluation as ev  # noqa: E402


def _d(x, digits=2):
    return ev.fmt_dec(x, digits)


def table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    out += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(out)


def round1_table() -> str:
    """Runde 1 am Handbeispiel (ein Aufruf des Preisproblems) und Zahl der zulässigen Wege (Aufzählung)."""
    inst, pi = ev.hand()
    rows = []
    for r in ev.hand_ladder():
        walks = len(A.enumerate_walks(inst, pi, r.memory, exact=True))
        rows.append([r.name, ev.fmt_walk(r.best_walk), ev.fmt_num(r.best_rc), r.generated, f"{r.discarded} / {r.displaced} / {r.alive}", walks])
    return table(["Gedächtnis", "Bester Weg", "Reduzierte Kosten", "Erzeugte Labels", "Verworfen / verdrängt / übrig", "Zulässige Wege"], rows)


def hand_table() -> str:
    """Die Daten des Handbeispiels (wie die Tabelle der App): Gitterpunkt, Entfernung zum Depot, Last, Zeitfenster, Dualpreis der ersten Runde."""
    inst, duals = ev.hand()
    rows = [[i, f"({inst.points[i][0]}, {inst.points[i][1]})", inst.d[0][i], inst.demand[i], f"[{inst.ready[i]}, {inst.due[i]}]", duals[i]] for i in range(1, inst.n + 1)]
    return table(["Kunde", "Punkt", "Entfernung zum Depot", "Last", "Zeitfenster [früh, spät]", "Dualpreis (Runde 1)"], rows)


def ladder_table() -> str:
    rows = [[r.name, ev.fmt_bound(r.bound), r.rounds, r.labels, ev.fmt_pct(r.gap, 2)] for r in ev.hand_ladder()]
    return table(["Gedächtnis", "Schranke", "Runden", "Labels (eine neue Spalte je Runde)", "Lücke zur elementaren Schranke"], rows)


def walks_table() -> str:
    names = [name for name, _ in ev.CONTRAST_MEMORIES]
    rows = [[ev.fmt_walk(r["walk"])] + ["erlaubt" if r[n] else "verboten" for n in names] for r in ev.contrast_walks()]
    return table(["Weg"] + names, rows)


def knick_table(rows) -> str:
    out = []
    for r in ev.knick_table(rows):
        name = f"ng k = {r['k']}" if r["art"] == "ng" else f"k-Zyklen K = {r['k']}"
        out.append([name, f"{r['instanzen']} / {r['abgebrochen']}", f"{_d(r['luecke_mittel'], 3)} ({_d(r['luecke_max'], 3)})", _d(r["labels_verhaeltnis"], 2)])
    return table(["Gedächtnis", "Instanzen fertig / abgebrochen", "Lücke Mittel (Maximum) in %", "Labels / ng k = 8"], out)


def pairs_table(rows) -> str:
    out = [[f"K = {p['K']} gegen ng k = {p['K']}", p["paare"], p["hoeher"], p["gleich"], p["tiefer"], _d(p["labels_verhaeltnis"], 2)] for p in ev.knick_pairs(rows)]
    return table(["Paar", "Instanzen", "Schranke der k-Zyklen höher", "gleich", "tiefer", "Labels k-Zyklen / ng (Mittel)"], out)


def elementar30_table(rows) -> str:
    out = []
    for r in ev.elementar_table(rows, 30):
        mean = "–" if r["luecke_mittel"] is None else f"{_d(r['luecke_mittel'], 2)} ({_d(r['luecke_max'], 2)})"
        out.append([r["breite"], "elementar" if r["elementar"] else f"ng k = {r['k']}", r["laeufe"], r["mit_bezug"], mean, r["luecke_null"], ev.fmt_int(round(r["labels_median"]))])
    return table(["Breite", "Gedächtnis", "Läufe fertig", "Instanzen mit Bezug", "Lücke Mittel (Maximum) in %", "Instanzen mit Lücke 0", "Labels (Median)"], out)


def small_n_table(rows) -> str:
    out = []
    for n in (10, 15, 20, 25):
        for r in ev.elementar_table(rows, n):
            if r["k"] in (1, 5):
                out.append([n, r["breite"], f"ng k = {r['k']}", f"{r['mit_bezug'] - r['luecke_null']} von {r['mit_bezug']}", f"{_d(r['luecke_mittel'], 2)} ({_d(r['luecke_max'], 2)})"])
    return table(["Kunden n", "Breite", "Gedächtnis", "Instanzen mit Lücke", "Lücke Mittel (Maximum) in %"], out)


def skalierung_table(rows) -> str:
    t = ev.skalierung_table(rows)
    out = []
    for typ, n, width in ev.skalierung_cells(rows):
        cells = [x for x in t if (x["typ"], x["n"], x["breite"]) == (typ, n, width)]
        by_k = {x["k"]: x for x in cells}
        row = [f"n = {n}, Breite {width}, {ev.TYP_NAMES[typ]}"]
        row += [f"{_d(by_k[k]['luecke_mittel'], 2)} ({_d(by_k[k]['luecke_max'], 2)})" for k in ev.SKALIERUNG_KS[:-1]]
        row += [_d(by_k[16]["faktor_16_zu_5"], 2), f"{_d(by_k[5]['dominiert_anteil'], 1)} / {_d(by_k[16]['dominiert_anteil'], 1)}"]
        out.append(row)
    return table(["Zelle", "k = 1", "k = 3", "k = 5", "k = 8", "k = 12", "Labels k = 16 / k = 5 (Median)", "Dominiert k = 5 / k = 16 in %"], out)


def dssr_table(rows) -> str:
    s = ev.dssr_summary(rows)
    out = [
        ["DSSR liefert denselben Wert wie die elementare Rechnung", f"{s['gleich_elem']} von {s['mit_elem']} Sätzen (in {s['saetze'] - s['mit_elem']} Sätzen war die elementare Rechnung abgebrochen)"],
        ["Labels DSSR / ng k = 5 (Mittel der Verhältnisse)", _d(s["faktor_ng5"], 1)],
        ["Labels DSSR / ng k = 8 (Mittel der Verhältnisse)", _d(s["faktor_ng8"], 1)],
        ["ng k = 5 verfehlt den besten Weg", f"{s['ng5_verfehlt']} von {s['saetze']} (Runde 2: {s['ng5_verfehlt_runde2']}, Runde 4: {s['ng5_verfehlt_runde4']}, Ende: {s['ng5_verfehlt_ende']} von {s['saetze_ende']})"],
        ["Labels DSSR / ng k = 5 am Ende der Spaltenerzeugung", _d(s["faktor_ng5_ende"], 1)],
    ]
    return table(["Größe", "Wert"], out)


def check_table() -> str:
    """Ergebnis der Nachrechnung mit dem Kern der Demo (data/nachrechnung.json)."""
    chk = ev.load_check()
    rows = []
    for key, name in (("knick", "24 Instanzen, n = 30"), ("elementar", "n = 10 bis 30, Bezug elementar"), ("skalierung", "n = 50 und 100, Bezug k = 16")):
        c = chk[key]
        dom = f"{c['dominiert_gleich']} von {c['dominiert_verglichen']}" if c["dominiert_verglichen"] else "–"
        rows.append([name, c["zeilen"], c["in_vormessung_abgebrochen"], c["neu_gerechnet"], c["schranke_gleich"], c["labels_gleich"], c["runden_gleich"], dom])
    return table(["Messreihe", "Zeilen", "In der Messung abgebrochen", "Neu gerechnet", "Schranke gleich", "Labels gleich", "Runden gleich", "Dominierte gleich"], rows)


def all_tables() -> dict[str, str]:
    knick, elem, skal, dssr = ev.load_rows("knick_n30"), ev.load_rows("elementar"), ev.load_rows("skalierung"), ev.load_rows("dssr")
    return {"hand": hand_table(), "round1": round1_table(), "ladder": ladder_table(), "walks": walks_table(), "knick": knick_table(knick), "pairs": pairs_table(knick), "elementar30": elementar30_table(elem),
            "small_n": small_n_table(elem), "skalierung": skalierung_table(skal), "dssr": dssr_table(dssr), "check_table": check_table()}


if __name__ == "__main__":
    for name, text in all_tables().items():
        print(f"<!-- {name} -->")
        print(text)
        print()
