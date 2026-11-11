"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import ngr_algorithm as A
import ngr_constants as C
import ngr_evaluation as ev


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360, legend_below=True):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="rgba(0,0,0,0)",
                      legend=dict(orientation="h", y=-0.25) if legend_below else {})
    return lock_axes(fig)


def _manhattan_path(points, seq):
    """Linienzug einer Folge von Knoten auf dem Gitter: erst waagerecht, dann senkrecht (der Abstand des Handbeispiels ist der Manhattan-Abstand)."""
    xs, ys = [], []
    for a, b in zip(seq, seq[1:]):
        (x1, y1), (x2, y2) = points[a], points[b]
        xs += [x1, x2, x2]
        ys += [y1, y1, y2]
    return xs, ys


def build_hand_map(inst, k, walk, analysis):
    """Die Kunden des Handbeispiels auf dem Gitter mit dem gewählten Weg und den Nachbarschaften NG(j) der Kunden auf dem Weg (Pfeile von j zu den k − 1 nächsten
    Kunden). Grauer Pfeil: gegenseitige Nachbarn; oranger Pfeil: j hat den Kunden als Nachbarn, er j aber nicht (die Nachbarschaft ist nicht symmetrisch).
    Der Weg ist durchgezogen bis vor den ersten verbotenen Besuch; die verbotene Fahrt ist rot gestrichelt."""
    masks = A.ng_masks(inst, k)
    fig = go.Figure()
    cut = len(walk) if analysis.allowed else analysis.first_forbidden - 1
    seq_ok = (0,) + tuple(walk[:cut])
    if len(seq_ok) > 1:
        xs, ys = _manhattan_path(inst.points, seq_ok + ((0,) if analysis.allowed else ()))
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=C.COLOR_OK, width=6), opacity=0.45, name="Weg", hoverinfo="skip"))
    if not analysis.allowed:
        a, b = (seq_ok[-1], walk[cut])
        xs, ys = _manhattan_path(inst.points, (a, b))
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=C.COLOR_BAD, width=4, dash="dash"), name="verbotene Fahrt", hoverinfo="skip"))
    shown = sorted(set(walk[: cut + (0 if analysis.allowed else 1)]))
    for j in shown:
        for i in range(1, inst.n + 1):
            if i == j or not (masks[j] >> i) & 1:
                continue
            mutual = bool((masks[i] >> j) & 1)
            (x1, y1), (x2, y2) = inst.points[j], inst.points[i]
            fig.add_annotation(x=x2, y=y2, ax=x1, ay=y1, xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=2, arrowsize=1.1, arrowwidth=1.6,
                               arrowcolor="rgba(120,120,120,0.8)" if mutual else C.COLOR_LINE2, standoff=9, startstandoff=9, text="")
    cust = list(range(1, inst.n + 1))
    hover = [f"Kunde {i}: Last {inst.demand[i]}, Fenster [{inst.ready[i]}, {inst.due[i]}]" for i in cust]
    fig.add_trace(go.Scatter(x=[inst.points[i][0] for i in cust], y=[inst.points[i][1] for i in cust], mode="markers+text", text=[str(i) for i in cust],
                             textposition="top center", marker=dict(size=16, color=C.COLOR_LINE), textfont=dict(size=13), name="Kunden", hovertext=hover,
                             hovertemplate="%{hovertext}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[inst.points[0][0]], y=[inst.points[0][1]], mode="markers+text", text=["Depot"], textposition="bottom center",
                             marker=dict(size=16, color="black", symbol="square"), name="Depot", hovertemplate="Depot<extra></extra>"))
    fig.update_xaxes(range=[-4.5, 4.5], title_text="Gitter, waagerecht", dtick=1)
    fig.update_yaxes(range=[-3.5, 4.5], title_text="Gitter, senkrecht", dtick=1)
    return _base(fig, height=430)


def build_ladder_gap_chart(rows):
    """Lücke der Schranke zur elementaren Schranke je Gedächtnis (Handbeispiel)."""
    names = [r.name.replace(" (elementar)", "") for r in rows]
    colors = [C.COLOR_LINE if r.memory.kind == "ng" else C.COLOR_LINE2 for r in rows]
    fig = go.Figure(go.Bar(x=names, y=[r.gap for r in rows], marker_color=colors, hovertemplate="%{x}: Lücke %{y:.2f} %<extra></extra>"))
    fig.update_yaxes(title_text="Lücke zur elementaren Schranke (%)", range=[0, 9])
    fig.update_xaxes(tickangle=-35)
    return _base(fig, height=330)


def build_ladder_labels_chart(rows):
    """Erzeugte Labels der ganzen Spaltenerzeugung je Gedächtnis (Handbeispiel)."""
    names = [r.name.replace(" (elementar)", "") for r in rows]
    colors = [C.COLOR_LINE if r.memory.kind == "ng" else C.COLOR_LINE2 for r in rows]
    fig = go.Figure(go.Bar(x=names, y=[r.labels for r in rows], marker_color=colors, hovertemplate="%{x}: %{y} Labels<extra></extra>"))
    fig.update_yaxes(title_text="erzeugte Labels (ganze Spaltenerzeugung)", range=[0, 450])
    fig.update_xaxes(tickangle=-35)
    return _base(fig, height=330)


def build_live_chart(rows, n, width):
    """Lücke zum größten k (Linie, links) und erzeugte Labels je k (Säulen) für die Zufallsinstanz."""
    ks = [f"k = {r.k}" for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=ks, y=[r.labels for r in rows], name="erzeugte Labels", marker_color="rgba(76,120,168,0.35)", yaxis="y2",
                         hovertemplate="%{x}: %{y} Labels<extra></extra>"))
    fig.add_trace(go.Scatter(x=ks, y=[r.gap for r in rows], mode="lines+markers", name="Lücke zum größten k (%)", line=dict(color=C.COLOR_BAD, width=3),
                             hovertemplate="%{x}: Lücke %{y:.3f} %<extra></extra>", connectgaps=False))
    top = max([r.gap for r in rows if r.gap is not None] + [1.0])
    fig.update_layout(yaxis=dict(title_text="Lücke zum größten k (%)", range=[0, top * 1.15], fixedrange=True),
                      yaxis2=dict(title_text="erzeugte Labels", overlaying="y", side="right", rangemode="tozero", showgrid=False, fixedrange=True))
    fig.update_xaxes(title_text=f"Gedächtnis k ({n} Kunden, Fensterbreite {width})")
    return _base(fig, height=360)


def build_contrast_chart(table):
    """Lücke zur Schranke von ng k = 8 gegen erzeugte Labels (im Verhältnis zu ng k = 8): ng-Stufen k = 1 bis 5 und k-Zyklen K = 2 bis 4 (24 Instanzen, n = 30).
    Beschriftungen der Punkte als Annotationen (nicht als Text-Spur)."""
    fig = go.Figure()
    ng_rows = [r for r in table if r["art"] == "ng" and r["luecke_mittel"] is not None]
    kc_rows = [r for r in table if r["art"] == "kcyc" and r["luecke_mittel"] is not None]
    ng_x, ng_y = [r["labels_verhaeltnis"] for r in ng_rows] + [1.0], [r["luecke_mittel"] for r in ng_rows] + [0.0]
    kc_x, kc_y = [r["labels_verhaeltnis"] for r in kc_rows], [max(r["luecke_mittel"], 0.0) for r in kc_rows]
    fig.add_trace(go.Scatter(x=ng_x, y=ng_y, mode="lines+markers", name="ng-Routen (k = 1 bis 5, Bezug k = 8)", line=dict(color=C.COLOR_LINE, width=3), marker=dict(size=10),
                             customdata=[f"k = {r['k']}" for r in ng_rows] + ["k = 8"], hovertemplate="%{customdata}: %{x:.2f}-fache Labels, Lücke %{y:.3f} %<extra></extra>"))
    fig.add_trace(go.Scatter(x=kc_x, y=kc_y, mode="lines+markers", name="k-Zyklen (K = 2 bis 4)", line=dict(color=C.COLOR_LINE2, width=3, dash="dash"),
                             marker=dict(size=10, symbol="diamond"), customdata=[f"K = {r['k']}" for r in kc_rows],
                             hovertemplate="%{customdata}: %{x:.2f}-fache Labels, Lücke %{y:.3f} %<extra></extra>"))
    for x, y, label, color in ([(x, y, f"k={r['k']}", C.COLOR_LINE) for x, y, r in zip(ng_x, ng_y, ng_rows)] + [(1.0, 0.0, "k=8", C.COLOR_LINE)]
                               + [(x, y, f"K={r['k']}", C.COLOR_LINE2) for x, y, r in zip(kc_x, kc_y, kc_rows)]):
        fig.add_annotation(x=x, y=y, text=label, showarrow=False, xanchor="left", yanchor="bottom", xshift=6, yshift=4, font=dict(color=color, size=12))
    fig.update_xaxes(title_text="erzeugte Labels im Verhältnis zu ng k = 8 (Mittel über die Instanzen)", range=[0, 4.2])
    fig.update_yaxes(title_text="Lücke zur Schranke von ng k = 8 (%, Mittel)", range=[-0.2, 4.2])
    return _base(fig, height=380)


def build_knick_chart(rows):
    """Lücke gegen k für die Zellen der Messreihe mit n = 50 und 100 (Zelle = Art, n, Breite), Mittel über 12 Instanzen; Bezug k = 16."""
    fig = go.Figure()
    cells = sorted({(r["typ"], r["n"], r["breite"]) for r in rows}, key=lambda c: (c[1], c[2], c[0]))
    for typ, n, width in cells:
        sel = [r for r in rows if (r["typ"], r["n"], r["breite"]) == (typ, n, width) and r["luecke_mittel"] is not None]
        flat = n == 100 and width == 20
        fig.add_trace(go.Scatter(x=[r["k"] for r in sel], y=[r["luecke_mittel"] for r in sel], mode="lines+markers",
                                 name=f"n = {n}, Breite {width}, {ev.TYP_NAMES[typ]}", line=dict(width=2, dash="dot" if flat else "solid"),
                                 hovertemplate=f"n = {n}, Breite {width}, {ev.TYP_NAMES[typ]}, k = %{{x}}: %{{y:.3f}} %<extra></extra>"))
    fig.update_xaxes(title_text="Gedächtnis k", tickvals=list(ev.SKALIERUNG_KS), range=[0.5, 16.5])
    fig.update_yaxes(title_text="Lücke zu k = 16 (%, Mittel über 12 Instanzen)", range=[0, 3.6])
    fig.update_layout(legend=dict(orientation="h", y=-0.35, font=dict(size=11)))
    return _base(fig, height=470, legend_below=False)
