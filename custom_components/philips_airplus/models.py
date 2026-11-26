"""Per-model profiles (pure module, no Home Assistant import).

The Air+ fans share one cloud protocol (AWS IoT shadow with D-codes) but differ
in how many speeds they have, how a speed is encoded, which presets exist and
what angle oscillation uses. Everything model-specific lives here, so adding a
model is: run the D-code sweep (debug log), add one ``ModelProfile``.

Verified mappings:
  CX3550/01 — see notes/properties.md (upstream, 2026-06/07)
  CX7550/01 — debug-log sweep on a physical unit, fw 0.2.9, 2026-11-26:
    * D0310C (mode) and D0310D (speed) report the same code in manual mode;
      levels 1..10 are encoded 1..10, level 11 = 81, level 12 = 82.
    * D0310C 0 = auto, 17 = sleep, 130 = natural breeze (echoes as -126).
    * Natural breeze cycles D0310D by itself (4 -> 6 -> 8 -> 10 ...).
    * D0320F oscillation reports and is set as the angle: 80 = on, 0 = off.
    * D03110 timer = hours + 1 (2 = 1 h, 4 = 3 h), D03211 = remaining minutes.
    * D03224 = temperature around the device in 0.1 degC (200 = 20.0 degC).
  CX7550/01 display settings — second sweep, 2026-11-26:
    * D03105 display brightness: 0 = off, 115 = low, 123 = high.
    * D03104 show temperature colour: 100 = on, 0 = off.
    * D03133 show temperature in standby: 1 = on, 0 = off.
    * D0312A preferred display indicator (setting): 7 = fan speed in manual
      mode (app overview shows "auto"), 5 = always temperature.
      D0312B mirrors what the display currently shows (read-only; it drops to 5
      in auto/sleep/natural even when D0312A is 7).
"""
from __future__ import annotations

from dataclasses import dataclass, field

PRESET_AUTO = "auto"
PRESET_SLEEP = "sleep"
PRESET_NATURAL = "natural"


@dataclass(frozen=True)
class ToggleSetting:
    """An on/off device setting, exposed as a CONFIG switch."""

    key: str  # translation_key and unique_id suffix
    code: str  # D-code
    on: int
    off: int

    def is_on(self, value) -> bool | None:
        try:
            return int(value) == self.on
        except (TypeError, ValueError):
            return None


@dataclass(frozen=True)
class ChoiceSetting:
    """A device setting with fixed values, exposed as a CONFIG select."""

    key: str  # translation_key and unique_id suffix
    code: str  # D-code
    options: dict[str, int]  # option (translated in the UI) -> wire value

    def value_to_option(self, value) -> str | None:
        try:
            value = int(value)
        except (TypeError, ValueError):
            return None
        for option, wire in self.options.items():
            if wire == value:
                return option
        return None


@dataclass(frozen=True)
class ModelProfile:
    """Model-specific encoding of the shared D-code protocol."""

    model: str
    # Wire code for each manual speed level; index 0 is level 1.
    speed_codes: tuple[int, ...]
    # preset name -> D0310C mode value (unsigned).
    presets: dict[str, int] = field(default_factory=dict)
    # Value to write to D0320F to start oscillating.
    oscillation_on: int = 90
    # translation_key of the fan entity (localizes preset names).
    translation_key: str = "cx3550"
    # Device reports D03224 (temperature x10).
    has_temperature: bool = False
    # Extra model-specific settings (switches / selects).
    toggles: tuple[ToggleSetting, ...] = ()
    choices: tuple[ChoiceSetting, ...] = ()

    @property
    def speed_count(self) -> int:
        return len(self.speed_codes)

    @property
    def preset_modes(self) -> list[str]:
        return list(self.presets)

    def level_to_code(self, level: int) -> int:
        """Manual level (1..speed_count) -> wire code. 0 or less -> 0."""
        if level <= 0:
            return 0
        level = min(level, self.speed_count)
        return self.speed_codes[level - 1]

    def code_to_level(self, code) -> int | None:
        """Wire code -> manual level, or None if the code is not a speed."""
        try:
            code = int(code)
        except (TypeError, ValueError):
            return None
        if code == 0:
            return 0
        try:
            return self.speed_codes.index(code) + 1
        except ValueError:
            return None

    def mode_to_preset(self, mode) -> str | None:
        """D0310C value -> preset name. Signed-byte echoes (-126) are normalized."""
        try:
            mode = int(mode) & 0xFF
        except (TypeError, ValueError):
            return None
        for name, value in self.presets.items():
            if value == mode:
                return name
        return None


CX3550 = ModelProfile(
    model="CX3550",
    speed_codes=(1, 2, 3),
    presets={PRESET_SLEEP: 17, PRESET_NATURAL: 130},
    oscillation_on=90,
    translation_key="cx3550",
)

CX7550 = ModelProfile(
    model="CX7550",
    speed_codes=(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 81, 82),
    presets={PRESET_AUTO: 0, PRESET_SLEEP: 17, PRESET_NATURAL: 130},
    oscillation_on=80,
    translation_key="cx7550",
    has_temperature=True,
    toggles=(
        ToggleSetting("temperature_color", "D03104", on=100, off=0),
        ToggleSetting("standby_temperature", "D03133", on=1, off=0),
    ),
    choices=(
        ChoiceSetting("display", "D03105", {"off": 0, "low": 115, "high": 123}),
        ChoiceSetting("display_indicator", "D0312A", {"fan_speed": 7, "temperature": 5}),
    ),
)

PROFILES = (CX3550, CX7550)
DEFAULT_PROFILE = CX3550  # behaviour of the original integration


def get_profile(modelid: str | None) -> ModelProfile:
    """Pick the profile by model id prefix (``CX7550/01`` -> CX7550)."""
    if modelid:
        for profile in PROFILES:
            if modelid.upper().startswith(profile.model):
                return profile
    return DEFAULT_PROFILE
