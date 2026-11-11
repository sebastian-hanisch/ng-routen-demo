"""Konstanten: Regler-Grenzen, feste Annahmen, Farben, Schnellstart-Szenarien und Texte, die App und README gemeinsam haben."""

# --- Regler ---------------------------------------------------------------------------------------------------------------------------------
# Handbeispiel: Gedächtnis k von 1 bis 7 (7 Kunden: k = 7 ist elementar); der Weg ist eine Folge von Kundennummern.
HAND_K_MIN, HAND_K_MAX, DEFAULT_HAND_K = 1, 7, 2
WALK_MAX_LENGTH = 12                     # längster Weg (Zahl der Besuche), den die Demo annimmt
WALK_TEXT_MAX = 40                       # längste Eingabe im Textfeld (Zeichen)
DEFAULT_WALK = "7-6-7"

# Zufallsinstanz (Experiment 3). Komplexität am Regler-Maximum (n = 30, Breite 100, größtes k = 12): Zahl der Labels wächst mit n, Fensterbreite und k;
# gemessen an den Zufalls-Seeds 1 bis 8 höchstens rund 1,2 Millionen erzeugte Labels über alle Stufen zusammen (Python, einige Sekunden).
# MAX_LABELS_PER_CALL fängt Ausreißer ab (ein Pricing-Aufruf bricht bei so vielen erzeugten Labels ab).
N_MIN, N_MAX, DEFAULT_N = 10, 30, 20
WIDTH_OPTIONS, DEFAULT_WIDTH = (20, 40, 100), 100
KMAX_OPTIONS, DEFAULT_KMAX = (5, 8, 12), 8
LIVE_LADDER = (1, 2, 3, 4, 5, 8, 12)     # mögliche Stufen des Live-Versuchs; verwendet werden die Stufen unter dem größten k und das größte k selbst
SEED_MAX, DEFAULT_SEED = 999999, 1
MAX_LABELS_PER_CALL = 2_000_000
ZERO_GAP_PERCENT = 1e-4                  # eine Lücke unter 0,0001 % (relativ zur Bezugsschranke) gilt als 0: Rundung der Messdateien und Rauschen des LP-Lösers

# --- Farben ---------------------------------------------------------------------------------------------------------------------------------
COLOR_OK = "#2F6B65"
COLOR_BAD = "#C0392B"
COLOR_OTHER = "rgba(150,150,150,0.55)"
COLOR_LINE = "#4c78a8"
COLOR_LINE2 = "#e08a2c"
CELL_OK = "background-color: rgba(46, 160, 67, 0.28)"
CELL_BAD = "background-color: rgba(218, 54, 51, 0.30)"

# --- Schnellstart-Szenarien -----------------------------------------------------------------------------------------------------------------
# Jedes Szenario setzt alle sechs Regler: Gedächtnis k und Weg im Handbeispiel, Kundenzahl, Fensterbreite, größtes k und Zufalls-Seed der Zufallsinstanz.
_RANDOM_DEFAULT = {"n": DEFAULT_N, "width": DEFAULT_WIDTH, "kmax": DEFAULT_KMAX, "seed": DEFAULT_SEED}
PRESETS = {
    "Kreis 7-6-7, k = 2 (Voreinstellung)": {"k": 2, "walk": "7-6-7", **_RANDOM_DEFAULT},
    "Weg 5-3-5-1, k = 2": {"k": 2, "walk": "5-3-5-1", **_RANDOM_DEFAULT},
    "Dreieck 7-6-1-7, k = 2": {"k": 2, "walk": "7-6-1-7", **_RANDOM_DEFAULT},
    "k = 1: nur direkte Wiederholung verboten": {"k": 1, "walk": "7-6-7", **_RANDOM_DEFAULT},
    "30 Kunden, enge Fenster (Breite 20)": {"k": 2, "walk": "7-6-7", "n": 30, "width": 20, "kmax": 5, "seed": 1},
    "30 Kunden, breite Fenster, k bis 12": {"k": 2, "walk": "7-6-7", "n": 30, "width": 100, "kmax": 12, "seed": 1},
}
PRESET_HELP = {
    "Kreis 7-6-7, k = 2 (Voreinstellung)": "Handbeispiel: der Weg 7-6-7 (Kunde 7, dann 6, dann wieder 7) bei Gedächtnis k = 2, dort verboten. Zufallsinstanz mit 20 Kunden, Fensterbreite 100, "
                                           "Zufalls-Seed 1 und größtem k = 8.",
    "Weg 5-3-5-1, k = 2": "Handbeispiel: der Weg 5-3-5-1 besucht Kunde 5 zweimal und ist bei k = 2 erlaubt, weil Kunde 3 den Kunden 5 nicht in seiner Nachbarschaft hat; bei k = 3 ist er verboten.",
    "Dreieck 7-6-1-7, k = 2": "Handbeispiel: der Weg 7-6-1-7 schließt einen Kreis mit drei Kanten; bei k = 2 ist er erlaubt, bei k-Zyklen K = 3 (Experiment 4) verboten.",
    "k = 1: nur direkte Wiederholung verboten": "Handbeispiel bei k = 1: Verboten ist nur ein Kunde direkt nach sich selbst, der Weg 7-6-7 ist erlaubt.",
    "30 Kunden, enge Fenster (Breite 20)": "Zufallsinstanz mit 30 Kunden, Fensterbreite 20 und größtem k = 5: Bei den Zufalls-Seeds 1 bis 8 ist die Schranke schon bei k = 1 gleich der bei k = 5.",
    "30 Kunden, breite Fenster, k bis 12": "Zufallsinstanz mit 30 Kunden, Fensterbreite 100, Zufalls-Seed 1 und größtem k = 12: Die Schranke bei k = 1 liegt 5,5 % unter der bei k = 12 und ist ab k = 4 gleich.",
}

# --- Text, den App und README gleich führen -------------------------------------------------------------------------------------------------
ASSUMPTIONS_MARKDOWN = """\
**Annahmen**
- Eigene Instanzen im Stil der Solomon-Instanzen (Quadrat 100 × 100, Fahrzeit gleich Entfernung, Bedienzeit 10, Kapazität 70, Horizont 300), **nicht die Originalinstanzen**, zufällig verteilt oder in fünf Gruppen; das Handbeispiel rechnet mit dem Manhattan-Abstand auf einem Gitter.
- Die Nachbarschaft eines Kunden besteht aus ihm und seinen k − 1 nächsten Kunden nach Abstand (Gleichstand: kleinere Nummer). Der Master ist die Überdeckung; Warten vor einem Zeitfenster ist erlaubt und kostenlos.
- Kosten gleich Entfernung gleich Fahrzeit; die Dreiecksungleichung gilt (Euklid-Abstand bei den Zufallsinstanzen, Manhattan-Abstand im Handbeispiel). Bei anderen Kosten kann sich die Rangfolge der Nachbarn und damit die Schärfe von k ändern; das ist nicht gemessen.
- Gezählt werden erzeugte Labels, nicht Sekunden.

**Grenzen**
- Die Messreihen haben 6 Instanzen je Zelle (10 bis 30 Kunden, Bezug elementar), 24 Instanzen (30 Kunden, Bezug ng k = 8) oder 12 Instanzen je Zelle (50 und 100 Kunden, Bezug k = 16); das sind Mittel und Maxima ohne Konfidenzaussage.
- Der Bezug ist nur bis 30 Kunden die elementare Schranke, und selbst dort wurde sie bei Breite 100 nur in 3 von 6 Instanzen fertig; ab 50 Kunden ist k = 16 der Bezug, und k = 16 ist selbst nur eine Relaxation.
- Gemessen sind genau diese Verfahren: Nachbarschaft nach Entfernung, Überdeckungs-Master, meine Dominanzregel für k-Zyklen (nicht die von Irnich und Villeneuve 2006) und eine eigene DSSR-Variante nach dem Abstract, nur pro Aufruf des Preisproblems und nur mit 30 Kunden.
- Die Demo macht **keine Aussage über Rechenzeit**.
- Die Live-Rechnung (Experiment 3) bricht einen Lauf ab, wenn ein Aufruf des Preisproblems mehr als 2 Millionen Labels erzeugt; abgebrochene Läufe gehen nicht in den Vergleich ein.

**Bekannte Probleme und Unsicherheiten**
- Ursachen („weil …“) sind Deutungen, wo es dasteht; gemessen sind die Zählungen.
- Die Zeilen der Messreihen stammen aus Läufen der Planung (Python 3.14.6, SciPy 1.18.1). Die Demo hat sie mit ihrem eigenen Kern nachgerechnet (Umfang: Experiment 5 und README); die DSSR-Reihe ist nicht neu gerechnet. Die Schranke einer Spaltenerzeugung ist der Zielwert eines LP und vom Weg des Lösers unabhängig, die Zahl der Runden und Labels hängt vom Weg ab und kann mit einer anderen Version der Bibliothek leicht abweichen.
- Läufe, die in der Messung an einer Zeitgrenze abbrachen, sind nicht eingerechnet; dass sie abbrachen, hing von der Last des Rechners ab.
- Die Darstellung ist im Browser am Computer durchgesehen; in einem 375 Pixel breiten Fenster sind Seitenbreite, Diagrammbreite und Konsole geprüft (keine Bildschirmansicht), nicht auf anderen Geräten oder in anderen Browsern. Die Diagramme haben keine Auswahl per Mausklick.
"""
