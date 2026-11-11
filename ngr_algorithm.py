"""Kern der Demo: Label-Setting mit begrenztem Gedächtnis (ng-Routen und k-Zyklen), Spaltenerzeugung, Aufzählung als Gegenprobe.

Aufgabe: den Weg mit den kleinsten **reduzierten Kosten** finden (Weglänge minus Dualpreise der besuchten Kunden), mit Last-, Zeitfenster- und
Horizontgrenze, wobei ein Kunde **mehrmals** vorkommen darf, solange das **Gedächtnis** es nicht verbietet. Ein **Label** hält einen Teilweg fest:
Zeit, Kosten, Last, Gedächtnis. Zwei Gedächtnisarten (`Memory`):
- `ng` mit k: Nachbarschaft NG(j) = der Kunde j und seine k - 1 nächsten Kunden. Nach jedem Besuch bleibt vom Gedächtnis nur, was in der
  Nachbarschaft des neuen Kunden liegt, dazu der neue Kunde. k = 1 verbietet nur „i direkt nach i“ (a-b-a ist erlaubt), k = n heißt elementar (jeder Kunde höchstens einmal).
- `kcyc` mit K: verboten sind alle Kreise mit höchstens K Kanten (K = 1: nur i direkt nach i). Das Gedächtnis sind die letzten K Kunden, gehalten als
  K Suffix-Mengen (Suffix der Länge s = 1..K); die Dominanz vergleicht jede dieser Mengen. **Das ist meine Dominanzregel, nicht die von Irnich und
  Villeneuve (2006)**: Sie verliert nichts (Begründung: Teilmengen der Suffixe setzen sich mit {j} ∪ S_{m-1} fort; zusätzlich gegen die Aufzählung getestet), ist aber vermutlich schwächer.

Jede Regel ist eine eigene Funktion mit expliziten Ein- und Ausgaben (DEMO-PLAYBOOK §1b): `ng_masks` (Nachbarschaften), `next_memory` (Gedächtnis nach einem
Besuch), `forbidden_mask` (was als Nächstes verboten ist), `dominates`, `extend` (Zulässigkeit einer Fortsetzung), `price` (nur die Schleife in Zeitreihenfolge),
`colgen` (nur die Runden). `walk_allowed` und `enumerate_walks` sind der Vergleichsweg ohne Labels: Die Gedächtnisregel wird als Eigenschaft des **ganzen Wegs**
geprüft, nicht als Zustand eines Labels. Kein versteckter Zustand, kein Zufall im Kern: Instanzen und Dualpreise kommen fertig herein.

Die Messgröße der Demo ist die Zahl der erzeugten Labels (jedes erzeugte Label, auch ein sofort verworfenes, plus das Start-Label), nicht die Zeit.
`exact=True` rechnet ohne Toleranz (für ganze Zahlen und Brüche, Handbeispiel); sonst gilt `EPS` für Vergleiche von Kosten und Zeiten."""

import heapq
from fractions import Fraction
from typing import NamedTuple

from ngr_scenario import Instance

EPS = 1e-9            # Toleranz für Vergleiche von Kosten und Zeiten (Gleitkomma)
IMPROVING = -1e-7     # eine Route zählt als verbessernd, wenn ihre reduzierten Kosten darunter liegen (exakt: unter 0)


class Memory(NamedTuple):
    kind: str   # "ng" oder "kcyc"
    size: int   # k bzw. K


def ng(k: int) -> Memory:
    return Memory("ng", k)


def kcyc(size: int) -> Memory:
    return Memory("kcyc", size)


class Label(NamedTuple):
    time: float     # Beginn der Bedienung am Knoten (nach Warten)
    cost: float     # reduzierte Kosten des Teilwegs
    load: int       # verbrauchte Last
    mem: object     # ng: Bitmaske der Kunden im Gedächtnis; kcyc: Tupel von K Bitmasken (Suffixe der Länge 1..K)
    node: int       # letzter Kunde (0 = Start im Depot)
    parent: int     # Nummer des Vorgänger-Labels, -1 beim Start


class PriceResult(NamedTuple):
    generated: int                         # erzeugte Labels inklusive Start-Label
    discarded: int                         # davon sofort verworfen (ein lebendes Label am selben Kunden dominiert das neue)
    displaced: int                         # ältere Labels, die ein neues Label verdrängt
    labels: tuple[Label, ...]              # alle behaltenen Labels in der Reihenfolge der Erzeugung (Nummer = Index)
    dead: tuple[bool, ...]                 # Label am Ende verdrängt?
    ended: tuple[tuple[float, int], ...]   # (reduzierte Kosten einschließlich Rückfahrt, Nummer des letzten Labels) je Weg, der ins Depot zurückkehren kann
    aborted: bool                          # Abbruch bei max_labels

    @property
    def dominated(self) -> int:
        return self.discarded + self.displaced

    @property
    def alive(self) -> int:
        return self.generated - self.discarded - self.displaced


# --- Gedächtnis -----------------------------------------------------------------------------------------------------------------------------

def ng_masks(inst: Instance, k: int) -> list[int]:
    """Nachbarschaft NG(j) als Bitmaske: der Kunde j und seine k - 1 nächsten Kunden (Gleichstand der Abstände: kleinere Nummer zuerst).
    k = 1 heißt NG(j) = {j}; k >= n heißt: alle Kunden (elementar). Index 0 (Depot) bleibt 0."""
    k = max(1, min(k, inst.n))
    masks = [0] * (inst.n + 1)
    for j in range(1, inst.n + 1):
        order = sorted(range(1, inst.n + 1), key=lambda i: (inst.d[j][i], i))
        m = 1 << j
        for i in order[:k]:
            m |= 1 << i
        masks[j] = m
    return masks


def start_memory(memory: Memory):
    """Gedächtnis des Start-Labels im Depot: leer."""
    return 0 if memory.kind == "ng" else (0,) * memory.size


def forbidden_mask(memory: Memory, mem) -> int:
    """Kunden, die als Nächstes nicht besucht werden dürfen: bei ng das ganze Gedächtnis, bei k-Zyklen die Menge der letzten K Kunden."""
    return mem if memory.kind == "ng" else mem[-1]


def next_memory(memory: Memory, mem, j: int, masks):
    """Gedächtnis nach dem Besuch von Kunde j. ng: (Gedächtnis geschnitten mit NG(j)) plus j. k-Zyklen: j vorn anfügen, den ältesten Suffix streichen."""
    b = 1 << j
    if memory.kind == "ng":
        return (mem & masks[j]) | b
    return (b,) + tuple(b | x for x in mem[:-1])


def dominates(o: Label, new: Label, memory: Memory, eps: float = EPS) -> bool:
    """Dominiert Label `o` das Label `new` (am selben Kunden)? Kosten, Zeit und Last von `o` nicht größer, und das Gedächtnis von `o` ist eine Teilmenge
    (ng: die Menge; k-Zyklen: jeder Suffix für sich, den längsten ausgenommen: er hat ohnehin den gleichen Kunden vorn)."""
    if o.cost > new.cost + eps or o.time > new.time + eps or o.load > new.load:
        return False
    if memory.kind == "ng":
        return (o.mem & ~new.mem) == 0
    om, nm = o.mem, new.mem
    for s in range(1, memory.size):
        if om[s] & ~nm[s]:
            return False
    return True


# --- Verlängern, Preisproblem ---------------------------------------------------------------------------------------------------------------

def extend(inst: Instance, pi, memory: Memory, masks, label: Label, parent: int, j: int, eps: float = EPS) -> Label | None:
    """Fortsetzung von `label` (Nummer `parent`) zum Kunden j, oder None, wenn sie unzulässig ist (Kunde j verboten, Last, Zeitfenster).
    Ankunft vor dem Fenster heißt warten (kostenlos). Die Rückkehr ins Depot prüft `price` beim Abschluss."""
    i = label.node
    if j == i or (forbidden_mask(memory, label.mem) >> j) & 1:
        return None
    load = label.load + inst.demand[j]
    if load > inst.capacity:
        return None
    arrival = label.time + (inst.service if i != 0 else 0) + inst.d[i][j]
    if arrival > inst.due[j] + eps:
        return None
    return Label(max(arrival, inst.ready[j]), label.cost + inst.d[i][j] - pi[j], load, next_memory(memory, label.mem, j, masks), j, parent)


def walk_of(labels, index: int) -> tuple[int, ...]:
    """Weg (ohne Depot) des Labels mit der Nummer `index`."""
    walk = []
    while index != -1:
        walk.append(labels[index].node)
        index = labels[index].parent
    return tuple(reversed(walk))[1:]


def price(inst: Instance, pi, memory: Memory, max_labels: int | None = None, exact: bool = False) -> PriceResult:
    """Label-Setting in Zeitreihenfolge mit Dominanz (Kosten, Zeit, Last, Gedächtnis).

    Ein neues Label wird verworfen, wenn ein lebendes Label am selben Kunden es dominiert (bei Gleichstand bleibt das ältere); sonst verdrängt es alle
    lebenden Labels, die es dominiert. Bei `max_labels` erzeugten Labels bricht der Lauf ab (aborted)."""
    eps = 0 if exact else EPS
    masks = ng_masks(inst, memory.size) if memory.kind == "ng" else None
    labels = [Label(0, 0, 0, start_memory(memory), 0, -1)]
    dead = [False]
    at_node: list[list[int]] = [[] for _ in range(inst.n + 1)]
    heap = [(0, 0)]
    generated, discarded, displaced = 1, 0, 0
    ended: list[tuple[float, int]] = []
    aborted = False
    while heap:
        _, li = heapq.heappop(heap)
        if dead[li]:
            continue
        if max_labels is not None and generated >= max_labels:
            aborted = True
            break
        label = labels[li]
        i = label.node
        if i != 0 and label.time + inst.service + inst.d[i][0] <= inst.horizon:
            ended.append((label.cost + inst.d[i][0], li))
        for j in range(1, inst.n + 1):
            new = extend(inst, pi, memory, masks, label, li, j, eps)
            if new is None:
                continue
            generated += 1
            lost = False
            for o in at_node[j]:
                if dominates(labels[o], new, memory, eps):
                    lost = True
                    break
            if lost:
                discarded += 1
                continue
            survivors = []
            for o in at_node[j]:
                if dominates(new, labels[o], memory, eps):
                    dead[o] = True
                    displaced += 1
                else:
                    survivors.append(o)
            nid = len(labels)
            labels.append(new)
            dead.append(False)
            survivors.append(nid)
            at_node[j] = survivors
            heapq.heappush(heap, (new.time, nid))
    return PriceResult(generated, discarded, displaced, tuple(labels), tuple(dead), tuple(ended), aborted)


def routes_of(inst: Instance, result: PriceResult, limit: int = 15, exact: bool = False) -> list[tuple[float, tuple[int, ...]]]:
    """Die besten verschiedenen verbessernden Wege eines Laufs (reduzierte Kosten, Weg), aufsteigend (Gleichstand: kleinere Folge zuerst); Grundlage neuer Spalten."""
    limit_value = 0 if exact else IMPROVING
    found: dict[tuple[int, ...], float] = {}
    for rc, li in result.ended:
        if rc < limit_value:
            found.setdefault(walk_of(result.labels, li), rc)
    return sorted((rc, walk) for walk, rc in found.items())[:limit]


def route_cost(inst: Instance, walk) -> float:
    """Länge eines Wegs vom Depot über die Kunden zurück zum Depot."""
    seq = (0,) + tuple(walk) + (0,)
    return sum(inst.d[a][b] for a, b in zip(seq, seq[1:]))


# --- Master und Spaltenerzeugung ------------------------------------------------------------------------------------------------------------

def solve_master_exact(inst: Instance, cols) -> tuple[list[Fraction], Fraction]:
    """Master als Überdeckung  min c x  s.t.  A x >= 1, x >= 0, exakt mit Brüchen gelöst über das Duale  max sum(pi)  s.t.  A^T pi <= c, pi >= 0
    (Simplex, Regel von Bland). Rückgabe: Dualpreise pi[0..n] (pi[0] = 0) und Zielwert. Ein Kunde, der mehrfach im Weg steht, zählt mehrfach."""
    n, m = inst.n, len(cols)
    tableau = []
    for r, walk in enumerate(cols):
        row = [Fraction(0)] * (n + m)
        for j in walk:
            row[j - 1] += 1
        row[n + r] = Fraction(1)
        tableau.append(row + [Fraction(route_cost(inst, walk))])
    obj = [Fraction(1)] * n + [Fraction(0)] * m + [Fraction(0)]
    basis = [n + r for r in range(m)]
    while True:
        entering = next((j for j in range(n + m) if obj[j] > 0), None)
        if entering is None:
            break
        best = None
        for r in range(m):
            if tableau[r][entering] > 0:
                key = (tableau[r][-1] / tableau[r][entering], basis[r])
                if best is None or key < best[0]:
                    best = (key, r)
        r = best[1]
        pivot = tableau[r][entering]
        tableau[r] = [x / pivot for x in tableau[r]]
        for i in range(m):
            if i != r and tableau[i][entering] != 0:
                f = tableau[i][entering]
                tableau[i] = [a - f * b for a, b in zip(tableau[i], tableau[r])]
        f = obj[entering]
        obj = [a - f * b for a, b in zip(obj, tableau[r])]
        basis[r] = entering
    pi = [Fraction(0)] * (n + 1)
    for r, b in enumerate(basis):
        if b < n:
            pi[b + 1] = tableau[r][-1]
    return pi, -obj[-1]


def solve_master_lp(inst: Instance, cols) -> tuple[list[float], float]:
    """Master als Überdeckung, gelöst mit HiGHS (SciPy); Rückgabe: Dualpreise pi[0..n] (pi[0] = 0) und Zielwert. Die Dualpreise sind bei Entartung nicht
    eindeutig und können mit der Version der Bibliothek wechseln; der Zielwert ist eindeutig."""
    import numpy as np
    from scipy.optimize import linprog

    n = inst.n
    a = np.zeros((n, len(cols)))
    for c, walk in enumerate(cols):
        for i in walk:
            a[i - 1, c] += 1
    res = linprog([route_cost(inst, w) for w in cols], A_ub=-a, b_ub=-np.ones(n), bounds=(0, None), method="highs")
    return [0.0] + list(-res.ineqlin.marginals), float(res.fun)


class Round(NamedTuple):
    value: float                          # Zielwert des Masters zu Beginn der Runde
    pi: tuple                             # Dualpreise der Runde
    best_rc: float                        # reduzierte Kosten des besten Wegs (0, wenn keiner verbessert)
    best_walk: tuple[int, ...]            # bester Weg ((), wenn keiner verbessert)
    generated: int
    discarded: int
    displaced: int
    alive: int
    new_columns: int                      # in dieser Runde aufgenommene Spalten


class ColgenResult(NamedTuple):
    bound: float | None                   # Schranke = Zielwert des Masters am Ende (None bei Abbruch)
    rounds: tuple[Round, ...]             # alle Runden, die letzte ohne verbessernden Weg
    columns: tuple[tuple[int, ...], ...]  # Einzelfahrten und erzeugte Spalten
    labels: int                           # erzeugte Labels aller Pricing-Aufrufe
    dominated: int
    aborted: bool

    @property
    def iterations(self) -> int:
        return len(self.rounds)


def colgen(inst: Instance, memory: Memory, master, per_round: int = 15, max_labels: int | None = None, max_rounds: int = 400, exact: bool = False) -> ColgenResult:
    """Spaltenerzeugung: Master lösen, Preisproblem mit dem Gedächtnis `memory` lösen, die besten `per_round` neuen Wege als Spalten aufnehmen, bis keiner mehr
    verbessert. `master(inst, cols) -> (Dualpreise, Zielwert)`: `solve_master_exact` (Brüche) oder `solve_master_lp`. Start: nur Einzelfahrten.
    `max_labels` gilt je Pricing-Aufruf; bei Abbruch ist die Schranke None."""
    cols = [(i,) for i in range(1, inst.n + 1)]
    colset = set(cols)
    rounds: list[Round] = []
    labels = dominated = 0
    for _ in range(max_rounds):
        pi, value = master(inst, cols)
        res = price(inst, pi, memory, max_labels=max_labels, exact=exact)
        labels += res.generated
        dominated += res.dominated
        if res.aborted:
            rounds.append(Round(value, tuple(pi), 0, (), res.generated, res.discarded, res.displaced, res.alive, 0))
            return ColgenResult(None, tuple(rounds), tuple(cols), labels, dominated, True)
        found = routes_of(inst, res, 15, exact=exact)
        fresh = [(rc, w) for rc, w in found if w not in colset][:per_round]
        best_rc, best_walk = (found[0] if found else (0, ()))
        rounds.append(Round(value, tuple(pi), best_rc, best_walk, res.generated, res.discarded, res.displaced, res.alive, len(fresh)))
        if not fresh:
            return ColgenResult(value, tuple(rounds), tuple(cols), labels, dominated, False)
        for _, w in fresh:
            cols.append(w)
            colset.add(w)
    return ColgenResult(None, tuple(rounds), tuple(cols), labels, dominated, True)


# --- Gedächtnisspur entlang eines Wegs ------------------------------------------------------------------------------------------------------

class Step(NamedTuple):
    customer: int
    before: int           # Gedächtnis vor dem Besuch (Bitmaske)
    neighbourhood: int    # NG(customer) (Bitmaske)
    kept: int             # before geschnitten mit NG(customer)
    after: int            # kept plus customer
    forbidden: bool       # stand der Kunde schon im Gedächtnis `before`?


def memory_trace(inst: Instance, k: int, walk) -> list[Step]:
    """Das Gedächtnis (ng, k) Schritt für Schritt entlang eines Wegs. Die Spur endet mit dem ersten verbotenen Besuch (forbidden=True)."""
    masks = ng_masks(inst, k)
    mem, steps = 0, []
    for j in walk:
        if (mem >> j) & 1:
            steps.append(Step(j, mem, masks[j], mem & masks[j], mem, True))
            break
        kept = mem & masks[j]
        after = kept | (1 << j)
        steps.append(Step(j, mem, masks[j], kept, after, False))
        mem = after
    return steps


def kcyc_trace(inst: Instance, size: int, walk) -> tuple[bool, str]:
    """Erlaubt oder verboten bei k-Zyklen (K = size) mit dem Grund: Kreis mit höchstens K Kanten, der als Erster geschlossen wird."""
    last: dict[int, int] = {}
    for pos, j in enumerate(walk):
        if j in last and pos - last[j] <= size:
            return False, f"Kunde {j} kommt nach {pos - last[j]} Kanten wieder"
        last[j] = pos
    return True, "kein Kreis mit höchstens %d Kanten" % size


# --- Aufzählung als Vergleichsweg (ohne Labels) ---------------------------------------------------------------------------------------------

def walk_allowed(inst: Instance, memory: Memory, walk, masks=None) -> bool:
    """Erlaubt die Gedächtnisregel diesen Weg? Eigenschaft des ganzen Wegs: Für jede Wiederholung eines Kunden j an Stelle q (vorige Stelle p) gilt bei ng:
    zwischen p und q kommt ein Kunde, in dessen Nachbarschaft j nicht liegt; bei k-Zyklen: q - p > K."""
    if memory.kind == "ng" and masks is None:
        masks = ng_masks(inst, memory.size)
    for q, j in enumerate(walk):
        p = next((x for x in range(q - 1, -1, -1) if walk[x] == j), None)
        if p is None:
            continue
        if memory.kind == "kcyc":
            if q - p <= memory.size:
                return False
        elif not any(not (masks[walk[r]] >> j) & 1 for r in range(p + 1, q)):
            return False
    return True


def walk_value(inst: Instance, pi, walk, eps: float = EPS) -> float | None:
    """Reduzierte Kosten eines Wegs von vorn nachgerechnet, oder None, wenn er unzulässig ist (Last, Zeitfenster, Horizont); Wiederholungen sind erlaubt."""
    walk = tuple(walk)
    time, load, cost, prev = 0, 0, 0, 0
    for j in walk:
        arrival = time + (inst.service if prev != 0 else 0) + inst.d[prev][j]
        load += inst.demand[j]
        if arrival > inst.due[j] + eps or load > inst.capacity:
            return None
        time = max(arrival, inst.ready[j])
        cost += inst.d[prev][j] - pi[j]
        prev = j
    if walk:
        if time + inst.service + inst.d[prev][0] > inst.horizon + eps:
            return None
        cost += inst.d[prev][0]
    return cost


def enumerate_walks(inst: Instance, pi, memory: Memory, exact: bool = False) -> list[tuple[float, tuple[int, ...]]]:
    """Alle zulässigen Wege (mindestens ein Kunde), deren Wiederholungen die Gedächtnisregel erfüllen, als (reduzierte Kosten, Weg) sortiert. Nur für kleine Instanzen."""
    eps = 0 if exact else EPS
    masks = ng_masks(inst, memory.size) if memory.kind == "ng" else None
    out: list[tuple[float, tuple[int, ...]]] = []

    def visit(walk: tuple[int, ...]) -> None:
        if walk:
            value = walk_value(inst, pi, walk, eps)
            if value is not None:
                out.append((value, walk))
        for j in range(1, inst.n + 1):
            if j == (walk[-1] if walk else 0):
                continue
            longer = walk + (j,)
            if not walk_allowed(inst, memory, longer, masks):
                continue
            if _prefix_feasible(inst, longer, eps):
                visit(longer)

    visit(())
    return sorted(out)


def _prefix_feasible(inst: Instance, walk, eps: float) -> bool:
    """Last und Zeitfenster eines Teilwegs (ohne Rückkehr); nur dann kann eine Verlängerung zulässig sein."""
    time, load, prev = 0, 0, 0
    for j in walk:
        arrival = time + (inst.service if prev != 0 else 0) + inst.d[prev][j]
        load += inst.demand[j]
        if arrival > inst.due[j] + eps or load > inst.capacity:
            return False
        time = max(arrival, inst.ready[j])
        prev = j
    return True
