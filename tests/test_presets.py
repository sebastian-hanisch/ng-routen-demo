"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, und je Preset die erwartete Verdikt-Zeile (DEMO-PLAYBOOK §11a Punkt 7)."""

import pytest

import ngr_algorithm as A
import ngr_constants as C
import ngr_evaluation as ev
import ngr_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_bounds_and_the_walk_is_valid():
    for name, preset in C.PRESETS.items():
        assert C.HAND_K_MIN <= preset["k"] <= C.HAND_K_MAX and C.N_MIN <= preset["n"] <= C.N_MAX and 0 <= preset["seed"] <= C.SEED_MAX, name
        assert preset["width"] in C.WIDTH_OPTIONS and preset["kmax"] in C.KMAX_OPTIONS, name
        assert ev.parse_walk(preset["walk"], 7) is not None and len(preset["walk"]) <= C.WALK_TEXT_MAX, name


def test_default_preset_equals_the_default_settings():
    first = C.PRESETS[next(iter(C.PRESETS))]
    assert first == {"k": C.DEFAULT_HAND_K, "walk": C.DEFAULT_WALK, "n": C.DEFAULT_N, "width": C.DEFAULT_WIDTH, "kmax": C.DEFAULT_KMAX, "seed": C.DEFAULT_SEED}
    assert {key: spec.default for key, spec in P.SETTING_SPECS.items()} == {P.PRESET_KEYS[k]: v for k, v in first.items()}


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_presets_are_pairwise_different():
    values = [tuple(sorted(p.items())) for p in C.PRESETS.values()]
    assert len(set(values)) == len(values)


def test_the_ladder_stages_are_below_the_largest_k_and_end_with_it():
    for kmax in C.KMAX_OPTIONS:
        ks = ev.ladder_ks(kmax)
        assert ks[-1] == kmax and list(ks) == sorted(set(ks)) and all(k in C.LIVE_LADDER for k in ks[:-1])
    assert ev.ladder_ks(5) == (1, 2, 3, 4, 5) and ev.ladder_ks(8) == (1, 2, 3, 4, 5, 8) and ev.ladder_ks(12) == C.LIVE_LADDER


# je Preset: (Art des Wegurteils, Satzteil des Wegurteils, Satzteil des Urteils der Zufallsinstanz)
EXPECTED = {
    "Kreis 7-6-7, k = 2 (Voreinstellung)": ("warning", "ist bei k = 2 **verboten**: An Stelle 3 steht Kunde 7", "liegt die Schranke bei k = 1 um 2,31 % unter der bei k = 8; **ab k = 3** ist die Lücke 0"),
    "Weg 5-3-5-1, k = 2": ("info", "ist bei k = 2 **erlaubt**, obwohl er einen Kunden mehrmals besucht", "liegt die Schranke bei k = 1 um 2,31 % unter der bei k = 8; **ab k = 3** ist die Lücke 0"),
    "Dreieck 7-6-1-7, k = 2": ("info", "ist bei k = 2 **erlaubt**, obwohl er einen Kunden mehrmals besucht", "liegt die Schranke bei k = 1 um 2,31 % unter der bei k = 8; **ab k = 3** ist die Lücke 0"),
    "k = 1: nur direkte Wiederholung verboten": ("info", "ist bei k = 1 **erlaubt**, obwohl er einen Kunden mehrmals besucht", "liegt die Schranke bei k = 1 um 2,31 % unter der bei k = 8"),
    "30 Kunden, enge Fenster (Breite 20)": ("warning", "ist bei k = 2 **verboten**", "ist die Schranke schon bei k = 1 gleich der bei k = 5"),
    "30 Kunden, breite Fenster, k bis 12": ("warning", "ist bei k = 2 **verboten**", "liegt die Schranke bei k = 1 um 5,45 % unter der bei k = 12; **ab k = 4** ist die Lücke 0"),
}


def test_every_preset_has_an_expected_verdict_line():
    assert set(EXPECTED) == set(C.PRESETS)


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_expected_verdict_lines_of_each_preset(name):
    preset = C.PRESETS[name]
    kind_w, part_w, part_live = EXPECTED[name]
    walk = ev.parse_walk(preset["walk"], 7)
    kind, text = ev.verdict_walk(preset["k"], walk, ev.analyse_walk(preset["k"], walk), 7)
    assert kind == kind_w and part_w in text
    rows = ev.live_ladder(preset["n"], preset["width"], preset["seed"], preset["kmax"])
    kind, text = ev.verdict_live(rows, preset["n"], preset["width"])
    assert part_live in text, text


def test_the_help_texts_state_what_the_computation_shows():
    """Die Aussagen der Hilfetexte, Stück für Stück gegen die Rechnung."""
    inst, _ = ev.hand()
    assert not A.walk_allowed(inst, A.ng(2), (7, 6, 7))                              # Voreinstellung: dort verboten
    assert A.walk_allowed(inst, A.ng(2), (5, 3, 5, 1)) and not A.walk_allowed(inst, A.ng(3), (5, 3, 5, 1))
    assert A.walk_allowed(inst, A.ng(2), (7, 6, 1, 7)) and not A.walk_allowed(inst, A.kcyc(3), (7, 6, 1, 7))
    assert A.walk_allowed(inst, A.ng(1), (7, 6, 7))
    rows = ev.live_ladder(30, 100, 1, 12)
    assert round(rows[0].gap, 1) == 5.5 and [r.k for r in rows if r.gap == 0.0][0] == 4
    for seed in range(1, 9):                                                         # „bei den Zufalls-Seeds 1 bis 8“: Lücke 0 schon bei k = 1 (Breite 20, 30 Kunden, größtes k = 5)
        enge = ev.live_ladder(30, 20, seed, 5)
        assert enge[0].gap == 0.0 and not any(r.aborted for r in enge), seed
