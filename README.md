# ng-Routen: wie viel Gedächtnis braucht das Preisproblem? – Streamlit-Demo

Demo der Linie „Ressourcenwege und Spaltenerzeugung“ in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“. Im **Preisproblem** der Spaltenerzeugung wird der Weg mit den kleinsten **reduzierten Kosten** gesucht (Weglänge minus die **Dualpreise** der besuchten Kunden; der Dualpreis ist der Betrag, den die übergeordnete Planung einem Kunden zurechnet). Verlangt man, dass jeder Kunde höchstens einmal vorkommt (**elementar**), wird die Suche bei vielen Kunden und breiten Zeitfenstern sehr teuer; erlaubt man Kreise (einen Kunden mehrmals), wird sie bei den 24 gemessenen Zufallsinstanzen mit 30 Kunden billig (mit dem kleinsten Gedächtnis, k = 1, im Mittel das 0,50-Fache der Labels von k = 8), im Handbeispiel aber nicht (k = 1 braucht dort mehr Labels: 416 statt 326 in der ganzen Spaltenerzeugung bei einer neuen Spalte je Runde, 62 statt 56 in Runde 1), und die **Schranke**, die Schlusszahl der Spaltenerzeugung, wird schwächer. **ng-Routen** begrenzen das Gedächtnis des Labels auf eine Nachbarschaft: Jeder Kunde hat sich und seine k − 1 nächsten Kunden als Nachbarschaft, und ein Kunde darf erst wieder besucht werden, wenn auf dem Weg dazwischen ein Kunde kam, in dessen Nachbarschaft er nicht liegt. Diese Demo fragt: **Wie viel Gedächtnis, also welches k, braucht das Preisproblem, und was kostet es an Labels?** Gezählt werden erzeugte Labels, keine Sekunden.

Als Gegenstück steht das Verbot aller kurzen Kreise (**k-Zyklen**) im Experiment 4, dazu ein Absatz, warum die Demo kein eigenes Verfahren „DSSR“ zeigt. Die Anwendung in einem Fall (Besatzungsplanung im Zugverkehr) zeigt [crew-pairing-demo](https://github.com/sebastian-hanisch/crew-pairing-demo). Die Label und ihre Dominanz erklärt [dominanz-labels-demo](https://github.com/sebastian-hanisch/dominanz-labels-demo), die Kreise im Preisproblem und die Wand der elementaren Rechnung zeigen [kreise-im-pricing-demo](https://github.com/sebastian-hanisch/kreise-im-pricing-demo) und [elementar-pricing-demo](https://github.com/sebastian-hanisch/elementar-pricing-demo).
**Abgrenzung:** [hub-labeling-demo](https://github.com/sebastian-hanisch/hub-labeling-demo) meint etwas anderes (vorberechnete Listen für schnelle Abfragen kürzester Wege); hier sind Labels Teilwege.

## Warum dieses Problem

Das Preisproblem der Spaltenerzeugung ist ein kürzester Weg mit Grenzen (Zeitfenster, Last), und es wird in jeder Runde neu gelöst. Fordert man, dass jeder Kunde höchstens einmal vorkommt, wächst die Zahl der Labels mit der Kundenzahl und der Fensterbreite stark; erlaubt man Wiederholungen, kommen Wege in die Spalten, die einen Kunden mehrmals bedienen, und die Schranke liegt tiefer. Ein begrenztes Gedächtnis liegt dazwischen: Die Demo zeigt an einem Handbeispiel Schritt für Schritt, wie das Gedächtnis arbeitet, und misst an Zufallsinstanzen, wie viel Schärfe der Schranke jede Stufe von k bringt und wie viele Labels sie kostet.

## Befunde und Korrekturen gegenüber dem Plan

- **„k = 5 reicht“ gilt nur mit Zusatz.** Bei 30 Kunden liegt k = 5 bei Breite 40 in 6 von 6 Instanzen und bei Breite 100 in 3 von 3 Instanzen mit fertigem elementarem Lauf (bei den anderen 3 brach die elementare Rechnung in der Messung ab) gleich der elementaren Schranke, bei 20 und 25 Kunden und Breite 100 aber in 2 von 6 Instanzen darunter. Bei 50 und 100 Kunden liegt die Schranke bei k = 5 im Mittel je Zelle bis 0,24 % unter der Schranke bei k = 16 (in Prozent dieser Schranke), im Einzelfall bis 0,67 %; bei k = 8 im Mittel je Zelle bis 0,07 %, im Einzelfall bis 0,30 %. Eine frühere Fassung der Planung nannte für k = 8 die größte Einzellücke der gruppierten Zelle (0,24 %); die zufällige Zelle (n = 50, Breite 100) hat 0,30 %, deshalb steht hier der größere Wert.
- **Der Bezug ist k = 16, nicht die elementare Schranke,** denn die elementare Rechnung ist bei 50 und 100 Kunden in 94 von 96 Läufen abgebrochen (fertig: 2 Läufe, zufällig, n = 50, Breite 40). Die Spanne „85 bis 96 %“ für den Anteil dominierter Labels in einer früheren Fassung der Planung galt nicht für alle Zellen: zufällig, n = 50, Breite 40 sinkt bei k = 16 auf 77,7 %, der größte Wert ist 96,0 %.
- **Die Messreihe zu k-Zyklen ist eine Messreihe meiner Dominanzregel,** nicht der von Irnich und Villeneuve (2006). Die Zahlen zu „Labels pro Schärfe“ gelten für diese Regel und für die 24 gemessenen Instanzen.
- **Die Messreihe zu 5 Instanzen und dem Typ „lang“** (k = 5 gegen k = 8 bei 30 Kunden, Planung V7) ist nicht übernommen; die Reihe mit 24 Instanzen zeigt k = 5 gegen k = 8 mit mehr Instanzen.
- **Nachrechnung:** Die Zeilen der festen Messreihen stammen aus den Messdateien der Planung. Die Demo hat sie mit ihrem eigenen Kern neu gerechnet; Umfang und Ergebnis siehe Abschnitt „Nachrechnung“.

## Modell

Ein Depot und Kunden mit Last, Zeitfenster und Dualpreis; Entfernung = Fahrzeit = Kosten je Strecke; Warten vor einem Fenster ist kostenlos; Kapazität, Horizont (späteste Rückkehr) und Bedienzeit je Kunde. Ein Label am Kunden $i$ ist $(T, C, R, M)$: Zeit, reduzierte Kosten, verbrauchte Last, Gedächtnis (Menge der Kunden, die als Nächstes verboten sind). **ng-Gedächtnis:** $N_j$ ist der Kunde $j$ und seine $k-1$ nächsten Kunden (Gleichstand der Abstände: kleinere Nummer); nach dem Besuch von $j$ gilt $M' = (M \cap N_j) \cup \{j\}$, und ein Kunde darf nur besucht werden, wenn er nicht im Gedächtnis steht. $k = 1$ verbietet nur „$i$ direkt nach $i$“, $k = n$ ist elementar. **Dominanz:** $L_1$ dominiert $L_2$, wenn $C_1 \le C_2$, $T_1 \le T_2$, $R_1 \le R_2$ und $M_1 \subseteq M_2$; bei Gleichstand bleibt das ältere Label. Die Wegmengen der Größen $k$ liegen ineinander, deshalb steigt die Schranke $z(k)$ mit $k$ und liegt nie über der elementaren. Die Formeln stehen im Expander **📐 Mathematische Formulierung** der App (`app.py`), mit Lesehilfe; der Expander **💬 In einfachen Worten** fasst das Verfahren ohne Formeln zusammen ([ausführlich erklärt](https://sebastianhanisch.net/ng-routen-erklaert.html)).

Zwei Arten von Instanzen: das **Handbeispiel** (Depot und 7 Kunden, Manhattan-Abstand auf einem Gitter, alle Zahlen ganz, Bedienzeit 2, Kapazität 6, Rückkehr bis 38, Dualpreise der ersten Runde = zweimal der Abstand zum Depot; die Daten stehen in der folgenden Tabelle) und **Zufallsinstanzen im Stil der Solomon-Instanzen** (Quadrat 100 × 100, Fahrzeit gleich Entfernung, Bedienzeit 10, Kapazität 70, Horizont 300, Fensterbreite 20, 40 oder 100, zufällig verteilt oder in fünf Gruppen; **nicht die Originalinstanzen**). Die Zufallsinstanzen ziehen ihre Zahlen in derselben Reihenfolge wie die Messreihen der Planung, damit gleiche Zufalls-Seeds gleiche Instanzen ergeben.

Die Daten des Handbeispiels (Depot im Gitterpunkt (0, 0); Zeitfenster als [früh, spät]; Dualpreis = zweimal die Entfernung zum Depot):

| Kunde | Punkt | Entfernung zum Depot | Last | Zeitfenster [früh, spät] | Dualpreis (Runde 1) |
|---|---|---|---|---|---|
| 1 | (-1, 2) | 3 | 1 | [18, 28] | 6 |
| 2 | (0, 3) | 3 | 3 | [3, 16] | 6 |
| 3 | (-3, -2) | 5 | 3 | [5, 15] | 10 |
| 4 | (-1, -2) | 3 | 3 | [20, 28] | 6 |
| 5 | (-2, -1) | 3 | 1 | [3, 12] | 6 |
| 6 | (2, 1) | 3 | 1 | [11, 21] | 6 |
| 7 | (3, 2) | 5 | 2 | [8, 20] | 10 |

## Methodik

Das Label-Verfahren verlängert Labels in Zeitreihenfolge um je einen Kunden (`ngr_algorithm.py`, `price`); die Spaltenerzeugung (`colgen`) löst abwechselnd den Master (Überdeckung, `solve_master_exact` mit Brüchen für das Handbeispiel, `solve_master_lp` mit HiGHS für Zufallsinstanzen) und das Preisproblem, bis kein Weg negative reduzierte Kosten hat. Der **Vergleichsweg** (`walk_allowed`, `enumerate_walks`) zählt alle zulässigen Wege auf und prüft die Gedächtnisregel als Eigenschaft des ganzen Wegs, ohne Labels. Die **Experimente** der App: (1) das Gedächtnis entlang eines Wegs am Handbeispiel (Nachbarschaften, Schnitt, erlaubt oder verboten); (2) die Leiter der Schranke am Handbeispiel (Runde 1 und ganze Spaltenerzeugung für k = 1 bis 7 und k-Zyklen K = 2 und 3, mit Gegenprobe durch Aufzählung); (3) eine Zufallsinstanz live (Kundenzahl, Fensterbreite, größtes k, Zufalls-Seed); (4) der Kontrast k-Zyklen (live am Handbeispiel, feste Messreihe mit 24 Instanzen) und der Absatz „DSSR gestrichen“; (5) feste Messreihen: der Knick bei 30 Kunden, 50 und 100 Kunden mit Bezug k = 16 und 10 bis 25 Kunden.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen sind Zählungen erzeugter Labels (jedes erzeugte Label, auch ein sofort gestrichenes, plus das Start-Label), Schranken oder Zählungen von Instanzen an **festen Zufalls-Seeds**, Python, die genannten Instanzen und Überdeckungs-Master. Die Spalte „Test“ nennt die Prüfung in `tests/test_claims.py` bzw. die genannte Testdatei (Zahl-zu-Test-Tabelle).

**Handbeispiel, Runde 1** (ein Aufruf des Preisproblems mit den Dualpreisen der ersten Runde; „erlaubt“ heißt nur: Der Weg erfüllt die Gedächtnisregel, „zulässig“ heißt: erlaubt und zusätzlich Last, Zeitfenster und Horizont eingehalten; „Zulässige Wege“ = Aufzählung aller zulässigen Wege):

| Gedächtnis | Bester Weg | Reduzierte Kosten | Erzeugte Labels | Verworfen / verdrängt / übrig | Zulässige Wege |
|---|---|---|---|---|---|
| ng k = 1 | 7-6-7-6 | −18 | 62 | 27 / 5 / 30 | 89 |
| ng k = 2 | 5-3-5-1 | −14 | 58 | 27 / 3 / 28 | 82 |
| ng k = 3 | 2-7-6 | −10 | 55 | 25 / 3 / 27 | 79 |
| ng k = 4 | 2-7-6 | −10 | 55 | 22 / 6 / 27 | 79 |
| ng k = 5 | 2-7-6 | −10 | 56 | 23 / 3 / 30 | 79 |
| ng k = 6 | 2-7-6 | −10 | 56 | 22 / 0 / 34 | 79 |
| ng k = 7 (elementar) | 2-7-6 | −10 | 56 | 20 / 0 / 36 | 79 |
| k-Zyklen K = 2 | 2-7-6 | −10 | 57 | 14 / 1 / 42 | 79 |
| k-Zyklen K = 3 | 2-7-6 | −10 | 57 | 11 / 0 / 46 | 79 |

**Handbeispiel, Spaltenerzeugung bis zum Ende** (je Runde die beste neue Spalte, Master mit Brüchen; Lücke = (30 − Schranke) / 30, Bezug ist die elementare Schranke 30):

| Gedächtnis | Schranke | Runden | Labels (eine neue Spalte je Runde) | Lücke zur elementaren Schranke |
|---|---|---|---|---|
| ng k = 1 | 83/3 (≈ 27,67) | 8 | 416 | 7,78 % |
| ng k = 2 | 86/3 (≈ 28,67) | 8 | 382 | 4,44 % |
| ng k = 3 | 30 | 8 | 370 | 0,00 % |
| ng k = 4 | 30 | 8 | 370 | 0,00 % |
| ng k = 5 | 30 | 7 | 326 | 0,00 % |
| ng k = 6 | 30 | 7 | 326 | 0,00 % |
| ng k = 7 (elementar) | 30 | 7 | 326 | 0,00 % |
| k-Zyklen K = 2 | 30 | 7 | 328 | 0,00 % |
| k-Zyklen K = 3 | 30 | 7 | 328 | 0,00 % |

Die Labels sinken hier mit k nur, weil je Runde eine neue Spalte aufgenommen wird (k = 1 bis 4 brauchen 8 Runden, k = 5 bis 7 nur 7). Nimmt die Spaltenerzeugung je Runde bis zu 15 neue Spalten auf (Voreinstellung des Kerns und der Live-Rechnung; hier mit dem Master mit Brüchen), sind es 209, 199, 147, 146, 148, 149 und 151 Labels für k = 1 bis 7, also nicht fallend; die Schranken sind dieselben.

Für jedes Gedächtnis ergibt der Master über **alle** zulässigen Wege der Aufzählung dieselbe Schranke und denselben besten Wert wie die Spaltenerzeugung mit Labels (9 von 9 Gedächtnissen).

**Drei Beispielwege und die Gedächtnisse** (Eigenschaft des ganzen Wegs): Bei k = 2 sind die Nachbarschaften {1,2}, {1,2}, {3,4}, {3,4}, {3,5}, {6,7}, {6,7} für die Kunden 1 bis 7; Kunde 5 hat Kunde 3 als Nachbarn, Kunde 3 aber den Kunden 4.

| Weg | ng k = 1 | ng k = 2 | ng k = 3 | k-Zyklen K = 2 | k-Zyklen K = 3 |
|---|---|---|---|---|---|
| 7-6-7 | erlaubt | verboten | verboten | verboten | verboten |
| 5-3-5-1 | erlaubt | erlaubt | verboten | verboten | verboten |
| 7-6-1-7 | erlaubt | erlaubt | erlaubt | erlaubt | verboten |

**Zufallsinstanz live** (Experiment 3, ganze Spaltenerzeugung, Überdeckungs-Master, Bezug der Lücke ist das größte k): Bei 30 Kunden, Fensterbreite 100 und Zufalls-Seed 1 liegt die Schranke bei k = 1 um 5,45 % unter der bei k = 12 und ist ab k = 4 gleich (Einzelfall, erzeugte Labels 44 946 bei k = 1 und 131 082 bei k = 12). Bei 30 Kunden und Fensterbreite 20 ist die Lücke bei den Zufalls-Seeds 1 bis 8 in 8 von 8 Instanzen schon bei k = 1 gleich 0 (größtes k = 5).

**30 Kunden, 24 Instanzen, Bezug ng k = 8** (je 12 zufällig und gruppiert, Breite 100, Zufalls-Seeds 0 bis 11; Lücke zur Schranke von ng k = 8; Labels im Verhältnis zu ng k = 8, Mittel der je Instanz gebildeten Verhältnisse; abgebrochene Läufe der Messung nicht eingerechnet; eine negative Lücke heißt: Die Schranke liegt über der von ng k = 8):

| Gedächtnis | Instanzen fertig / abgebrochen | Lücke Mittel (Maximum) in % | Labels / ng k = 8 |
|---|---|---|---|
| ng k = 1 | 24 / 0 | 3,563 (7,157) | 0,50 |
| ng k = 2 | 24 / 0 | 0,920 (2,365) | 0,59 |
| ng k = 3 | 24 / 0 | 0,460 (1,116) | 0,69 |
| ng k = 4 | 24 / 0 | 0,199 (0,938) | 0,73 |
| ng k = 5 | 24 / 0 | 0,115 (0,898) | 0,80 |
| k-Zyklen K = 2 | 24 / 0 | 0,469 (1,583) | 1,69 |
| k-Zyklen K = 3 | 22 / 2 | 0,073 (0,916) | 3,52 |
| k-Zyklen K = 4 | 15 / 9 | −0,004 (0,000) | 3,39 |

Die mittlere Lücke sinkt von 3,563 % bei k = 1 auf 0,920 % bei k = 2 (der größte Sprung) und weiter auf 0,460 %, 0,199 % und 0,115 % bei k = 3, 4 und 5. Die Schranke von K = 4 liegt in 2 der 15 fertigen Instanzen über der von ng k = 8 (größte Überschreitung 0,055 %), die von K = 3 in 1 der 22 (derselben Instanz).

**k-Zyklen gegen ng bei gleichem k** (meine Dominanzregel, nur Instanzen, in denen beide Läufe fertig wurden):

| Paar | Instanzen | Schranke der k-Zyklen höher | gleich | tiefer | Labels k-Zyklen / ng (Mittel) |
|---|---|---|---|---|---|
| K = 2 gegen ng k = 2 | 24 | 23 | 0 | 1 | 2,91 |
| K = 3 gegen ng k = 3 | 22 | 20 | 2 | 0 | 5,02 |
| K = 4 gegen ng k = 4 | 15 | 7 | 8 | 0 | 4,60 |

K = 2 gegen ng k = 5 (24 Paare): Schranke der k-Zyklen tiefer in 20, gleich in 2, höher in 2 Paaren, das 2,12-Fache der Labels. K = 4 ist bei den gruppierten Instanzen in 9 von 12 Fällen an der Zeitgrenze der Messung abgebrochen (zufällig: 0 von 12).

**30 Kunden, Bezug elementar** (zufällig verteilt, 6 Instanzen je Breite, Zufalls-Seeds 0 bis 5; Lücke zur elementaren Schranke nur in Instanzen, deren elementarer Lauf fertig wurde; bei Breite 100 sind das 3 von 6, die Zufalls-Seeds 0, 1 und 5; mit allen 6 Instanzen liegt die mittlere Lücke bei k = 1 bei 3,33 % (Maximum 6,80 %), gemessen in kreise-im-pricing-demo und hier nicht neu gerechnet):

| Breite | Gedächtnis | Läufe fertig | Instanzen mit Bezug | Lücke Mittel (Maximum) in % | Instanzen mit Lücke 0 | Labels (Median) |
|---|---|---|---|---|---|---|
| 40 | ng k = 1 | 6 | 6 | 0,24 (0,72) | 2 | 16 938 |
| 40 | ng k = 3 | 6 | 6 | 0,00 (0,00) | 6 | 20 525 |
| 40 | ng k = 5 | 6 | 6 | 0,00 (0,00) | 6 | 20 904 |
| 40 | ng k = 8 | 6 | 6 | 0,00 (0,00) | 6 | 24 998 |
| 40 | ng k = 12 | 6 | 6 | 0,00 (0,00) | 6 | 25 650 |
| 40 | elementar | 6 | 6 | 0,00 (0,00) | 6 | 40 175 |
| 100 | ng k = 1 | 6 | 3 | 4,82 (6,80) | 0 | 57 330 |
| 100 | ng k = 3 | 6 | 3 | 0,52 (0,96) | 0 | 71 951 |
| 100 | ng k = 5 | 6 | 3 | 0,00 (0,00) | 3 | 92 038 |
| 100 | ng k = 8 | 6 | 3 | 0,00 (0,00) | 3 | 108 188 |
| 100 | ng k = 12 | 6 | 3 | 0,00 (0,00) | 3 | 127 900 |
| 100 | elementar | 3 | 3 | 0,00 (0,00) | 3 | 140 285 |

**10 bis 25 Kunden, k = 5 gegen elementar** (zufällig verteilt, 6 Instanzen je Zelle, Zufalls-Seeds 0 bis 5, alle elementaren Läufe fertig): k = 5 ist bei n = 10 und 15 und bei Breite 40 für alle n gleich der elementaren Schranke, bei n = 20 und 25 und Breite 100 in je 2 von 6 Instanzen nicht.

| Kunden n | Breite | Gedächtnis | Instanzen mit Lücke | Lücke Mittel (Maximum) in % |
|---|---|---|---|---|
| 10 | 40 | ng k = 1 | 1 von 6 | 0,72 (4,33) |
| 10 | 40 | ng k = 5 | 0 von 6 | 0,00 (0,00) |
| 10 | 100 | ng k = 1 | 5 von 6 | 5,45 (13,91) |
| 10 | 100 | ng k = 5 | 0 von 6 | 0,00 (0,00) |
| 15 | 40 | ng k = 1 | 3 von 6 | 0,62 (2,71) |
| 15 | 40 | ng k = 5 | 0 von 6 | 0,00 (0,00) |
| 15 | 100 | ng k = 1 | 6 von 6 | 4,47 (6,89) |
| 15 | 100 | ng k = 5 | 0 von 6 | 0,00 (0,00) |
| 20 | 40 | ng k = 1 | 2 von 6 | 0,51 (2,56) |
| 20 | 40 | ng k = 5 | 0 von 6 | 0,00 (0,00) |
| 20 | 100 | ng k = 1 | 6 von 6 | 4,42 (7,40) |
| 20 | 100 | ng k = 5 | 2 von 6 | 0,07 (0,25) |
| 25 | 40 | ng k = 1 | 6 von 6 | 0,74 (1,47) |
| 25 | 40 | ng k = 5 | 0 von 6 | 0,00 (0,00) |
| 25 | 100 | ng k = 1 | 6 von 6 | 3,98 (4,57) |
| 25 | 100 | ng k = 5 | 2 von 6 | 0,18 (0,64) |

**50 und 100 Kunden, Bezug k = 16** (12 Instanzen je Zelle, Zufalls-Seeds 0 bis 11, zufällig verteilt und gruppiert; Lücke zu k = 16 im Mittel (Maximum) in Prozent; die elementare Rechnung ist in 94 von 96 Läufen abgebrochen, deshalb ist k = 16 der Bezug und selbst nur eine ng-Relaxation):

| Zelle | k = 1 | k = 3 | k = 5 | k = 8 | k = 12 | Labels k = 16 / k = 5 (Median) | Dominiert k = 5 / k = 16 in % |
|---|---|---|---|---|---|---|---|
| n = 50, Breite 40, gruppiert | 0,84 (2,38) | 0,16 (0,46) | 0,05 (0,14) | 0,01 (0,08) | 0,01 (0,08) | 1,90 | 90,4 / 84,7 |
| n = 50, Breite 40, zufällig | 1,19 (4,29) | 0,09 (0,29) | 0,00 (0,00) | 0,00 (0,00) | 0,00 (0,00) | 1,48 | 86,5 / 77,7 |
| n = 50, Breite 100, gruppiert | 2,52 (3,65) | 0,50 (0,98) | 0,24 (0,67) | 0,07 (0,24) | 0,03 (0,18) | 2,37 | 93,0 / 89,5 |
| n = 50, Breite 100, zufällig | 3,23 (4,81) | 0,41 (1,18) | 0,12 (0,30) | 0,03 (0,30) | 0,00 (0,00) | 1,99 | 91,0 / 85,5 |
| n = 100, Breite 20, gruppiert | 0,00 (0,00) | 0,00 (0,00) | 0,00 (0,00) | 0,00 (0,00) | 0,00 (0,00) | 1,87 | 94,7 / 92,2 |
| n = 100, Breite 20, zufällig | 0,00 (0,00) | 0,00 (0,00) | 0,00 (0,00) | 0,00 (0,00) | 0,00 (0,00) | 1,72 | 92,2 / 88,7 |
| n = 100, Breite 40, gruppiert | 0,76 (1,41) | 0,17 (0,54) | 0,04 (0,18) | 0,01 (0,03) | 0,00 (0,03) | 1,93 | 95,5 / 93,5 |
| n = 100, Breite 40, zufällig | 0,88 (1,53) | 0,11 (0,24) | 0,00 (0,03) | 0,00 (0,00) | 0,00 (0,00) | 1,90 | 93,7 / 90,9 |

Bei Breite 20 und 100 Kunden ist die Lücke schon bei k = 1 gleich 0 (24 von 24 Instanzen); die Zelle sagt deshalb nichts über die Wirkung von k auf die Schranke (Deutung, nicht gemessen: Die Fenster sind so eng, dass Kreise kaum möglich sind). Die Kosten wachsen dort trotzdem mit k: Die Labels von k = 16 sind in dieser Zelle im Median das 1,87-Fache (gruppiert) bzw. 1,72-Fache (zufällig) der Labels von k = 5. Die Labels von k = 16 sind je Zelle im Median das 1,48- bis 2,37-Fache der Labels von k = 5; der Anteil dominierter Labels liegt über alle Zellen für k = 1 bis 16 zwischen 77,7 und 96,0 % und sinkt mit k; die 2 fertigen elementaren Läufe (50 Kunden, Breite 40, zufällig, k = 50) haben zusammen 50,4 %.

**DSSR** (Decremental State Space Relaxation, eigene Variante nach dem Abstract von Righini und Salani 2008; 72 feste Dualpreis-Sätze aus Runde 2, Runde 4 und vom Ende der Spaltenerzeugung mit ng k = 5, 30 Kunden, Breite 100, je 12 zufällige und gruppierte Instanzen; nur pro Aufruf des Preisproblems gemessen, nicht in der Schleife der Spaltenerzeugung; **aus der Messdatei der Planung, nicht neu gerechnet**, die Zählungen sind aus den Zeilen berechnet):

| Größe | Wert |
|---|---|
| DSSR liefert denselben Wert wie die elementare Rechnung | 66 von 66 Sätzen (in 6 Sätzen war die elementare Rechnung abgebrochen) |
| Labels DSSR / ng k = 5 (Mittel der Verhältnisse) | 6,3 |
| Labels DSSR / ng k = 8 (Mittel der Verhältnisse) | 5,2 |
| ng k = 5 verfehlt den besten Weg | 24 von 72 (Runde 2: 13, Runde 4: 11, Ende: 0 von 24) |
| Labels DSSR / ng k = 5 am Ende der Spaltenerzeugung | 11,6 |

In den gemessenen Runden 2 und 4 verfehlt ng k = 5 den besten Weg in 13 bzw. 11 von 24 Sätzen, am Ende der Spaltenerzeugung in 0 von 24; dort kostet meine DSSR-Variante das 11,6-Fache der Labels. Andere Runden und andere DSSR-Fassungen sind nicht gemessen; ein eigenes Verfahren zeigt die Demo deshalb nicht.

**Zahl-zu-Test-Tabelle**

| Zahl oder Aussage | Test |
|---|---|
| Handbeispiel: Nachbarschaften, Gedächtnisspuren, reduzierte Kosten der drei Wege | `test_algorithm.py::test_neighbourhoods_k1_to_k4_by_hand`, `test_memory_trace_by_hand`, `test_reduced_costs_of_the_three_best_walks_by_hand` |
| Runde 1 und Spaltenerzeugung am Handbeispiel (Tabellen oben, exakt) | `test_algorithm.py::test_round_one_table_by_hand_script`, `test_column_generation_on_the_hand_example`; Tabellen in der README: `test_claims.py::test_the_hand_example_tables_are_in_the_readme` |
| Daten des Handbeispiels; „erlaubt“ gegen „zulässig“; Labels je Runde (eine gegen 15 neue Spalten); Aussagen der Einleitung | `test_claims.py::test_erlaubt_and_zulaessig_are_told_apart_and_the_hand_data_are_in_the_readme`, `test_the_labels_of_the_hand_example_fall_with_k_only_for_one_new_column_per_round`, `test_the_readme_intro_names_where_cycles_are_cheap_and_where_not` |
| 89, 82, 79 zulässige Wege; Schranke über alle Wege gleich | `test_oracle_ng_routen.py::test_oracle_on_the_hand_example`, `test_claims.py::test_the_counterproof_over_all_walks` |
| 24 Instanzen, n = 30: Lücken, Labels, Paare, Instanzmengen des Vergleichs | `test_claims.py::test_knick_table_and_pairs`, `test_the_k_cycle_contrast_names_its_instance_sets` |
| 30 Kunden, Bezug elementar; 10 bis 25 Kunden | `test_claims.py::test_elementary_reference_tables`, `test_the_statements_about_30_customers_name_their_instances` |
| 50 und 100 Kunden: Lücken, Faktoren, Anteile, 94 von 96, Breite 20 | `test_claims.py::test_scaling_tables_and_headline_numbers`, `test_the_scaling_side_statements_dominated_share_and_cost_at_width_20` |
| DSSR: 6,3 / 5,2 / 24 von 72 / 11,6 | `test_claims.py::test_dssr_numbers` |
| Zufallsinstanz live: 5,45 %, ab k = 4; Breite 20 in 8 von 8 | `test_presets.py::test_the_help_texts_state_what_the_computation_shows`, `test_claims.py::test_live_instance_numbers` |
| Stichproben der Messreihen mit dem Kern neu gerechnet | `test_claims.py::test_sample_rows_are_recomputed_with_the_kernel` |
| Ergebnis der vollständigen Nachrechnung | `test_claims.py::test_the_recomputation_report_is_consistent` (Messung dieser README über `tools/nachrechnen.py`, nicht im Test neu gerechnet) |
| Zeilen der Messreihen gleich den Rohdateien der Planung (Stichprobe, nur wenn die Planung neben der Demo liegt) | `test_claims.py::test_rows_equal_the_raw_files_of_the_planning` |

## Nachrechnung

Die vier Messreihen stammen aus Ausgabedateien der Planung (Python 3.14.6, SciPy 1.18.1). `tools/baender_bauen.py` liest sie in `data/*.json` ein (jede Zeile mit Quelle `Datei:Zeile`), `tools/nachrechnen.py` rechnet jede Zeile, die in der Messung fertig wurde, mit dem Kern dieser Demo neu und vergleicht Schranke (auf die Stellen der Rohdatei), Zahl der erzeugten Labels, Zahl der Runden und, wo die Rohdatei sie nennt, Zahl der dominierten Labels. Ergebnis in `data/nachrechnung.json`, die einzelnen Läufe in `tools/nachrechnung/*.jsonl`:

| Messreihe | Zeilen | In der Messung abgebrochen | Neu gerechnet | Schranke gleich | Labels gleich | Runden gleich | Dominierte gleich |
|---|---|---|---|---|---|---|---|
| 24 Instanzen, n = 30 | 216 | 11 | 205 | 205 | 205 | 205 | – |
| n = 10 bis 30, Bezug elementar | 216 | 3 | 213 | 213 | 213 | 213 | – |
| n = 50 und 100, Bezug k = 16 | 672 | 94 | 362 | 362 | 362 | 362 | 362 von 362 |

Zeilen, die in der Messung an einer Zeitgrenze abbrachen (11 + 3 + 94 Läufe), sind nicht neu gerechnet: Dass sie abbrachen, hing von der Last des Rechners ab. Bei den vier Zellen mit 100 Kunden (Breite 20 und 40, zufällig und gruppiert) sind nur die Zufalls-Seeds 0 bis 2 neu gerechnet (72 von 288 fertigen Läufen); die übrigen 216 Läufe (Zufalls-Seeds 3 bis 11) stammen nur aus der Messdatei der Planung. Alle anderen in der Messung fertigen Läufe sind neu gerechnet (780 von 996). **Die DSSR-Reihe ist nicht neu gerechnet** (der Kern enthält kein DSSR). Der Abgleich gilt für diese Python- und SciPy-Version und Windows; auf anderen Versionen kann der Weg des LP-Lösers und damit die Zahl der Runden und Labels abweichen, die Schranke nicht (sie ist der Zielwert eines LP). Deshalb prüft `test_claims.py` eine Stichprobe der Zeilen exakt, wenn die Umgebung die der Messung ist (Windows, SciPy 1.18.1), und sonst in einem Band.

## Ehrliche Grenzen

- Eigene Instanzen im Stil der Solomon-Instanzen, **nicht die Originalinstanzen**; 6 bis 12 Instanzen je Zelle (24 beim Kontrast), keine Konfidenzaussage. „k = 5 reicht“ gilt nur im Sinn der Zahlen oben und hängt an der Fensterbreite.
- Bezug: elementar nur bis 30 Kunden (bei Breite 100 und 30 Kunden in 3 von 6 Instanzen fertig), sonst k = 8 (24 Instanzen) bzw. k = 16 (50 und 100 Kunden). Wie weit k = 16 selbst unter der elementaren Schranke liegt, ist nicht gemessen.
- Gemessen sind genau diese Verfahren: Nachbarschaft nach Entfernung, Überdeckungs-Master, meine Dominanzregel für k-Zyklen (nicht die von Irnich und Villeneuve 2006; mit deren Regel könnten die k-Zyklen weniger Labels brauchen), eine eigene DSSR-Variante nach dem Abstract (nicht nach dem Volltext von Righini und Salani 2008), nur pro Aufruf und nur mit 30 Kunden. Andere Nachbarschaften, Partitionierung, nichtmetrische Kosten, Instanzen mit mehr als 100 Kunden und Dualpreise aus einem Verzweigungsbaum sind nicht gemessen.
- Die Demo macht **keine Aussage über Rechenzeit**; Sekunden hängen vom Rechner ab und stehen in keinem Test.
- Literatur (Prüfstand: Autoren, Zeitschrift und Jahr per Abstract und Suchtreffer geprüft, Volltexte außer dem Hinweis auf den Ursprung der ng-Routen in Pessoa u. a. nicht gelesen, keine Zahl daraus übernommen): Baldacci, Mingozzi, Roberti (2011), Operations Research 59(5):1269–1283; Irnich, Villeneuve (2006), INFORMS Journal on Computing 18(3):391–406; Righini, Salani (2008), Networks 51(3):155–170; Christofides, Mingozzi, Toth (1981), Networks 11(2):145–164; Pessoa, Sadykov, Uchoa, Vanderbeck (2020), Mathematical Programming 183:483–523.

Annahmen, Grenzen und bekannte Probleme, wie sie auch in der App stehen (ein Test prüft, dass beide Fassungen gleich sind):

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

## Verifikation

- **Kern:** je Einheit gegen Handrechnung am Handbeispiel (`tests/conftest.py`, `tests/test_algorithm.py`): Nachbarschaften, Gedächtnisspuren, Fortsetzung, Dominanz je Bedingung, Runde 1 und Spaltenerzeugung für alle neun Gedächtnisse, exakter gegen LP-Master, Abbruch bei zu vielen Labels, Worst-Case am Regler-Maximum (ohne Zeitvergleich).
- **Orakel** (`tests/test_oracle_ng_routen.py`): Tiefensuche über alle zulässigen Wege ohne Labels, mit Mengen-Simulation des Gedächtnisses und Nachbarschaften aus `numpy.argsort` (selbst am Handbeispiel geprüft: 89, 82 und 79 Wege), gegen das Label-Verfahren für ng k = 1, 2, 3, elementar und k-Zyklen K = 2 und 3, und gegen die Schranke der Spaltenerzeugung (Master über alle aufgezählten Wege mit `linprog`); Trennschärfe: Jede Stufe weicht von der Nachbarstufe ab. Im Bauprotokoll zusätzlich 5 040 Preisprobleme (n = 6 und 7, 7 Gedächtnisse, 720 Instanzen) und 400 Schranken (n = 5) gegen das Orakel ohne Abweichung (nicht im Repo).
- **Eigenschaften** (`tests/test_eigenschaften_ng_routen.py`): Schranke steigt mit k und liegt nie über der elementaren; k-Zyklen nie über elementar; breitere Fenster heben die Schranke nie; Umnummerieren ändert nur Namen; Skalieren aller Längen, Zeiten und Dualpreise mit 2 ändert nur die Einheit; derselbe Lauf in zwei Prozessen mit anderem Hash-Seed gleich.
- **Randfälle** (`tests/test_edge_cases.py`): ein und zwei Kunden, k an den Rändern, Gleichstand der Abstände, Asymmetrie, Fensterende und Horizont inklusive, Dualpreise 0, Fenster ohne zweiten Besuch, Eingabe des Wegs.
- **Zahlen der README** (`tests/test_claims.py`): die Tabellen oben werden aus den Messreihen und dem Kern berechnet und müssen wörtlich in der README stehen; Stichproben der Zeilen werden mit dem Kern neu gerechnet; die vollständige Nachrechnung steht in `data/nachrechnung.json`.
- **Verdikte** (`tests/test_verdicts.py`) und **je Schnellstart-Szenario die erwartete Verdikt-Zeile** (`tests/test_presets.py`, `tests/test_app.py`).
- **Oberfläche:** AppTest-Rauchtest (jeder Knopf, jeder Regler und jede Option am Minimum und Maximum, ungültiger Weg, Permalink mit ungültigen Werten), Layout (fester Kopf, Schnellstart in der Seitenleiste, Hervorhebung), Footer, Laufzeit-Importe.
- **Testzahl:** 186 Tests (`pytest --collect-only -q tests`).

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: Kopf, Handbeispiel, fünf Experimente, Grenzen, Formeln, Fußzeile |
| `ngr_algorithm.py` | Kern: Label-Verfahren mit ng- und k-Zyklen-Gedächtnis, Dominanz, Fortsetzung, Spaltenerzeugung (Master mit Brüchen und mit HiGHS), Gedächtnisspur, Aufzählung aller Wege |
| `ngr_constants.py` | Regler-Grenzen, Farben, Schnellstart-Szenarien, gemeinsamer Text der Annahmen |
| `ngr_evaluation.py` | Handbeispiel-Auswertung, Leiter, Live-Versuch, Tabellen der Messreihen, Verdikte (reine Funktionen) |
| `ngr_layout.py` | Fester Kopf (Stylesheet) |
| `ngr_presets.py` | Permalink (Begrenzen), Schnellstart in der Seitenleiste, aktives Szenario hervorgehoben, Zufalls-Seed-Knopf |
| `ngr_scenario.py` | Handbeispiel, Zufallsinstanzen im Solomon-Stil |
| `ngr_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `data/knick_n30.json`, `data/elementar.json`, `data/skalierung.json`, `data/dssr.json` | feste Messreihen, jede Zeile mit Quelle |
| `data/nachrechnung.json` | Ergebnis der Nachrechnung mit dem Kern der Demo |
| `tools/baender_bauen.py` | erzeugt `data/*.json` aus den Rohausgaben der Planung |
| `tools/nachrechnen.py`, `tools/nachrechnen_alles.sh` | rechnet die Messreihen mit dem Kern neu und fasst zusammen; die einzelnen Läufe stehen in `tools/nachrechnung/` |
| `tools/readme_tabellen.py` | erzeugt die Zahlentabellen der README aus Kern und Daten |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `tests/` | siehe Verifikation |

## Bewusst nicht umgesetzt

- Keine Aussage über Rechenzeit und keine Zeitmessung in der App.
- Kein DSSR als Verfahren (nur der Absatz mit dem Befund aus der Messdatei), keine Dominanz der k-Zyklen nach Irnich und Villeneuve.
- Keine Subset-Row-Schnitte, keine bidirektionale Suche, keine Eimer, keine Kantenstreichung, kein heuristisches Pricing, kein Verzweigen.
- Keine andere Wahl der Nachbarschaft (nur nach Entfernung), keine Partitionierung, keine nichtmetrischen Kosten.
- Keine Live-Rechnung mit mehr als 30 Kunden (die Bänder für 50 und 100 Kunden sind feste Messreihen).
- Kein PDF-Export.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

Python 3.12 oder neuer (die CI läuft mit 3.12). Die in der Streamlit Cloud eingestellte Python-Version ist beim ersten Deploy einzutragen. <!-- lint-ok: dezimalpunkt -->

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, pandas und SciPy.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Ressourcenwege: von der Grenze zur Verfahrenswahl](https://sebastianhanisch.net/konzepte-ressourcenwege.html).
