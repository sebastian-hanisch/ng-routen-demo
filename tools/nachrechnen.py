"""Rechnet die festen Messreihen (data/*.json) mit dem Kern dieser Demo nach.

Aufruf:
  python tools/nachrechnen.py run <serie> [--n 50] [--seeds 0-11] [--art ng|kcyc] [--jobs 3] [--auch-grosse]
  python tools/nachrechnen.py merge

Serien: knick (24 Instanzen, 30 Kunden), elementar (n = 10 bis 30), skalierung (n = 50 und 100).
`run` rechnet jede Zeile der Serie, die in der Vormessung fertig wurde (nicht abgebrochen), mit `ngr_algorithm.colgen` (Überdeckungs-Master, HiGHS, bis zu 15
Spalten je Runde, wie die Vormessung) nach und hängt das Ergebnis an `tools/nachrechnung/<serie>.jsonl` an; schon vorhandene Zeilen (gleiche Quelle) werden übersprungen,
ein abgebrochener Aufruf kann also fortgesetzt werden. Die Arbeitsprozesse laufen mit niedriger Priorität.
`merge` vergleicht alle Ergebnisse mit den Zeilen der Messreihen und schreibt data/nachrechnung.json: je Serie, wie viele Zeilen es gibt, wie viele neu gerechnet
wurden, in wie vielen Schranke, Zahl der erzeugten Labels, Zahl der Runden und Zahl der dominierten Labels übereinstimmen, und jede Abweichung einzeln.
Läufe, die in der Vormessung an einer Zeitgrenze abgebrochen wurden, werden nicht neu gerechnet (der Abbruch hing von der Last des Rechners ab)."""

import argparse
import json
import multiprocessing
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
DATA = ROOT / "data"
OUT = Path(__file__).resolve().parent / "nachrechnung"
SERIES = ("knick", "elementar", "skalierung")
FILES = {"knick": "knick_n30.json", "elementar": "elementar.json", "skalierung": "skalierung.json"}
BOUND_TOLERANCE = {"knick": 1e-6, "skalierung": 1e-6, "elementar": 6e-5}   # Stellen der Rohdateien: 6, 6, 4


def load_rows(serie: str) -> list[dict]:
    return json.loads((DATA / FILES[serie]).read_text(encoding="utf-8"))["zeilen"]


def run_one(args):
    """Eine Zeile nachrechnen (in einem Arbeitsprozess). Rückgabe: Ergebnis als dict."""
    serie, row = args
    import ngr_algorithm as A
    from ngr_scenario import make_instance

    clustered = row.get("typ") == "cluster"
    n = row.get("n", 30)
    width = row.get("breite", 100)
    inst = make_instance(n, row["seed"], float(width), clustered=clustered)
    memory = A.Memory(row.get("art", "ng"), row["k"])
    t0 = time.time()
    res = A.colgen(inst, memory, A.solve_master_lp)
    return {"quelle": row["quelle"], "schranke": res.bound, "runden": res.iterations, "labels": res.labels, "dominiert": res.dominated, "abgebrochen": res.aborted,
            "sekunden": round(time.time() - t0, 1)}


def _low_priority() -> None:
    try:
        import ctypes

        ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)   # BELOW_NORMAL_PRIORITY_CLASS
    except Exception:
        pass


def cmd_run(opts) -> None:
    serie = opts.serie
    rows = load_rows(serie)
    todo = []
    out_path = OUT / f"{serie}.jsonl"
    OUT.mkdir(exist_ok=True)
    done = set()
    if out_path.exists():
        done = {json.loads(line)["quelle"] for line in out_path.read_text(encoding="utf-8").splitlines() if line.strip()}
    lo, hi = (int(x) for x in opts.seeds.split("-")) if opts.seeds else (0, 10**9)
    for row in rows:
        if row["abgebrochen"] or row["schranke"] is None:
            continue
        if opts.n is not None and row.get("n", 30) != opts.n:
            continue
        if opts.art is not None and row.get("art", "ng") != opts.art:
            continue
        if not lo <= row["seed"] <= hi:
            continue
        if row["quelle"] in done:
            continue
        todo.append(row)
    todo.sort(key=lambda r: -(r.get("labels") or 0))   # die größten zuerst: gleichmäßige Auslastung
    print(f"{serie}: {len(todo)} Läufe zu rechnen, {len(done)} schon vorhanden", flush=True)
    t0 = time.time()
    with multiprocessing.Pool(opts.jobs, initializer=_low_priority) as pool, out_path.open("a", encoding="utf-8", newline="\n") as f:
        for number, result in enumerate(pool.imap_unordered(run_one, [(serie, r) for r in todo]), start=1):
            f.write(json.dumps(result) + "\n")
            f.flush()
            print(f"  {number}/{len(todo)} {result['quelle']} {result['sekunden']} s (gesamt {time.time() - t0:.0f} s)", flush=True)


def cmd_merge(_opts) -> None:
    report = {}
    for serie in SERIES:
        rows = load_rows(serie)
        by_source = {r["quelle"]: r for r in rows}
        path = OUT / f"{serie}.jsonl"
        results = {}
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    r = json.loads(line)
                    results[r["quelle"]] = r
        tol = BOUND_TOLERANCE[serie]
        same_bound = same_labels = same_rounds = same_dom = compared_dom = 0
        differences = []
        for source, res in results.items():
            ref = by_source[source]
            ok_bound = res["schranke"] is not None and ref["schranke"] is not None and abs(res["schranke"] - ref["schranke"]) <= tol
            ok_labels = ref.get("labels") == res["labels"]
            ok_rounds = ref.get("runden") == res["runden"]
            ok_dom = ref.get("dominiert") is None or ref["dominiert"] == res["dominiert"]
            same_bound += ok_bound
            same_labels += ok_labels
            same_rounds += ok_rounds
            compared_dom += ref.get("dominiert") is not None
            same_dom += ok_dom and ref.get("dominiert") is not None
            if not (ok_bound and ok_labels and ok_rounds and ok_dom):
                differences.append({"quelle": source, "messreihe": {k: ref.get(k) for k in ("schranke", "labels", "runden", "dominiert")},
                                    "nachgerechnet": {k: res[k] for k in ("schranke", "labels", "runden", "dominiert")}})
        report[serie] = {
            "zeilen": len(rows),
            "in_vormessung_abgebrochen": sum(1 for r in rows if r["abgebrochen"] or r["schranke"] is None),
            "neu_gerechnet": len(results),
            "schranke_gleich": same_bound,
            "labels_gleich": same_labels,
            "runden_gleich": same_rounds,
            "dominiert_verglichen": compared_dom,
            "dominiert_gleich": same_dom,
            "abweichungen": differences,
        }
        print(serie, {k: v for k, v in report[serie].items() if k != "abweichungen"}, f"Abweichungen: {len(differences)}")
    (DATA / "nachrechnung.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run")
    run.add_argument("serie", choices=SERIES)
    run.add_argument("--n", type=int, default=None)
    run.add_argument("--seeds", default=None, help="von-bis, einschließlich (Zufalls-Seeds)")
    run.add_argument("--art", choices=("ng", "kcyc"), default=None)
    run.add_argument("--jobs", type=int, default=3)
    sub.add_parser("merge")
    opts = parser.parse_args()
    {"run": cmd_run, "merge": cmd_merge}[opts.cmd](opts)


if __name__ == "__main__":
    main()
