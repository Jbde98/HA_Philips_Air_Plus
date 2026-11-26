"""Select platform for Philips Air+: pick a fan level directly.

  * fan_level  D0310D / D0310C  options "1".."N" (N = the model's speed count)

The fan entity exposes speed as a percentage (HA convention, also what voice
assistants use). With 12 levels on the CX7550 a percentage slider is fiddly, so
this select offers every level as its own option for dashboards and automations.

State: the level the device currently reports (D0310D), also while a preset
(auto / sleep / natural breeze) is running, since those drive the speed too.
Selecting a level powers the fan on in manual mode at that level.
"""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import D_MODE, D_POWER, D_SPEED, DOMAIN, MANUFACTURER, MODEL_CX3550
from .coordinator import PhilipsAirplusCoordinator
from .models import get_profile


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    store = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        PhilipsAirplusFanLevelSelect(coordinator)
        for coordinator in store["coordinators"].values()
    )


class PhilipsAirplusFanLevelSelect(CoordinatorEntity, SelectEntity):
    """Direct fan level selection (1..speed_count)."""

    _attr_has_entity_name = True
    _attr_translation_key = "fan_level"

    def __init__(self, coordinator: PhilipsAirplusCoordinator) -> None:
        super().__init__(coordinator)
        self.coordinator = coordinator
        self._profile = get_profile((coordinator.device_info or {}).get("modelid"))
        self._attr_unique_id = f"{coordinator.device_id}_fan_level"
        self._attr_options = [str(level) for level in range(1, self._profile.speed_count + 1)]

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

    @property
    def current_option(self) -> str | None:
        level = self._profile.code_to_level((self.coordinator.data or {}).get(D_SPEED))
        if not level:  # None (unknown code) or 0
            return None
        return str(level)

    async def async_select_option(self, option: str) -> None:
        code = self._profile.level_to_code(int(option))
        # same write as the fan entity's manual speed: mode mirrors the speed code
        await self.coordinator.async_set_desired({D_POWER: 1, D_SPEED: code, D_MODE: code})
