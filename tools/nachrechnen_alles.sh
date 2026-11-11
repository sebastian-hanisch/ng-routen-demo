#!/bin/sh
# Rechnet alle Messreihen mit dem Kern der Demo nach (Reihenfolge: billig zuerst). Dauer auf einem ausgelasteten Rechner mit 3 Arbeitsprozessen: einige Stunden.
# Aufruf im Demo-Ordner: sh tools/nachrechnen_alles.sh   (Python des Test-venv: PY=... sh tools/nachrechnen_alles.sh)
PY=${PY:-../_venvs/test/Scripts/python.exe}
$PY tools/nachrechnen.py run knick --art ng --jobs 3
$PY tools/nachrechnen.py run elementar --jobs 3
$PY tools/nachrechnen.py run skalierung --n 50 --jobs 3
$PY tools/nachrechnen.py run knick --art kcyc --jobs 3
$PY tools/nachrechnen.py run skalierung --n 100 --seeds 0-2 --jobs 3
$PY tools/nachrechnen.py merge
