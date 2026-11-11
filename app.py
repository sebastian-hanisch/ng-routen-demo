"""ng-Routen: wie viel Gedächtnis braucht das Preisproblem? - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Preisproblem der Spaltenerzeugung mit begrenztem Gedächtnis (ng-Routen): Ein Kunde darf mehrmals vorkommen, solange das Gedächtnis des Labels ihn vergessen hat.
Handbeispiel Schritt für Schritt, Leiter der Schranke, Zufallsinstanz live, Kontrast k-Zyklen und feste Messreihen bis 100 Kunden.

Lauffähig mit: streamlit run app.py
"""

import pandas as pd
import streamlit as st

import ngr_algorithm as A
import ngr_constants as C
import ngr_evaluation as ev
from ngr_layout import dunkles_design, kopf_css
from ngr_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from ngr_visualization import (
    build_contrast_chart,
    build_hand_map,
    build_knick_chart,
    build_ladder_gap_chart,
    build_ladder_labels_chart,
    build_live_chart,
)

st.set_page_config(page_title="ng-Routen – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _live(n, width, seed, kmax):
    return ev.live_ladder(n, width, seed, kmax)


@st.cache_data(show_spinner=False)
def _tables():
    knick = ev.load_rows("knick_n30")
    elementar = ev.load_rows("elementar")
    skal = ev.load_rows("skalierung")
    return {
        "knick": ev.knick_table(knick),
        "knick_cluster": ev.knick_table(knick, "cluster"),
        "knick_pairs": ev.knick_pairs(knick),
        "knick_k2_ng5": ev.knick_compare_k2_ng5(knick),
        "elementar": {n: ev.elementar_table(elementar, n) for n in (10, 15, 20, 25, 30)},
        "skal": ev.skalierung_table(skal),
        "skal_elementar": ev.skalierung_elementar(skal),
        "dssr": ev.dssr_summary(ev.load_rows("dssr")),
        "check": ev.load_check(),
    }


def _name(art, k):
    return f"ng k = {k}" if art == "ng" else f"k-Zyklen K = {k}"


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in ngr_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🧩 ng-Routen: wie viel Gedächtnis braucht das Preisproblem?")
st.markdown(
    """
Im **Preisproblem** der Spaltenerzeugung wird der Weg mit den kleinsten **reduzierten Kosten** gesucht (Weglänge minus die **Dualpreise** der besuchten Kunden; der Dualpreis ist der Betrag,
den die übergeordnete Planung einem Kunden zurechnet). Verlangt man, dass jeder Kunde höchstens einmal vorkommt (**elementar**), wird die Suche bei vielen Kunden und breiten Zeitfenstern sehr teuer;
erlaubt man Kreise, wird sie bei den Zufallsinstanzen mit 30 Kunden billig (im Handbeispiel nicht, siehe Punkt 4 unten), aber die **Schranke** (die Schlusszahl der Spaltenerzeugung, eine Untergrenze für die Gesamtplanung) wird schwächer. **ng-Routen** sind der Mittelweg:
Jeder Kunde hat eine **Nachbarschaft** aus sich und seinen k − 1 nächsten Kunden, und ein Teilweg (**Label**) merkt sich nur, welche Kunden der Nachbarschaften er noch nicht „vergessen“ hat.
Diese Demo fragt: **Wie viel Gedächtnis, also welches k, braucht das Preisproblem?** Die Antwort kommt am Handbeispiel Schritt für Schritt, an einer Zufallsinstanz live und aus festen Messreihen bis 100 Kunden;
als Gegenstück steht das Verbot aller kurzen Kreise (k-Zyklen) daneben.

Weiter unten: die Expander **💬 In einfachen Worten** und **So funktioniert ng-Routen** (beide zuerst), fünf Experimente (**🔬**), **🚧 Wo die Annahmen enden**, **📐 Mathematische Formulierung** und
**⚠️ Annahmen, Grenzen und bekannte Probleme**. Die Anwendung dieses Verfahrens in einem Fall (Besatzungsplanung im Zugverkehr) zeigt
[crew-pairing-demo](https://github.com/sebastian-hanisch/crew-pairing-demo). Nicht zu verwechseln mit [hub-labeling-demo](https://github.com/sebastian-hanisch/hub-labeling-demo): Dort sind Labels vorberechnete
Listen für schnelle Abfragen kürzester Wege, hier sind es Teilwege im Preisproblem der Spaltenerzeugung.
"""
)

# erklaerseite:einfach:start (erzeugt von tools/set_demo_explainer.py (Website-Repo) aus tools/content/explainers/ng-routen-erklaert.json, nicht von Hand ändern)
with st.expander("💬 In einfachen Worten"):
    st.markdown(
        """
Im **Preisproblem** der Spaltenerzeugung sucht die Planung den Weg, der sich am meisten lohnt: Weglänge minus die Preise der besuchten Kunden. Darf ein Kunde beliebig oft vorkommen, wird die Suche in den Zufallsbeispielen der Demo billiger (im kleinen Handbeispiel nicht), aber die **Schranke** (die Untergrenze für die Gesamtplanung) kann schwächer werden. Muss jeder Kunde höchstens einmal vorkommen, wird die Suche bei vielen Kunden und breiten Zeitfenstern sehr teuer. **ng-Routen** liegen dazwischen: Jeder Kunde hat eine **Nachbarschaft** aus sich und seinen nächsten Kunden, und ein Teilweg merkt sich nur, welche Kunden daraus noch gesperrt sind. Ein Kunde darf erst wieder besucht werden, wenn dazwischen ein Kunde kam, in dessen Nachbarschaft er nicht liegt. Die Demo fragt, wie groß die Nachbarschaft sein muss, und zählt, was das an Teilwegen (Labels) kostet.

[Ausführlich und verständlich erklärt, mit Fachteil](https://sebastianhanisch.net/ng-routen-erklaert.html)
        """
    )
# erklaerseite:einfach:end

with st.expander("So funktioniert ng-Routen", expanded=True):
    st.markdown(
        """
1. **Das Preisproblem sucht einen Weg:** vom Depot über Kunden zurück, mit Last-, Zeitfenster- und Rückkehrgrenze. Seine **reduzierten Kosten** sind die Länge minus die Dualpreise der besuchten Kunden;
   ein Weg mit negativen reduzierten Kosten ist eine neue Spalte für die Planung. Die Spaltenerzeugung wiederholt das, bis kein Weg mehr verbessert; die Schlusszahl ist die **Schranke**. Das ist eine einzige Zahl mit zwei Rollen: der Zielwert des Masters am Ende der Spaltenerzeugung und zugleich
   eine Untergrenze für die Kosten der Gesamtplanung (weil jeder elementare Weg auch ein erlaubter Weg ist).
   Erlaubt das Preisproblem mehr Wege, findet es mehr Spalten, und die Schranke ist **niedriger** (schwächer).
2. **Ein Label ist ein Teilweg in vier Zahlen:** reduzierte Kosten, Zeit, Last und **Gedächtnis**. Das Gedächtnis sagt, welche Kunden als Nächstes verboten sind. Ein Label darf gestrichen werden, wenn ein anderes
   am selben Kunden in allen vier Größen mindestens so gut ist (Dominanz; das Gedächtnis des besseren Labels muss dafür eine Teilmenge sein).
3. **Die Nachbarschaft NG(j)** besteht aus dem Kunden j und seinen k − 1 nächsten Kunden (Gleichstand der Abstände: kleinere Nummer zuerst). Nach dem Besuch eines Kunden j bleibt vom Gedächtnis nur,
   **was in NG(j) liegt**, dazu kommt j selbst. Ein Kunde darf also erst wieder besucht werden, wenn auf dem Weg dazwischen ein Kunde kam, in dessen Nachbarschaft er nicht liegt.
4. **k stellt die Strenge ein:** Bei k = 1 ist nur „Kunde i direkt nach Kunde i“ verboten (Kreise sind sonst frei), bei k gleich der Kundenzahl bleibt jeder besuchte Kunde im Gedächtnis (**elementar**).
   Die Nachbarschaften wachsen mit k ineinander hinein; deshalb steigt die Schranke mit k und liegt nie über der elementaren; bei den Zufallsinstanzen mit 30 Kunden entstehen im Mittel mehr Labels (im Handbeispiel nicht: dort sinken sie mit k, aber nur bei einer neuen Spalte je Runde, wie sie Experiment 2 aufnimmt; mit mehr neuen Spalten je Runde sind sie nicht fallend).
5. **Die Frage der Demo:** Ab welchem k ist die Schranke so scharf wie die elementare (Lücke 0), und was kostet das an Labels? Das Handbeispiel zeigt jeden Schritt, die Messreihen zählen es an vielen Instanzen.

Merksatz: **Das Gedächtnis ist ein Schieberegler zwischen „Kreise erlaubt“ und „jeder Kunde höchstens einmal“.**
"""
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Szenario ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Handbeispiel** (Experimente 1 und 2)")
    hand_k = st.slider("Gedächtnis k", *bounds("k_slider"), key="k_slider",
                       help="Größe der Nachbarschaft: der Kunde und seine k − 1 nächsten Kunden. Im Handbeispiel (7 Kunden) ist k = 7 elementar.")
    walk_text = st.text_input("Weg", key="walk_text", max_chars=C.WALK_TEXT_MAX,
                              help="Kunden in der Reihenfolge des Besuchs, mit Bindestrich getrennt, zum Beispiel 5-3-5-1 (Kunden 1 bis 7, höchstens 12 Besuche, nie derselbe Kunde zweimal direkt hintereinander).")
    st.markdown("**Zufallsinstanz** (Experiment 3)")
    n = st.slider("Kunden n", *bounds("n_slider"), key="n_slider", help="Zahl der Kunden der Zufallsinstanz (10 bis 30).")
    width = st.radio("Fensterbreite", C.WIDTH_OPTIONS, key="width_radio", horizontal=True,
                     help="Breite der Zeitfenster der Kunden in Zeiteinheiten (Horizont 300). Breite Fenster lassen viel mehr Wege zu.")
    kmax = st.radio("Größtes k (Bezug der Lücke)", C.KMAX_OPTIONS, key="kmax_radio", horizontal=True,
                    help="Verglichen werden die Stufen k = 1, 2, 3, 4, 5, 8, 12 bis zu diesem k. Die Lücke bezieht sich auf die Schranke bei diesem größten k, nicht auf die elementare.")
    seed = st.number_input("Zufalls-Seed der Instanz", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)

sync_query_params({"k_slider": int(hand_k), "walk_text": walk_text, "n_slider": int(n), "width_radio": int(width), "kmax_radio": int(kmax), "seed_input": int(seed)})

inst, duals = ev.hand()
ladder = ev.hand_ladder()
tables = _tables()
walk = ev.parse_walk(walk_text, inst.n)

# --- Ergebnis: das Handbeispiel ------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Das Handbeispiel: sieben Kunden, ein Gedächtnis")
st.markdown(
    "Ein Fahrzeug startet im Depot (Gitterpunkt (0, 0)) und besucht Kunden; hier darf ein Kunde **mehrmals** vorkommen, wenn das Gedächtnis es erlaubt. **Entfernung = Fahrzeit = Manhattan-Abstand** "
    f"(Zeilen plus Spalten auf dem Gitter, so bleiben alle Zahlen ganz). Bedienzeit {inst.service}, Rückkehr spätestens zur Zeit {inst.horizon}, Last höchstens {inst.capacity}. Wer vor Beginn "
    "seines Fensters ankommt, wartet kostenlos. Die **Dualpreise** sind die der ersten Runde der Spaltenerzeugung: Der Planung sind nur die Einzelfahrten bekannt, und jeder Kunde kostet zweimal seinen Abstand zum Depot."
)
st.dataframe(
    pd.DataFrame(
        {
            "Kunde": list(range(1, inst.n + 1)),
            "Punkt": [f"({inst.points[i][0]}, {inst.points[i][1]})" for i in range(1, inst.n + 1)],
            "Entfernung zum Depot": [inst.d[0][i] for i in range(1, inst.n + 1)],
            "Last": [inst.demand[i] for i in range(1, inst.n + 1)],
            "Zeitfenster [früh, spät]": [f"[{inst.ready[i]}, {inst.due[i]}]" for i in range(1, inst.n + 1)],
            "Dualpreis (Runde 1)": [duals[i] for i in range(1, inst.n + 1)],
        }
    ),
    hide_index=True, width="stretch",
)
analysis = ev.analyse_walk(int(hand_k), walk) if walk else None
m1, m2, m3 = st.columns(3)
m1.metric("Gedächtnis", f"k = {int(hand_k)}", help=f"Nachbarschaft: der Kunde und seine {int(hand_k) - 1} nächsten Kunden.")
m2.metric("Weg", ev.fmt_walk(walk) if walk else "ungültig")
m3.metric("Urteil", "–" if analysis is None else ("erlaubt" if analysis.allowed else "verboten"))
if walk:
    st.plotly_chart(build_hand_map(inst, int(hand_k), walk, analysis), width="stretch", key="hand_map")
    st.caption("Grün: der Weg bis zum ersten verbotenen Besuch (bei einem erlaubten Weg mit Rückfahrt zum Depot), rot gestrichelt: die verbotene Fahrt. Pfeile: die Nachbarschaft jedes Kunden auf dem Weg "
               "(von j zu den k − 1 nächsten Kunden); grau, wenn die Nachbarschaft gegenseitig ist, orange, wenn nicht. Die Linien folgen dem Gitter (erst waagerecht, dann senkrecht).")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Ab welchem k ist die Schranke so scharf wie die elementare?")
kind, text = ev.verdict_ladder(ladder)
getattr(st, kind)(text)
with st.spinner("Rechnet die Zufallsinstanz (bei 30 Kunden und breiten Fenstern dauert das einige Sekunden) …"):
    live = _live(int(n), int(width), int(seed), int(kmax))
kind, text = ev.verdict_live(live, int(n), int(width))
getattr(st, kind)(text)
st.caption("Erste Zeile: das Handbeispiel (Experiment 2). Zweite Zeile: die Zufallsinstanz der Seitenleiste (Experiment 3), Bezug ist dort das größte gewählte k. Feste Messreihen mit bis zu 100 Kunden stehen in Experiment 5.")

st.markdown("---")

# --- Experiment 1 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 1: Das Gedächtnis entlang eines Wegs")
st.caption(
    f"Handbeispiel mit k = {int(hand_k)} und dem Weg aus der Seitenleiste. Nach jedem Kunden j wird das Gedächtnis mit der Nachbarschaft NG(j) geschnitten, danach kommt j hinzu. "
    "**Verboten** ist ein Besuch, wenn der Kunde im Gedächtnis steht; **erlaubt** heißt nur, dass die Gedächtnisregel den Weg zulässt, **zulässig** ist ein Weg erst, wenn zusätzlich Last, Zeitfenster und Horizont stimmen. Probieren Sie 7-6-7, 5-3-5-1 und 7-6-1-7 bei k = 1, 2 und 3."
)
if walk is None:
    st.warning(f"Der Weg „{walk_text}“ ist ungültig. Erwartet werden Kundennummern von 1 bis {inst.n}, mit Bindestrich getrennt (zum Beispiel 5-3-5-1), höchstens {C.WALK_MAX_LENGTH} Besuche, "
               "und nie derselbe Kunde zweimal direkt hintereinander.")
else:
    rows = []
    for number, step in enumerate(analysis.steps, start=1):
        rows.append({
            "Schritt": number,
            "Kunde j": step.customer,
            "Gedächtnis vorher": ev.fmt_set(step.before, inst.n),
            "Nachbarschaft NG(j)": ev.fmt_set(step.neighbourhood, inst.n),
            "Schnitt": "–" if step.forbidden else ev.fmt_set(step.kept, inst.n),
            "Gedächtnis nachher": "–" if step.forbidden else ev.fmt_set(step.after, inst.n),
            "Urteil": f"verboten: Kunde {step.customer} steht im Gedächtnis" if step.forbidden else "erlaubt",
        })
    df1 = pd.DataFrame(rows)
    st.dataframe(df1.style.map(lambda v: C.CELL_BAD if str(v).startswith("verboten") else (C.CELL_OK if v == "erlaubt" else ""), subset=["Urteil"]), hide_index=True, width="stretch")
    kind, text = ev.verdict_walk(int(hand_k), walk, analysis, inst.n)
    getattr(st, kind)(text)
masks = A.ng_masks(inst, int(hand_k))
st.markdown(f"**Alle Nachbarschaften bei k = {int(hand_k)}** (nach Abstand, Gleichstand: kleinere Nummer zuerst)")
st.dataframe(
    pd.DataFrame(
        {
            "Kunde j": list(range(1, inst.n + 1)),
            "Nachbarschaft NG(j)": [ev.fmt_set(masks[j], inst.n) for j in range(1, inst.n + 1)],
            "Kunden, die j in ihrer Nachbarschaft haben": [ev.fmt_set(sum(1 << i for i in range(1, inst.n + 1) if (masks[i] >> j) & 1), inst.n) for j in range(1, inst.n + 1)],
        }
    ),
    hide_index=True, width="stretch",
)
asym = [(i, j) for i in range(1, inst.n + 1) for j in range(1, inst.n + 1) if i != j and (masks[i] >> j) & 1 and not (masks[j] >> i) & 1]
if asym:
    i, j = asym[0]
    st.caption(f"Die Nachbarschaft ist **nicht symmetrisch**: bei k = {int(hand_k)} gibt es {len(asym)} Paare, in denen ein Kunde einen anderen als Nachbarn hat, dieser ihn aber nicht "
               f"(zum Beispiel hat Kunde {i} den Kunden {j} als Nachbarn, Kunde {j} den Kunden {i} aber nicht).")
else:
    st.caption(f"Bei k = {int(hand_k)} ist die Nachbarschaft in diesem Beispiel symmetrisch (kein Paar mit nur einseitiger Nachbarschaft).")

st.markdown("---")

# --- Experiment 2 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 2: Die Leiter der Schranke am Handbeispiel")
st.caption(
    "Spaltenerzeugung bis zum Ende (je Runde die beste neue Spalte, Master mit exakten Brüchen) für jedes Gedächtnis: ng-Routen mit k = 1 bis 7 und, als Kontrast, k-Zyklen (Experiment 4). "
    "„Runde 1“ ist ein einziger Aufruf des Preisproblems mit den Dualpreisen der ersten Runde; „Labels“ zählt jedes erzeugte Label, auch ein sofort verworfenes, und das Start-Label. "
    "Die Zeile des gewählten k ist hervorgehoben."
)
df2 = pd.DataFrame(
    {
        "Gedächtnis": [r.name for r in ladder],
        "Bester Weg, Runde 1": [ev.fmt_walk(r.best_walk) for r in ladder],
        "Reduzierte Kosten": [ev.fmt_num(r.best_rc) for r in ladder],
        "Labels, Runde 1": [r.generated for r in ladder],
        "Verworfen": [r.discarded for r in ladder],
        "Verdrängt": [r.displaced for r in ladder],
        "Übrig": [r.alive for r in ladder],
        "Schranke": [ev.fmt_bound(r.bound) for r in ladder],
        "Runden": [r.rounds for r in ladder],
        "Labels gesamt (eine neue Spalte je Runde)": [r.labels for r in ladder],
        "Lücke zu elementar (%)": [r.gap for r in ladder],
    }
)
chosen = [i for i, r in enumerate(ladder) if r.memory == A.ng(int(hand_k))]
st.dataframe(df2.style.apply(lambda row: ["font-weight: bold; background-color: rgba(76,120,168,0.18)" if row.name in chosen else "" for _ in row], axis=1),
             hide_index=True, width="stretch", column_config={"Lücke zu elementar (%)": st.column_config.NumberColumn(format="%.2f %%")})
c1, c2 = st.columns(2)
c1.plotly_chart(build_ladder_gap_chart(ladder), width="stretch", key="ladder_gap")
c2.plotly_chart(build_ladder_labels_chart(ladder), width="stretch", key="ladder_labels")
kind, text = ev.verdict_round1(ladder)
getattr(st, kind)(text)

st.markdown("**Gegenprobe ohne Labels:** alle zulässigen Wege aufzählen (zulässig: die Gedächtnisregel gilt für den ganzen Weg, und Last, Zeitfenster und Horizont sind eingehalten) und den Master über alle diese Wege lösen.")
if st.button("Gegenprobe rechnen (einige Sekunden)", key="walkcheck_button"):
    st.session_state["walkcheck_done"] = True
if st.session_state.get("walkcheck_done"):
    with st.spinner("Zählt alle zulässigen Wege auf …"):
        checks = ev.hand_check_all_walks()
    st.dataframe(
        pd.DataFrame(
            {
                "Gedächtnis": [c.name for c in checks],
                "Zulässige Wege": [c.walks for c in checks],
                "Bester Wert der Aufzählung": [ev.fmt_num(c.best_value) for c in checks],
                "Schranke über alle Wege": [ev.fmt_bound(c.bound_all) for c in checks],
                "Gleich wie die Labels": ["ja" if c.same_best and c.same_bound else "nein" for c in checks],
            }
        ),
        hide_index=True, width="stretch",
    )
    kind, text = ev.verdict_walkcheck(checks)
    getattr(st, kind)(text)

st.markdown("---")

# --- Experiment 3 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 3: Regler k und Kundenzahl, live")
st.caption(
    f"Zufallsinstanz im Stil der Solomon-Instanzen mit {int(n)} Kunden, Fensterbreite {int(width)} und Zufalls-Seed {int(seed)}; ganze Spaltenerzeugung (Überdeckungs-Master) für jedes k bis {int(kmax)}. "
    "Die **Lücke** ist (Schranke beim größten k − Schranke bei k) / Schranke beim größten k. **Bezug ist das größte gewählte k, nicht die elementare Schranke:** bei 30 Kunden und Breite 100 "
    "kam die elementare Rechnung in der Messreihe von Experiment 5 in 3 von 6 Instanzen nicht zu Ende. Gezählt werden Labels, **nicht Sekunden**."
)
st.plotly_chart(build_live_chart(live, int(n), int(width)), width="stretch", key="live_chart")
st.dataframe(
    pd.DataFrame(
        {
            "Gedächtnis k": [r.k for r in live],
            "Schranke": [r.bound for r in live],
            "Lücke zum größten k (%)": [r.gap for r in live],
            "Erzeugte Labels": [r.labels for r in live],
            "Runden": [r.rounds for r in live],
            "Davon dominiert (%)": [100.0 * r.dominated / r.labels if r.labels else None for r in live],
            "Lauf": ["abgebrochen" if r.aborted else "fertig" for r in live],
        }
    ),
    hide_index=True, width="stretch",
    column_config={"Schranke": st.column_config.NumberColumn(format="%.4f"), "Lücke zum größten k (%)": st.column_config.NumberColumn(format="%.3f %%"),
                   "Davon dominiert (%)": st.column_config.NumberColumn(format="%.1f %%")},
)
kind, text = ev.verdict_live(live, int(n), int(width))
getattr(st, kind)(text)
st.caption("Eine Zufallsinstanz ist ein Einzelfall: Die Aussagen über viele Instanzen stehen in Experiment 5. "
           "Mehr als 2 Millionen erzeugte Labels in einem Aufruf des Preisproblems brechen den Lauf ab.")

st.markdown("---")

# --- Experiment 4 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 4: Kontrast k-Zyklen, und warum DSSR hier fehlt")
st.markdown(
    "**Die naheliegende Alternative zum Gedächtnis:** alle **kurzen Kreise verbieten** (k-Zyklen, Verbot aller Kreise mit höchstens K Kanten; K = 2 verbietet „i, j, i“). Die Dominanz der k-Zyklen in dieser Demo "
    "ist **meine** Regel (die Gedächtnisse aller Suffixe der letzten K Kunden müssen Teilmengen sein), **nicht die von Irnich und Villeneuve (2006)**; dass sie nichts verliert (gültig ist), folgt aus der Begründung im Expander „📐 Mathematische Formulierung“, ein Test gegen die Aufzählung bestätigt es für K = 2 und 3, und sie ist vermutlich schwächer. "
    "Gemessen ist deshalb mein Verfahren, nicht das der Literatur."
)
tab_live, tab_series = st.tabs(["Handbeispiel (live)", "24 Instanzen mit 30 Kunden (feste Messreihe)"])
with tab_live:
    st.caption("Welcher Weg ist bei welchem Gedächtnis erlaubt? Das Urteil ist eine Eigenschaft des ganzen Wegs. Die Regeln sind verschieden: Bei ng entscheidet die Nachbarschaft, bei k-Zyklen allein die Zahl der Kanten des Kreises.")
    cw = ev.contrast_walks()
    names_c = [name for name, _ in ev.CONTRAST_MEMORIES]
    df4 = pd.DataFrame({"Weg": [ev.fmt_walk(r["walk"]) for r in cw], **{name: ["erlaubt" if r[name] else "verboten" for r in cw] for name in names_c}})
    st.dataframe(df4.style.map(lambda v: C.CELL_OK if v == "erlaubt" else (C.CELL_BAD if v == "verboten" else ""), subset=names_c), hide_index=True, width="stretch")
    st.caption("Zeile 2 (5-3-5-1): Der Kreis 5-3-5 hat zwei Kanten, K = 2 verbietet ihn, ng k = 2 erlaubt ihn. Zeile 3 (7-6-1-7): Der Kreis hat drei Kanten, K = 3 verbietet ihn, ng erlaubt ihn bei k = 1, 2 und 3.")
    kind, text = ev.verdict_contrast_hand(ladder)
    getattr(st, kind)(text)
with tab_series:
    t = tables["knick"]
    st.caption(
        f"Feste Messreihe: {t[0]['instanzen']} Instanzen mit 30 Kunden und Fensterbreite 100 (je 12 zufällig und gruppiert, Zufalls-Seeds 0 bis 11), Überdeckungs-Master. **Bezug ist die Schranke von ng k = 8** "
        "(nicht die elementare). Lücke im Mittel (Maximum) über die Instanzen, Labels im Verhältnis zu ng k = 8 (Mittel der je Instanz gebildeten Verhältnisse). Läufe, die an einer Zeitgrenze der Messung abbrachen, sind nicht eingerechnet."
    )
    st.dataframe(
        pd.DataFrame(
            {
                "Gedächtnis": [_name(r["art"], r["k"]) for r in t],
                "Instanzen (fertig)": [r["instanzen"] for r in t],
                "Abgebrochen": [r["abgebrochen"] for r in t],
                "Lücke Mittel (%)": [r["luecke_mittel"] for r in t],
                "Lücke Maximum (%)": [r["luecke_max"] for r in t],
                "Labels / ng k = 8": [r["labels_verhaeltnis"] for r in t],
            }
        ),
        hide_index=True, width="stretch",
        column_config={"Lücke Mittel (%)": st.column_config.NumberColumn(format="%.3f %%"), "Lücke Maximum (%)": st.column_config.NumberColumn(format="%.3f %%"),
                       "Labels / ng k = 8": st.column_config.NumberColumn(format="%.2f")},
    )
    st.plotly_chart(build_contrast_chart(t), width="stretch", key="contrast_chart")
    pairs = tables["knick_pairs"]
    st.markdown("**Bei gleichem k:** k-Zyklen K gegen ng k = K an derselben Instanz (nur Instanzen, in denen beide fertig wurden)")
    st.dataframe(
        pd.DataFrame(
            {
                "Paar": [f"K = {p['K']} gegen ng k = {p['K']}" for p in pairs],
                "Instanzen": [p["paare"] for p in pairs],
                "Schranke der k-Zyklen höher": [p["hoeher"] for p in pairs],
                "gleich": [p["gleich"] for p in pairs],
                "tiefer": [p["tiefer"] for p in pairs],
                "Labels k-Zyklen / ng (Mittel)": [p["labels_verhaeltnis"] for p in pairs],
            }
        ),
        hide_index=True, width="stretch", column_config={"Labels k-Zyklen / ng (Mittel)": st.column_config.NumberColumn(format="%.2f")},
    )
    kind, text = ev.verdict_contrast_series(t, pairs, tables["knick_k2_ng5"], tables["knick_cluster"])
    getattr(st, kind)(text)
    st.caption("Dass die Dominanz der k-Zyklen **gültig** ist, folgt aus der Begründung im Expander „📐 Mathematische Formulierung“; der Test gegen die Aufzählung (Abschnitt Tests der README) bestätigt es für K = 2 und 3, beweist es aber nicht. "
               "Dass sie die **stärkste** mögliche ist, zeigt keines von beidem. "
               "Mit der Dominanz von Irnich und Villeneuve (2006), die hier nicht nachgebaut ist, könnte K = 2 weniger Labels brauchen und der Kontrast kleiner ausfallen.")

d = tables["dssr"]
st.markdown("### Absatz: DSSR gestrichen")
st.markdown(
    f"**Decremental State Space Relaxation (DSSR)** rüstet die Elementarität erst dort nach, wo ein Kreis auftritt: Die kritische Menge der Kunden, deren Besuch gemerkt wird, wächst Runde für Runde, "
    f"bis der beste Weg elementar ist. An {d['saetze']} festen Dualpreis-Sätzen (30 Kunden, Breite 100, je 12 zufällige und gruppierte Instanzen; Sätze aus Runde 2, Runde 4 und vom Ende der Spaltenerzeugung mit ng k = 5) "
    f"lieferte meine DSSR-Variante in {d['gleich_elem']} von {d['mit_elem']} Sätzen, in denen die elementare Rechnung fertig wurde, denselben Wert (in {d['saetze'] - d['mit_elem']} Sätzen war sie abgebrochen), brauchte aber im Mittel das **{ev.fmt_dec(d['faktor_ng5'], 1)}-Fache** der Labels von ng k = 5 "
    f"(das {ev.fmt_dec(d['faktor_ng8'], 1)}-Fache von ng k = 8). ng k = 5 verfehlt den besten Weg in {d['ng5_verfehlt']} von {d['saetze']} Fällen, in den gemessenen Runden 2 und 4 "
    f"({d['ng5_verfehlt_runde2']} bei Runde 2, {d['ng5_verfehlt_runde4']} bei Runde 4); **am Ende der Spaltenerzeugung in {d['ng5_verfehlt_ende']} von {d['saetze_ende']}**, und dort kostet DSSR das "
    f"{ev.fmt_dec(d['faktor_ng5_ende'], 1)}-Fache von ng k = 5. Andere Runden und andere DSSR-Fassungen sind nicht gemessen; ein eigenes Verfahren zeigt die Demo deshalb nicht. **Vorbehalte:** gemessen pro Aufruf des Preisproblems, nicht in der ganzen Schleife der "
    "Spaltenerzeugung (dort könnte die kritische Menge von Runde zu Runde wiederverwendet werden, das ist nicht gemessen); nur 30 Kunden; eigene Variante nach dem Abstract von Righini und Salani (2008), nicht nach dem Volltext. "
    "Diese Reihe ist in dieser Demo **nicht neu gerechnet**, sie stammt aus der Messdatei der Planung; nur die Zählungen daraus sind hier aus den Zeilen berechnet."
)

st.markdown("---")

# --- Experiment 5 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 5: Der Knick und die Breite, feste Messreihen")
st.caption(
    "Fensterbreite und Kundenzahl entscheiden, wie viel Elementarität zählt. Alle Reihen: eigene Zufallsinstanzen im Stil der Solomon-Instanzen (nicht die Originale), Überdeckungs-Master, "
    "Zufalls-Seeds ab 0, Messgröße Labels. **Die Zeilen stammen aus den Messdateien der Planung; die Demo hat sie mit ihrem eigenen Kern nachgerechnet** (Umfang: Abschnitt „Nachrechnung“ unten und README)."
)
tab_a, tab_b, tab_c = st.tabs(["30 Kunden, Bezug elementar", "50 und 100 Kunden, Bezug k = 16", "10 bis 25 Kunden, k = 5 gegen elementar"])

LUECKE_CFG = {"Lücke Mittel (%)": st.column_config.NumberColumn(format="%.3f %%"), "Lücke Maximum (%)": st.column_config.NumberColumn(format="%.3f %%")}

with tab_a:
    ta = tables["elementar"][30]
    st.markdown("**30 Kunden, zufällig verteilt, 6 Instanzen je Fensterbreite (Zufalls-Seeds 0 bis 5):** Lücke zur **elementaren** Schranke. Eine Instanz zählt nur, wenn ihr elementarer Lauf fertig wurde; "
                "bei Breite 100 sind das **3 von 6** (die anderen brachen in der Messung an der Zeitgrenze ab), die Zufalls-Seeds 0, 1 und 5. Die Mittel der Tabelle gelten nur für diese 3 Instanzen; mit allen 6 liegt die mittlere Lücke bei k = 1 bei 3,33 % "
                "(Maximum 6,80 %; gemessen in kreise-im-pricing-demo, hier nicht neu gerechnet).")
    st.dataframe(
        pd.DataFrame(
            {
                "Fensterbreite": [r["breite"] for r in ta],
                "Gedächtnis": ["elementar (k = 30)" if r["elementar"] else f"ng k = {r['k']}" for r in ta],
                "Läufe fertig": [r["laeufe"] for r in ta],
                "Instanzen mit elementarem Bezug": [r["mit_bezug"] for r in ta],
                "Lücke Mittel (%)": [r["luecke_mittel"] for r in ta],
                "Lücke Maximum (%)": [r["luecke_max"] for r in ta],
                "Instanzen mit Lücke 0": [r["luecke_null"] for r in ta],
                "Labels (Median)": [r["labels_median"] for r in ta],
            }
        ),
        hide_index=True, width="stretch", column_config={**LUECKE_CFG, "Labels (Median)": st.column_config.NumberColumn(format="%d")},
    )
    kind, text = ev.verdict_elementar(ta, 30)
    getattr(st, kind)(text)
    tk = tables["knick"]
    _g = {r["k"]: r["luecke_mittel"] for r in tk if r["art"] == "ng"}
    st.markdown(f"**Feinerer Knick, 24 Instanzen, Bezug ng k = 8:** Die mittlere Lücke sinkt von {ev.fmt_dec(_g[1], 3)} % bei k = 1 auf {ev.fmt_dec(_g[2], 3)} % bei k = 2 und weiter auf "
                f"{ev.fmt_dec(_g[3], 3)} %, {ev.fmt_dec(_g[4], 3)} % und {ev.fmt_dec(_g[5], 3)} % bei k = 3, 4 und 5.")
    st.dataframe(
        pd.DataFrame(
            {
                "Gedächtnis": [_name(r["art"], r["k"]) for r in tk if r["art"] == "ng"],
                "Lücke Mittel (%)": [r["luecke_mittel"] for r in tk if r["art"] == "ng"],
                "Lücke Maximum (%)": [r["luecke_max"] for r in tk if r["art"] == "ng"],
                "Labels / ng k = 8": [r["labels_verhaeltnis"] for r in tk if r["art"] == "ng"],
            }
        ),
        hide_index=True, width="stretch", column_config={**LUECKE_CFG, "Labels / ng k = 8": st.column_config.NumberColumn(format="%.2f")},
    )
    kind, text = ev.verdict_knick(ev.load_rows("knick_n30"))
    getattr(st, kind)(text)

with tab_b:
    ts = tables["skal"]
    el = tables["skal_elementar"]
    _f20 = {x["typ"]: x["faktor_16_zu_5"] for x in ts if (x["n"], x["breite"], x["k"]) == (100, 20, 16)}
    st.markdown(
        f"**Bezug: k = 16, nicht elementar** (bei n ≥ 50 ist die elementare Rechnung in {el['abgebrochen']} von {el['laeufe']} Läufen abgebrochen; k = 16 ist selbst nur eine ng-Relaxation). "
        "12 Instanzen je Zelle (Zufalls-Seeds 0 bis 11), zufällig verteilt und gruppiert. Lücke zu k = 16 im Mittel (Maximum) in Prozent:"
    )
    cells = ev.skalierung_cells(ev.load_rows("skalierung"))
    pivot = []
    for typ, nn, ww in cells:
        row = {"Zelle": f"n = {nn}, Breite {ww}, {ev.TYP_NAMES[typ]}"}
        for k in ev.SKALIERUNG_KS[:-1]:
            r = next(x for x in ts if (x["typ"], x["n"], x["breite"], x["k"]) == (typ, nn, ww, k))
            row[f"k = {k}"] = f"{ev.fmt_dec(r['luecke_mittel'], 2)} ({ev.fmt_dec(r['luecke_max'], 2)})"
        r16 = next(x for x in ts if (x["typ"], x["n"], x["breite"], x["k"]) == (typ, nn, ww, 16))
        r5 = next(x for x in ts if (x["typ"], x["n"], x["breite"], x["k"]) == (typ, nn, ww, 5))
        row["Labels k = 16 / k = 5 (Median)"] = r16["faktor_16_zu_5"]
        row["Dominiert k = 5 / k = 16 (%)"] = f"{ev.fmt_dec(r5['dominiert_anteil'], 1)} / {ev.fmt_dec(r16['dominiert_anteil'], 1)}"
        pivot.append(row)
    st.dataframe(pd.DataFrame(pivot), hide_index=True, width="stretch", column_config={"Labels k = 16 / k = 5 (Median)": st.column_config.NumberColumn(format="%.2f")})
    st.plotly_chart(build_knick_chart(ts), width="stretch", key="knick_chart")
    kind, text = ev.verdict_skalierung(ts)
    getattr(st, kind)(text)
    st.caption("Zeile „n = 100, Breite 20“: Die Lücke ist schon bei k = 1 gleich 0 (24 von 24 Instanzen). Diese Zelle sagt deshalb nichts über die Wirkung von k auf die Schranke (Deutung, nicht gemessen: "
               "Die Fenster sind so eng, dass Kreise kaum möglich sind). Die Kosten wachsen dort trotzdem mit k: k = 16 braucht im Median das "
               f"{ev.fmt_dec(_f20['cluster'], 2)}-Fache (gruppiert) bzw. {ev.fmt_dec(_f20['zufall'], 2)}-Fache (zufällig) der Labels von k = 5. „Dominiert“ ist der Anteil der erzeugten Labels, die gestrichen wurden (über die 12 Läufe zusammengezählt).")

with tab_c:
    st.markdown("**k = 5 gegen elementar bei kleineren Kundenzahlen** (zufällig verteilt, 6 Instanzen je Zelle, alle elementaren Läufe fertig; Zufalls-Seeds 0 bis 5):")
    rows_c = []
    for nn in (10, 15, 20, 25):
        for r in tables["elementar"][nn]:
            if r["k"] == 5 or r["k"] == 1:
                rows_c.append({"Kunden n": nn, "Fensterbreite": r["breite"], "Gedächtnis k": r["k"], "Instanzen mit Lücke": r["mit_bezug"] - r["luecke_null"], "Instanzen": r["mit_bezug"],
                               "Lücke Mittel (%)": r["luecke_mittel"], "Lücke Maximum (%)": r["luecke_max"]})
    st.dataframe(pd.DataFrame(rows_c), hide_index=True, width="stretch", column_config=LUECKE_CFG)
    kind, text = ev.verdict_small_n(tables["elementar"])
    getattr(st, kind)(text)

st.markdown("**Nachrechnung mit dem Kern dieser Demo**")
chk = tables["check"]
if chk:
    st.dataframe(
        pd.DataFrame(
            {
                "Messreihe": ["24 Instanzen, n = 30 (Experiment 4 und 5)", "n = 10 bis 30, Bezug elementar", "n = 50 und 100, Bezug k = 16"],
                "Zeilen": [chk[s]["zeilen"] for s in ("knick", "elementar", "skalierung")],
                "In der Messung abgebrochen": [chk[s]["in_vormessung_abgebrochen"] for s in ("knick", "elementar", "skalierung")],
                "Neu gerechnet": [chk[s]["neu_gerechnet"] for s in ("knick", "elementar", "skalierung")],
                "Schranke gleich": [chk[s]["schranke_gleich"] for s in ("knick", "elementar", "skalierung")],
                "Labels gleich": [chk[s]["labels_gleich"] for s in ("knick", "elementar", "skalierung")],
            }
        ),
        hide_index=True, width="stretch",
    )
    kind, text = ev.verdict_check(chk)
    getattr(st, kind)(text)
else:
    st.info("Die Nachrechnung liegt nicht vor (data/nachrechnung.json fehlt); die Zeilen der Messreihen stammen dann nur aus den Messdateien der Planung.")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
_el30 = {(r["breite"], r["k"]): r for r in tables["elementar"][30]}
_knick = {(r["art"], r["k"]): r for r in tables["knick"]}
_skal = {(r["typ"], r["n"], r["breite"], r["k"]): r for r in tables["skal"]}
st.markdown(
    f"""
| Annahme | Was passiert, wenn sie nicht gilt | Belegt durch |
|---|---|---|
| **Bezug ist das größte k, nicht die elementare Schranke** (ab 50 Kunden, bei 30 Kunden und Breite 100 teilweise) | Die Lücke zu k = 16 sagt nichts darüber, wie weit k = 16 selbst unter der elementaren Schranke liegt: Die elementare Rechnung ist bei 50 und 100 Kunden nur in {tables['skal_elementar']['fertig']} von {tables['skal_elementar']['laeufe']} Läufen fertig geworden. | Experiment 5 |
| **Fensterbreite** | Bei Breite 20 und 100 Kunden ist die Lücke schon bei k = 1 gleich 0. Bei Breite 100 liegt k = 1 im Mittel {ev.fmt_dec(_el30[(100, 1)]['luecke_mittel'], 2)} % (30 Kunden, Bezug elementar, {_el30[(100, 1)]['mit_bezug']} Instanzen; mit allen 6 Instanzen 3,33 % nach kreise-im-pricing-demo), {ev.fmt_dec(_knick[('ng', 1)]['luecke_mittel'], 2)} % (30 Kunden, Bezug k = 8, 24 Instanzen) und {ev.fmt_dec(_skal[('cluster', 50, 100, 1)]['luecke_mittel'], 2)} bzw. {ev.fmt_dec(_skal[('zufall', 50, 100, 1)]['luecke_mittel'], 2)} % (50 Kunden, Bezug k = 16, gruppiert bzw. zufällig) unter dem Bezug: „k = 5 reicht“ hängt an der Breite. | Experiment 5 |
| **Nachbarschaft nach Entfernung** | Eine andere Wahl der Nachbarn (nach Zeitfenster, nach Dualpreis) ist nicht gemessen. | nicht gemessen |
| **Kosten = Entfernung = Fahrzeit** (Dreiecksungleichung gilt) | Bei anderen Kosten kann sich die Rangfolge der Nachbarn und damit die Schärfe von k ändern; nicht gemessen. | nicht gemessen |
| **Überdeckungs-Master, Dualpreise aus der Spaltenerzeugung** | Mit Partitionierung oder in einem Verzweigungsbaum (andere Dualpreise) ist nicht gemessen. | nicht gemessen |
| **6 bis 12 Instanzen je Zelle** | Mittel und Maxima über so wenige Instanzen sind keine Konfidenzaussage. | Experiment 5 |
| **Meine Dominanz für k-Zyklen** | Mit der Dominanz aus der Literatur könnten die k-Zyklen weniger Labels brauchen. | Experiment 4 |
| **DSSR nur pro Aufruf gemessen, nur 30 Kunden** | In der Schleife der Spaltenerzeugung (Wiederverwendung der kritischen Menge) ist DSSR nicht gemessen. | Experiment 4 |
| **Gezählt werden Labels** | Sekunden dieser Python-Fassung sind kein Thema; die Zahl der Dominanzprüfungen je Label ist hier nicht gezählt und kann mit der Größe des Gedächtnisses wachsen (die elementar-pricing-demo zählt sie). | alle Experimente |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    # erklaerseite:lesehilfe:start (erzeugt von tools/set_demo_explainer.py (Website-Repo) aus tools/content/explainers/ng-routen-erklaert.json, nicht von Hand ändern)
    st.markdown(
        r"""
**Lesehilfe.** Gegeben sind ein Depot $0$ und Kunden $1,\dots,n$ mit Entfernungen $d_{ij}$ (gleich Fahrzeit und Kosten), Lasten $q_j$, Zeitfenstern $[e_j, l_j]$ und Dualpreisen $\pi_j$. Gesucht ist ein Weg ab und bis zum Depot mit den kleinsten reduzierten Kosten, auf dem ein Kunde mehrmals vorkommen darf, soweit das Gedächtnis es erlaubt. Die Spaltenerzeugung wiederholt diese Suche mit neuen Dualpreisen; ihre Schlusszahl ist die Schranke $z(k)$.

| Symbol | Bedeutung |
|---|---|
| $i, j$ | Knoten; $0$ ist das Depot, $1,\dots,n$ sind Kunden ($n$: Zahl der Kunden) |
| $r$, $m$ | ein Weg $r = (0, j_1, \dots, j_m, 0)$ mit $m$ Besuchen |
| $a, b, t$ | Stellen (Positionen) im Weg, $a < b$; $t$ liegt zwischen $a$ und $b$ |
| $d_{ij}$ | Entfernung von $i$ nach $j$ |
| $\pi_j$ | Dualpreis des Kunden $j$ ($\pi_0 = 0$) |
| $q_j$, $Q$ | Last des Kunden $j$; Kapazität |
| $e_j$, $l_j$ | frühester und spätester Beginn der Bedienung bei $j$ |
| $s$, $H$ | Bedienzeit je Kunde; Horizont (späteste Rückkehr ins Depot) |
| $N_j$ | Nachbarschaft von $j$: $j$ und die $k-1$ nächsten Kunden |
| $M$ | Gedächtnis eines Labels (Menge von Kunden) |
| $(T, C, R, M)$ | Label: Zeit, reduzierte Kosten, verbrauchte Last, Gedächtnis |
| $L_1, L_2$ | zwei Labels am selben Kunden (Dominanz) |
| $\beta_{jr}$, $c_r$ | Zahl der Besuche von $j$ im Weg $r$; Länge von $r$ (Überdeckungs-Master) |
| $z(k)$ | Schranke der Spaltenerzeugung mit ng-Routen der Größe $k$ |
| $K$, $S_1,\dots,S_K$ | k-Zyklen: Kreise mit höchstens $K$ Kanten sind verboten; $S_i$ ist die Menge der letzten $i$ Kunden |

[Schritt für Schritt erklärt, mit Herleitung und Literatur](https://sebastianhanisch.net/ng-routen-erklaert.html#fachleute)
        """
    )
    # erklaerseite:lesehilfe:end
    st.markdown(
        r"""
**Reduzierte Kosten** eines Wegs $r = (0, j_1, \dots, j_m, 0)$:

$$\bar c(r) = \sum_{t=0}^{m} d_{j_t j_{t+1}} - \sum_{t=1}^{m} \pi_{j_t}$$

**Nachbarschaft** (Gleichstand: kleinere Nummer zuerst) und **Gedächtnis nach dem Besuch** von $j$:

$$N_j = \{j\} \cup \{\text{die } k-1 \text{ nächsten Kunden von } j\}, \qquad M' = (M \cap N_j) \cup \{j\}$$

Ein Kunde $j$ darf als Nächster nur gewählt werden, wenn $j \notin M$ gilt; wegen $i \in M$ nach jedem Besuch von $i$ ist „$i$ direkt nach $i$“ immer verboten.

**Fortsetzung** eines Labels $(T, C, R, M)$ am Knoten $i$ zum Kunden $j \notin M$ (mit $s\,[i \ne 0]$: im Depot entfällt die Bedienzeit):

$$T' = \max\bigl(e_j,\; T + s\,[i \ne 0] + d_{ij}\bigr), \quad C' = C + d_{ij} - \pi_j, \quad R' = R + q_j$$

zulässig, wenn $T + s\,[i \ne 0] + d_{ij} \le l_j$ und $R' \le Q$ gelten; zurück ins Depot geht es, wenn $T + s + d_{i0} \le H$.

**Dominanz** (am selben Kunden):

$$L_1 \preceq L_2 \iff C_1 \le C_2, \quad T_1 \le T_2, \quad R_1 \le R_2, \quad M_1 \subseteq M_2$$

**Warum sie nichts verliert:** Aus $M_1 \subseteq M_2$ folgt $(M_1 \cap N_j) \cup \{j\} \subseteq (M_2 \cap N_j) \cup \{j\}$ für jede Fortsetzung $j$. Jede Fortsetzung von $L_2$ ist daher auch für $L_1$ zulässig
(früher oder gleich spät ankommen hält Fenster und Horizont ein, weil Warten erlaubt ist; weniger oder gleich viel Last) und kostet nicht mehr.

**Dieselbe Regel als Eigenschaft des ganzen Wegs:** Ein Weg ist erlaubt, wenn für jede Wiederholung eines Kunden $j$ (frühere Stelle $a$, spätere Stelle $b$) eine Stelle $t$ mit $a < t < b$ und $j \notin N_{j_t}$ existiert.
Diese Fassung benutzt die Aufzählung in den Tests, ohne Labels.

**Spaltenerzeugung.** Der Master ist die Überdeckung $\min \sum_r c_r x_r$ unter $\sum_r \beta_{jr} x_r \ge 1$ für alle Kunden $j$, $x \ge 0$ ($\beta_{jr}$ = Zahl der Besuche von $j$ im Weg $r$, $c_r$ die Länge).
Das Preisproblem sucht mit den Dualpreisen $\pi$ den Weg mit den kleinsten $\bar c(r)$ unter der Gedächtnisregel; die Rechnung endet, wenn kein Weg negative reduzierte Kosten hat. Die Wegmengen der Größen $k$ liegen
ineinander ($k$ Nachbarn $\subseteq$ $k+1$ Nachbarn, $k = n$ ist elementar), deshalb gilt

$$z(1) \le z(2) \le \dots \le z(n) = z_{\text{elementar}}$$

**Lücke** gegen eine Bezugsschranke $z_{\text{ref}}$: $\;(z_{\text{ref}} - z(k)) / z_{\text{ref}}$.

**k-Zyklen** (Kontrast): Ein Weg ist erlaubt, wenn für jede Wiederholung eines Kunden, $j_a = j_b$ mit $a < b$ (nur Kunden, nicht das Depot), gilt $b - a > K$. Als Gedächtnis halten die Labels die Mengen $S_1, \dots, S_K$ der letzten $1, \dots, K$ Kunden; die Dominanz
verlangt, dass jede dieser Mengen von $L_1$ eine Teilmenge der von $L_2$ ist (meine Regel).

**Warum diese Dominanz nichts verliert:** Nach dem Besuch von $j$ sind die neuen Mengen $S'_1 = \{j\}$ und $S'_m = \{j\} \cup S_{m-1}$ für $m = 2, \dots, K$; ein Kunde $j$ ist verboten, wenn er in $S_K$ steht, also genau dann, wenn er unter den letzten $K$ Kunden war.
Gilt $S_m^{(1)} \subseteq S_m^{(2)}$ für alle $m$, so ist jede Fortsetzung $j \notin S_K^{(2)}$ von $L_2$ auch für $L_1$ erlaubt, und die neuen Mengen $\{j\} \cup S_{m-1}^{(1)} \subseteq \{j\} \cup S_{m-1}^{(2)}$ liegen wieder ineinander.
Durch Wiederholen dieses Schritts ist jede Fortsetzung von $L_2$ auch eine von $L_1$, mit Zeit, Last und Kosten wie bei der ng-Dominanz. Am selben Kunden ist $S_1$ ohnehin gleich; die Demo vergleicht deshalb $S_2, \dots, S_K$.

**Literatur** (Prüfstand: Autoren, Zeitschrift und Jahr per Abstract und Suchtreffer geprüft; die Volltexte sind außer dem Hinweis auf den Ursprung der ng-Routen in Pessoa u. a. nicht gelesen, die Demo übernimmt keine Zahl daraus):
- Baldacci, Mingozzi, Roberti (2011): New route relaxation and pricing strategies for the vehicle routing problem, Operations Research 59(5):1269–1283 (ng-Routen).
- Irnich, Villeneuve (2006): INFORMS Journal on Computing 18(3):391–406 (Verbot von Kreisen mit höchstens k Kanten, eigene Dominanzregel; hier nicht nachgebaut).
- Righini, Salani (2008): New dynamic programming algorithms for the resource constrained elementary shortest path problem, Networks 51(3):155–170 (DSSR; hier nur nach dem Abstract nachgebaut).
- Christofides, Mingozzi, Toth (1981): State-space relaxation procedures for the computation of bounds to routing problems, Networks 11(2):145–164 (Vorläufer).
- Pessoa, Sadykov, Uchoa, Vanderbeck (2020): A generic exact solver for vehicle routing and related problems, Mathematical Programming 183:483–523 (nennt Baldacci u. a. als Ursprung der ng-Pfade).
        """
    )

st.markdown("---")

with st.expander("⚠️ Annahmen, Grenzen und bekannte Probleme"):
    st.markdown(C.ASSUMPTIONS_MARKDOWN)

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Ressourcenwege: von der Grenze zur Verfahrenswahl](https://sebastianhanisch.net/konzepte-ressourcenwege.html)."
)
