"""Fan platform for Philips Air+ fans (CX3550/01, CX7550/01).

Maps the shadow D-codes to a Home Assistant fan entity:

  on/off          D03102   power flag 0/1
  speed           D0310D   reported fan level (wire code, see models.py)
  mode / preset   D0310C   manual speed code, or a preset (auto/sleep/natural)
  oscillate       D0320F   angle (model-specific) / 0=off

Everything model-specific (number of speeds, speed encoding, presets,
oscillation angle) comes from ``models.get_profile(modelid)``.
Manual speeds are exposed as **percentage**; auto/sleep/natural are
**preset_modes**. Setting a percentage clears any preset (writes the speed code
to both D0310D and D0310C); setting a preset writes D0310C only and powers on.
"""
from __future__ import annotations

import math
from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.percentage import (
    percentage_to_ranged_value,
    ranged_value_to_percentage,
)

from .const import (
    DOMAIN,
    D_MODE,
    D_OSCILLATE,
    D_POWER,
    D_SPEED,
    MANUFACTURER,
    MODEL_CX3550,
    OSC_OFF,
)
from .coordinator import PhilipsAirplusCoordinator
from .models import get_profile


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    store = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        PhilipsAirplusFan(coordinator) for coordinator in store["coordinators"].values()
    )


class PhilipsAirplusFan(CoordinatorEntity, FanEntity):
    """A Philips Air+ fan."""

    _attr_has_entity_name = True
    _attr_name = None  # use the device name

    def __init__(self, coordinator: PhilipsAirplusCoordinator) -> None:
        super().__init__(coordinator)
        self.coordinator = coordinator
        self._profile = get_profile((coordinator.device_info or {}).get("modelid"))
        self._attr_unique_id = f"{coordinator.device_id}_fan"
        self._attr_translation_key = self._profile.translation_key
        self._attr_speed_count = self._profile.speed_count
        self._attr_preset_modes = self._profile.preset_modes
        self._attr_supported_features = (
            FanEntityFeature.TURN_ON
            | FanEntityFeature.TURN_OFF
            | FanEntityFeature.SET_SPEED
            | FanEntityFeature.PRESET_MODE
            | FanEntityFeature.OSCILLATE
        )

    @property
    def device_info(self) -> DeviceInfo:
        di = self.coordinator.device_info or {}
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.device_id)},
            name=di.get("name") or di.get("device_alias"),
            manufacturer=MANUFACTURER,
            model=di.get("modelid") or MODEL_CX3550,
            sw_version=di.get("swversion"),
            serial_number=di.get("mac"),
        )

    @property
    def available(self) -> bool:
        return self.coordinator.device_available

    # ---- state ----
    def _rep(self) -> dict:
        return self.coordinator.data or {}

    @property
    def is_on(self) -> bool:
        return int(self._rep().get(D_POWER, 0)) == 1

    @property
    def percentage(self) -> int | None:
        if not self.is_on:
            return 0
        level = self._profile.code_to_level(self._rep().get(D_SPEED))
        if level is None:
            return None
        if level == 0:
            return 0
        return ranged_value_to_percentage((1, self._profile.speed_count), level)

    @property
    def preset_mode(self) -> str | None:
        if not self.is_on:
            return None
        return self._profile.mode_to_preset(self._rep().get(D_MODE))

    @property
    def oscillating(self) -> bool:
        try:
            return int(self._rep().get(D_OSCILLATE, 0)) != 0
        except (TypeError, ValueError):
            return False

    # ---- helpers ----
    def _pct_to_code(self, percentage: int) -> int:
        if percentage <= 0:
            return 0
        level = math.ceil(
            percentage_to_ranged_value((1, self._profile.speed_count), percentage)
        )
        return self._profile.level_to_code(level)

    def _speed_desired(self, percentage: int) -> dict:
        code = self._pct_to_code(percentage)
        if code == 0:
            return {D_POWER: 0}
        # manual mode mirrors the speed code in D0310C
        return {D_POWER: 1, D_SPEED: code, D_MODE: code}

    # ---- commands ----
    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        desired: dict = {D_POWER: 1}
        if preset_mode in self._profile.presets:
            desired[D_MODE] = self._profile.presets[preset_mode]
        elif percentage is not None:
            desired = self._speed_desired(percentage)
        await self.coordinator.async_set_desired(desired)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_desired({D_POWER: 0})

    async def async_set_percentage(self, percentage: int) -> None:
        await self.coordinator.async_set_desired(self._speed_desired(percentage))

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        if preset_mode not in self._profile.presets:
            return
        await self.coordinator.async_set_desired(
            {D_POWER: 1, D_MODE: self._profile.presets[preset_mode]}
        )

    async def async_oscillate(self, oscillating: bool) -> None:
        await self.coordinator.async_set_desired(
            {D_OSCILLATE: self._profile.oscillation_on if oscillating else OSC_OFF}
        )
