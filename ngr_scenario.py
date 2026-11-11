"""Szenario: Instanzen für das Preisproblem (ein Depot, Kunden mit Last, Zeitfenster; Dualpreise kommen von außen).

Zwei Arten von Instanzen:
- das **Handbeispiel** (Depot und 7 Kunden auf einem Gitter, Manhattan-Abstand, ganze Zahlen; von Hand nachrechenbar),
- **Zufallsinstanzen** im Stil der Solomon-Instanzen (Quadrat 100 x 100, Fahrzeit = Entfernung, Bedienzeit 10, Kapazität 70, Horizont 300;
  nicht die Originalinstanzen), zufällig verteilt oder in fünf Gruppen. `make_instance` zieht die Zahlen in derselben Reihenfolge wie die
  Messreihen der Planung, damit die festen Zufalls-Seeds dieselben Instanzen ergeben."""

import math
import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Instance:
    """Knoten 0 ist das Depot, die Kunden sind 1..n. Alle Tupel haben die Länge n + 1."""

    n: int
    points: tuple[tuple[float, float], ...]
    d: tuple[tuple[float, ...], ...]   # Entfernung = Fahrzeit = Kosten je Strecke
    demand: tuple[int, ...]
    ready: tuple[float, ...]           # frühester Beginn der Bedienung (früher ankommen heißt warten, kostenlos)
    due: tuple[float, ...]             # spätester Beginn der Bedienung
    service: float                     # Bedienzeit je Kunde
    horizon: float                     # spätestmögliche Rückkehr ins Depot
    capacity: int


def make_instance(n: int, seed: int, width: float, clustered: bool = False, horizon: float = 300.0, capacity: int = 70, service: float = 10.0) -> Instance:
    """Zufallsinstanz aus (n, seed, Fensterbreite, Art): gleiche Eingabe, gleiche Instanz (Zufallsgenerator `random.Random(seed)`).

    clustered=False: Kunden gleichverteilt im Quadrat. clustered=True: fünf zufällige Gruppenmitten, jeder Kunde gehört zu einer Gruppe (Normalverteilung, Streuung 6)."""
    rng = random.Random(seed)
    if clustered:
        centres = [(rng.uniform(15, 85), rng.uniform(15, 85)) for _ in range(5)]
        customers = []
        for _ in range(n):
            cx, cy = rng.choice(centres)
            customers.append((min(100.0, max(0.0, rng.gauss(cx, 6))), min(100.0, max(0.0, rng.gauss(cy, 6)))))
    else:
        customers = [(rng.uniform(0, 100), rng.uniform(0, 100)) for _ in range(n)]
    points = [(50.0, 50.0)] + customers
    d = tuple(tuple(math.dist(a, b) for b in points) for a in points)
    demand = [0] + [rng.randint(5, 25) for _ in range(n)]
    ready = [0.0] * (n + 1)
    due = [horizon] * (n + 1)
    for i in range(1, n + 1):
        lo = d[0][i]
        hi = horizon - service - d[0][i]
        center = rng.uniform(lo, hi)
        ready[i] = max(lo, center - width / 2)
        due[i] = min(hi, center + width / 2)
    return Instance(n, tuple(points), d, tuple(demand), tuple(ready), tuple(due), service, horizon, capacity)


# --- Handbeispiel ---------------------------------------------------------------------------------------------------------------------------
# Depot im Ursprung, Kunden 1 bis 7; Manhattan-Abstand, Bedienzeit 2, Kapazität 6, Rückkehr bis 38.

HAND_POINTS = ((0, 0), (-1, 2), (0, 3), (-3, -2), (-1, -2), (-2, -1), (2, 1), (3, 2))
HAND_DEMAND = (0, 1, 3, 3, 3, 1, 1, 2)
HAND_READY = (0, 18, 3, 5, 20, 3, 11, 8)
HAND_DUE = (38, 28, 16, 15, 28, 12, 21, 20)
HAND_SERVICE, HAND_HORIZON, HAND_CAPACITY = 2, 38, 6


def hand_instance() -> Instance:
    """Das Handbeispiel: Manhattan-Abstand auf einem Gitter, alle Zahlen ganz (die Zufallsinstanzen rechnen euklidisch)."""
    d = tuple(tuple(abs(a[0] - b[0]) + abs(a[1] - b[1]) for b in HAND_POINTS) for a in HAND_POINTS)
    return Instance(7, HAND_POINTS, d, HAND_DEMAND, HAND_READY, HAND_DUE, HAND_SERVICE, HAND_HORIZON, HAND_CAPACITY)


def first_round_duals(inst: Instance) -> tuple[int, ...]:
    """Dualpreise der ersten Runde: Der Master kennt nur Einzelfahrten, der Dualpreis eines Kunden ist die Einzelfahrt (zweimal der Abstand zum Depot)."""
    return (0,) + tuple(2 * inst.d[0][j] for j in range(1, inst.n + 1))
