"""Baut die festen Messreihen (data/*.json) aus den Rohausgaben der Vormessung der Planung.

Aufruf: python tools/baender_bauen.py [Ordner der Vormessung]   (Standard: ../../label-setting-planung/vormessung relativ zu diesem Skript)

Jede Zeile einer Messreihe ist ein Lauf der Spaltenerzeugung (eine Instanz, ein Gedächtnis) und nennt ihre Quelle als `Datei:Zeile`. Gebaut werden:
- data/knick_n30.json     24 Instanzen mit 30 Kunden, Breite 100 (12 zufällig, 12 gruppiert): ng k = 1 bis 5 (run_p09.log), ng k = 8 und k-Zyklen K = 2 bis 4
                          (out_v12a_*.txt, Nachläufe out_v12a_nl_*.txt überschreiben abgebrochene Läufe)
- data/elementar.json     6 Instanzen je Zelle, n = 10, 15, 20, 25 (run_p07_n*.log) und n = 30 (out_v1_n30.txt), Breite 40 und 100: ng k = 1, 5 (n = 30 auch 3, 8, 12)
                          und elementar (k = n)
- data/skalierung.json    n = 50 und 100, 12 Instanzen je Zelle (out_v8_*.txt, out_v8_*_elem.txt): ng k = 1, 3, 5, 8, 12, 16 und elementar
- data/dssr.json          72 feste Dualpreis-Sätze, n = 30, Breite 100 (out_v12b_*.txt): DSSR, ng k = 5, ng k = 8, elementar je Satz

Die Rohdateien sind Textausgaben der Messskripte der Planung (Python 3.14, SciPy 1.18.1); die Demo rechnet die Reihen mit ihrem eigenen Kern nach
(`tools/nachrechnen.py`, Ergebnis in data/nachrechnung.json)."""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
DEFAULT_VM = HERE.parent.parent / "label-setting-planung" / "vormessung"


def _lines(path: Path):
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        yield number, line.split()


def _bound(text):
    return None if text == "NA" else float(text)


def build_knick(vm: Path) -> dict:
    rows = {}   # (typ, seed, konfig) -> Zeile
    for number, p in _lines(vm / "run_p09.log"):
        if len(p) == 7 and p[0] in ("zufall", "cluster") and p[1].isdigit() and p[2].isdigit():
            typ, seed, k = p[0], int(p[1]), int(p[2])
            rows[(typ, seed, f"ng{k}")] = {"typ": typ, "seed": seed, "art": "ng", "k": k, "schranke": _bound(p[3]), "runden": int(p[4]), "labels": int(p[5]),
                                           "abgebrochen": int(p[6]), "quelle": f"run_p09.log:{number}"}
    v12a = {}
    paths = sorted(vm.glob("out_v12a_zufall_?.txt")) + sorted(vm.glob("out_v12a_cluster_?.txt")) + sorted(vm.glob("out_v12a_nl_*.txt"))
    for path in paths:   # spätere Dateien (Nachläufe mit größerer Zeitgrenze) überschreiben abgebrochene Läufe
        for number, p in _lines(path):
            if len(p) < 11 or p[0] not in ("zufall", "cluster") or not p[3].isdigit():
                continue
            typ, seed, konfig = p[0], int(p[3]), p[4]
            v12a[(typ, seed, konfig)] = {"typ": typ, "seed": seed, "konfig": konfig, "schranke": _bound(p[5]), "runden": int(p[6]), "labels": int(p[8]),
                                         "abgebrochen": int(p[10]), "quelle": f"{path.name}:{number}"}
    for (typ, seed, konfig), r in sorted(v12a.items()):
        if konfig in ("ng8",) or konfig.startswith("kcyc"):
            art, k = ("ng", 8) if konfig == "ng8" else ("kcyc", int(konfig[4:]))
            rows[(typ, seed, konfig)] = {"typ": typ, "seed": seed, "art": art, "k": k, **{x: r[x] for x in ("schranke", "runden", "labels", "abgebrochen", "quelle")}}
    # Kontrolle: ng k = 1 und k = 5 aus run_p09.log wiederholen V12a in 48 von 48 Läufen
    same = sum(1 for (typ, seed, konfig), r in rows.items() if konfig in ("ng1", "ng5") and (typ, seed, konfig) in v12a
               and abs(v12a[(typ, seed, konfig)]["schranke"] - r["schranke"]) < 1e-6 and v12a[(typ, seed, konfig)]["labels"] == r["labels"])
    assert same == 48, same
    out = [rows[key] for key in sorted(rows, key=lambda x: (x[0] != "zufall", x[1], x[2]))]
    return {"beschreibung": "24 Instanzen mit 30 Kunden, Breite 100: je 12 zufällig (zufall) und gruppiert (cluster), Zufalls-Seeds 0 bis 11, Überdeckungs-Master",
            "kontrolle_ng1_ng5_gegen_v12a": same, "zeilen": out}


def _runs(path: Path, columns: dict, typ_default=None):
    out = []
    for number, p in _lines(path):
        if len(p) < len(columns) or not p[0].lstrip("-").isalnum() or p[0] == "typ" or p[0] == "n":
            continue
        out.append((number, dict(zip(columns, p))))
    return out


def build_elementar(vm: Path) -> dict:
    cols = ("n", "breite", "seed", "k", "schranke", "runden", "spalten", "t_pricing", "labels", "dom_anteil", "abgebrochen")
    rows = []
    files = [vm / f"run_p07_n{n}.log" for n in (10, 15, 20, 25)] + [vm / "out_v1_n30.txt"]
    for path in files:
        for number, r in _runs(path, cols):
            if int(r["breite"]) not in (40, 100):
                continue
            rows.append({"n": int(r["n"]), "breite": int(r["breite"]), "seed": int(r["seed"]), "k": int(r["k"]), "schranke": _bound(r["schranke"]), "runden": int(r["runden"]),
                         "labels": int(r["labels"]) if r["schranke"] != "NA" else None, "abgebrochen": int(r["abgebrochen"]), "quelle": f"{path.name}:{number}"})
    return {"beschreibung": "Zufällig verteilte Instanzen, 6 je Zelle (Zufalls-Seeds 0 bis 5), Breite 40 und 100, Überdeckungs-Master; k = n ist elementar", "zeilen": rows}


def build_skalierung(vm: Path) -> dict:
    cols = ("typ", "n", "breite", "seed", "k", "schranke", "runden", "spalten", "t_pricing", "labels", "dominiert", "abgebrochen")
    rows = []
    for path in sorted(vm.glob("out_v8_*_n*_w*.txt")):   # schließt die *_elem.txt-Dateien (elementare Läufe) ein
        for number, r in _runs(path, cols):
            if r["typ"] not in ("zufall", "cluster"):
                continue
            done = r["schranke"] != "NA"
            rows.append({"typ": r["typ"], "n": int(r["n"]), "breite": int(r["breite"]), "seed": int(r["seed"]), "k": int(r["k"]), "schranke": _bound(r["schranke"]),
                         "runden": int(r["runden"]), "labels": int(r["labels"]) if done else None, "dominiert": int(r["dominiert"]) if done else None,
                         "abgebrochen": int(r["abgebrochen"]), "quelle": f"{path.name}:{number}"})
    return {"beschreibung": "12 Instanzen je Zelle (Zufalls-Seeds 0 bis 11), zufällig (zufall) und gruppiert (cluster), Überdeckungs-Master; k = n ist elementar", "zeilen": rows}


def build_dssr(vm: Path) -> dict:
    groups = {}
    for path in sorted(vm.glob("out_v12b_zufall_?.txt")) + sorted(vm.glob("out_v12b_cluster_?.txt")):
        for number, p in _lines(path):
            if len(p) < 14 or p[0] not in ("zufall", "cluster") or not p[3].isdigit():
                continue
            typ, seed, duals, methode = p[0], int(p[3]), p[4], p[5]
            g = groups.setdefault((typ, seed, duals), {"typ": typ, "seed": seed, "duals": duals, "quelle": f"{path.name}:{number}"})
            g[methode] = {"rc": None if p[6] == "NA" else float(p[6]), "labels": int(p[7]), "abgebrochen": int(p[11])}
    rows = [groups[key] for key in sorted(groups, key=lambda x: (x[0] != "zufall", x[1], x[2]))]
    assert len(rows) == 72, len(rows)
    return {"beschreibung": "72 feste Dualpreis-Sätze (Runde 2, Runde 4 und Ende der Spaltenerzeugung mit ng k = 5, je Instanz), n = 30, Breite 100, 12 Instanzen je Art", "zeilen": rows}


def main() -> None:
    vm = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_VM
    DATA.mkdir(exist_ok=True)
    for name, builder in (("knick_n30", build_knick), ("elementar", build_elementar), ("skalierung", build_skalierung), ("dssr", build_dssr)):
        data = builder(vm)
        data["quelle_ordner"] = "label-setting-planung/vormessung"
        rows = data.pop("zeilen")
        head = json.dumps(data, ensure_ascii=False)[:-1]
        body = ",\n".join(json.dumps(r, ensure_ascii=False) for r in rows)
        (DATA / f"{name}.json").write_text(f'{head}, "zeilen": [\n{body}\n]}}\n', encoding="utf-8", newline="\n")
        print(name, len(rows), "Zeilen")


if __name__ == "__main__":
    main()
