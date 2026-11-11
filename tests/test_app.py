"""End-to-end Smoke-Test via Streamlits offiziellem AppTest-Framework: lädt app.py mit den Standardeinstellungen, klickt jeden Preset-Button, fährt jeden Regler an seine Grenzen,
prüft Permalink (auch mit ungültigen Werten), die erwartete Verdikt-Zeile je Preset und die Texte der Expander. Expander werden nie per Index angesprochen (DEMO-PLAYBOOK §2)."""

import os
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest
from test_presets import EXPECTED

import ngr_constants as C
import ngr_presets as P

APP_PATH = str(Path(__file__).resolve().parent.parent / "app.py")
README = (Path(__file__).resolve().parent.parent / "README.md").read_text(encoding="utf-8")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))  # unter Last (parallele Läufe) reichen 180 s nicht immer; Umgebungsvariable zum Anpassen
AUTOPLAY_MARKER = "▶"  # Auto-Play-Buttons (Animation mit sleep) im Smoke-Test auslassen


def _fresh_app() -> AppTest:
    at = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT)
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _messages(at):
    """Alle Verdikt-Texte (success, info, warning, error) der Seite."""
    return [m.value for kind in (at.success, at.info, at.warning, at.error) for m in kind]


def test_app_loads_without_exception():
    at = _fresh_app()
    assert at.title[0].value.startswith("🧩 ng-Routen")


def test_every_button_click_does_not_raise():
    labels = [b.label for b in _fresh_app().button]
    assert labels, "keine Buttons gefunden"
    for index, label in enumerate(labels):
        if AUTOPLAY_MARKER in label:
            continue
        at = _fresh_app()
        at.button[index].click().run(timeout=TIMEOUT)
        assert not at.exception, (label, [str(e) for e in at.exception])


def test_every_slider_at_its_min_and_max_does_not_raise():
    labels = [s.label for s in _fresh_app().slider]
    assert labels, "keine Slider gefunden"
    for index, label in enumerate(labels):
        for edge in ("min", "max"):
            at = _fresh_app()
            slider = at.slider[index]
            value = slider.min if edge == "min" else slider.max
            if isinstance(slider.value, int):
                value = int(value)
            slider.set_value(value).run(timeout=TIMEOUT)
            assert not at.exception, (label, edge, [str(e) for e in at.exception])


def test_every_radio_option_and_all_minima_and_all_maxima_do_not_raise():
    for radio_key, options in (("width_radio", C.WIDTH_OPTIONS), ("kmax_radio", C.KMAX_OPTIONS)):
        for option in options:
            at = _fresh_app()
            at.sidebar.radio(key=radio_key).set_value(option).run(timeout=TIMEOUT)
            assert not at.exception, (radio_key, option, [str(e) for e in at.exception])
    for values in ({"k_slider": 1, "n_slider": C.N_MIN, "width_radio": min(C.WIDTH_OPTIONS), "kmax_radio": min(C.KMAX_OPTIONS), "seed_input": 0, "walk_text": "1"},
                   {"k_slider": 7, "n_slider": C.N_MAX, "width_radio": max(C.WIDTH_OPTIONS), "kmax_radio": max(C.KMAX_OPTIONS), "seed_input": C.SEED_MAX, "walk_text": "-".join(["7", "6"] * 6)}):
        at = _fresh_app()
        at.sidebar.slider(key="k_slider").set_value(values["k_slider"])
        at.sidebar.slider(key="n_slider").set_value(values["n_slider"])
        at.sidebar.radio(key="width_radio").set_value(values["width_radio"])
        at.sidebar.radio(key="kmax_radio").set_value(values["kmax_radio"])
        at.sidebar.number_input(key="seed_input").set_value(values["seed_input"])
        at.sidebar.text_input(key="walk_text").set_value(values["walk_text"]).run(timeout=TIMEOUT)
        assert not at.exception, (values, [str(e) for e in at.exception])


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_each_preset_shows_its_expected_verdict_lines(name):
    at = _fresh_app()
    at.sidebar.button(key=f"preset_{name}").click().run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    _kind, part_walk, part_live = EXPECTED[name]
    messages = _messages(at)
    assert any(part_walk in m for m in messages), (name, part_walk)
    assert any(part_live in m for m in messages), (name, part_live)
    preset = C.PRESETS[name]
    assert at.sidebar.slider(key="k_slider").value == preset["k"] and at.sidebar.text_input(key="walk_text").value == preset["walk"]
    assert at.sidebar.slider(key="n_slider").value == preset["n"] and at.sidebar.radio(key="width_radio").value == preset["width"]


def test_the_default_state_shows_the_forbidden_cycle_and_the_ladder():
    at = _fresh_app()
    messages = _messages(at)
    assert any("Der Weg 7-6-7 ist bei k = 2 **verboten**" in m for m in messages)
    assert any("83/3 (≈ 27,67) bei k = 1 (Lücke 7,78 %" in m for m in messages)
    assert [m.label for m in at.metric][:3] == ["Gedächtnis", "Weg", "Urteil"]
    assert [m.value for m in at.metric][:3] == ["k = 2", "7-6-7", "verboten"]


def test_permalink_sets_the_widgets_and_clamps_invalid_values():
    at = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT)
    at.query_params["k"] = "99"                  # über dem Maximum: auf 7 begrenzt
    at.query_params["weg"] = "5-3-5-1"
    at.query_params["n"] = "12"
    at.query_params["breite"] = "40"
    at.query_params["kmax"] = "7"                # keine Auswahl des Optionsfelds: ignoriert, Voreinstellung bleibt
    at.query_params["seed"] = "abc"              # keine Zahl: ignoriert
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    assert at.sidebar.slider(key="k_slider").value == 7
    assert at.sidebar.text_input(key="walk_text").value == "5-3-5-1"
    assert at.sidebar.slider(key="n_slider").value == 12 and at.sidebar.radio(key="width_radio").value == 40
    assert at.sidebar.radio(key="kmax_radio").value == C.DEFAULT_KMAX and at.sidebar.number_input(key="seed_input").value == C.DEFAULT_SEED


def test_permalink_text_is_cut_to_the_maximum_length():
    at = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT)
    at.query_params["weg"] = "1-2-" * 30
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    assert len(at.sidebar.text_input(key="walk_text").value) <= C.WALK_TEXT_MAX


@pytest.mark.parametrize("text", ["", "9-9", "a-b", "1-2-2-3", "-", "1-" * 30])
def test_an_invalid_walk_shows_a_warning_and_does_not_raise(text):
    at = _fresh_app()
    at.sidebar.text_input(key="walk_text").set_value(text).run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    assert any("ist ungültig" in w.value for w in at.warning)
    assert [m.value for m in at.metric][1:3] == ["ungültig", "–"]


def test_the_all_walks_counterproof_button_shows_a_success():
    at = _fresh_app()
    at.button(key="walkcheck_button").click().run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    assert any("In 9 von 9 Gedächtnissen stimmen bester Wert der Aufzählung und Schranke des Masters" in m.value for m in at.success)


def test_the_new_instance_button_changes_the_seed_inside_the_bounds():
    at = _fresh_app()
    at.sidebar.button[-1].click().run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    assert 0 <= at.sidebar.number_input(key="seed_input").value <= C.SEED_MAX


def test_expanders_are_found_by_title_and_the_assumptions_text_equals_the_readme():
    at = _fresh_app()
    labels = [e.label for e in at.expander]
    for title in ("💬 In einfachen Worten", "So funktioniert ng-Routen", "📐 Mathematische Formulierung", "⚠️ Annahmen, Grenzen und bekannte Probleme"):
        assert title in labels
    box = next(e for e in at.expander if e.label == "⚠️ Annahmen, Grenzen und bekannte Probleme")
    assert box.markdown[0].value.strip() == C.ASSUMPTIONS_MARKDOWN.strip()
    assert C.ASSUMPTIONS_MARKDOWN.strip() in README
    math = next(e for e in at.expander if e.label == "📐 Mathematische Formulierung")
    assert "**Lesehilfe.**" in math.markdown[0].value and "| Symbol | Bedeutung |" in math.markdown[0].value
    assert sum("**Lesehilfe.**" in b.value for b in math.markdown) == 1


def test_every_setting_has_an_entry_for_the_permalink():
    assert {spec.url_param for spec in P.SETTING_SPECS.values()} == {"k", "weg", "n", "breite", "kmax", "seed"}


def test_plotly_charts_have_unique_keys_and_locked_axes():
    at = _fresh_app()
    figures = [e for e in at.get("plotly_chart")]
    assert len(figures) == 6
    for fig in figures:
        assert '"fixedrange":true' in fig.proto.spec.replace(" ", "")
