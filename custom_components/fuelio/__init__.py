"""Read-only Fuelio ZIP integration for Home Assistant."""
from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import CONF_FILE_PATH, DOMAIN
from .parser import FuelioSnapshot, load_snapshot

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor"]


class FuelioCoordinator(DataUpdateCoordinator[FuelioSnapshot]):
    """Poll a local ZIP, never log user-specific source rows or file paths."""

    def __init__(self, hass: HomeAssistant, path: str) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(minutes=5))
        self.path = path

    async def _async_update_data(self) -> FuelioSnapshot:
        try:
            return await self.hass.async_add_executor_job(load_snapshot, self.path, dt_util.now().date())
        except (OSError, ValueError):
            raise UpdateFailed("Cannot read Fuelio backup; check local ZIP file and format") from None


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a configured Fuelio backup."""
    coordinator = FuelioCoordinator(hass, entry.data[CONF_FILE_PATH])
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Fuelio sensors."""
    if await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id, None)
        return True
    return False
