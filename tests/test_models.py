"""Tests for models.py (pure module, loaded by path so no Home Assistant is needed)."""
import importlib.util
import sys
from pathlib import Path

_PATH = Path(__file__).parents[1] / "custom_components" / "philips_airplus" / "models.py"
_spec = importlib.util.spec_from_file_location("models", _PATH)
models = importlib.util.module_from_spec(_spec)
sys.modules["models"] = models  # dataclasses resolve their module via sys.modules
_spec.loader.exec_module(models)


def test_profile_selection():
    assert models.get_profile("CX7550/01") is models.CX7550
    assert models.get_profile("CX7550/00") is models.CX7550
    assert models.get_profile("CX3550/01") is models.CX3550
    # unknown / missing -> original behaviour
    assert models.get_profile("CX9999/01") is models.CX3550
    assert models.get_profile(None) is models.CX3550


def test_cx7550_speed_encoding_from_sweep():
    p = models.CX7550
    assert p.speed_count == 12
    assert [p.level_to_code(n) for n in range(1, 13)] == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 81, 82]
    assert p.code_to_level(81) == 11
    assert p.code_to_level(82) == 12
    assert p.code_to_level(6) == 6


def test_level_edges():
    p = models.CX7550
    assert p.level_to_code(0) == 0
    assert p.level_to_code(99) == 82  # clamped
    assert p.code_to_level(0) == 0
    assert p.code_to_level(55) is None
    assert p.code_to_level(None) is None
    assert p.code_to_level("x") is None


def test_cx7550_presets():
    p = models.CX7550
    assert p.mode_to_preset(0) == "auto"
    assert p.mode_to_preset(17) == "sleep"
    assert p.mode_to_preset(130) == "natural"
    assert p.mode_to_preset(-126) == "natural"  # signed-byte echo seen in the log
    assert p.mode_to_preset(6) is None  # manual speed, no preset


def test_cx3550_unchanged():
    p = models.CX3550
    assert p.speed_count == 3
    assert p.preset_modes == ["sleep", "natural"]
    assert p.mode_to_preset(0) is None  # CX3550 has no auto
    assert p.oscillation_on == 90
    assert not p.has_temperature


def test_cx7550_oscillation_and_temperature():
    assert models.CX7550.oscillation_on == 80
    assert models.CX7550.has_temperature
