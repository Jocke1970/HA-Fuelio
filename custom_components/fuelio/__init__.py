"""Read-only Fuelio ZIP integration for Home Assistant."""
from __future__ import annotations

from datetime import timedelta
import logging
from pathlib import Path

import voluptuous as vol

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_ENTITY_ID,
    ATTR_RANGE_KM,
    CONF_FILE_PATH,
    DOMAIN,
    SERVICE_CALIBRATE_RANGE,
    SERVICE_CLEAR_RANGE_CALIBRATION,
)
from .parser import (
    FuelioSnapshot,
    apply_range_calibration,
    load_snapshot,
    range_calibration_consumption,
)

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor"]
FRONTEND_URL = "/fuelio/ha-fuelio-card.js"
FRONTEND_FILE = Path(__file__).parent / "www" / "ha-fuelio-card.js"
FRONTEND_REGISTERED = "_frontend_registered"
SERVICES_REGISTERED = "_services_registered"
CALIBRATION_STORE_VERSION = 1


class FuelioCoordinator(DataUpdateCoordinator[FuelioSnapshot]):
    """Poll a local ZIP and apply an optional HA-local current-tank calibration."""

    def __init__(self, hass: HomeAssistant, path: str, entry_id: str) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(minutes=5))
        self.path = path
        self.entry_id = entry_id
        self._raw_snapshot: FuelioSnapshot | None = None
        self._calibration: dict | None = None
        self._calibration_store = Store(
            hass,
            CALIBRATION_STORE_VERSION,
            f"{DOMAIN}.range_calibration.{entry_id}",
        )

    async def async_initialize(self) -> None:
        """Load an HA-local calibration before the first coordinator refresh."""
        stored = await self._calibration_store.async_load()
        self._calibration = stored if isinstance(stored, dict) else None

    async def _async_update_data(self) -> FuelioSnapshot:
        try:
            snapshot = await self.hass.async_add_executor_job(
                load_snapshot, self.path, dt_util.now().date()
            )
        except (OSError, ValueError):
            raise UpdateFailed("Cannot read Fuelio backup; check local ZIP file and format") from None

        self._raw_snapshot = snapshot
        calibration = self._calibration
        if calibration is None:
            return snapshot

        current_marker = snapshot.fuel_forecast.get("latest_primary_fillup_marker")
        anchor_marker = calibration.get("anchor_primary_fillup_marker")

        # b16 stored only the total primary-fill count. That could falsely reset
        # a calibration when a reload caught up with older/historical source
        # changes. Migrate legacy state to the stable latest-fill marker unless
        # the source clearly contains a fill-up after the calibration date.
        if anchor_marker is None:
            calibrated_at = dt_util.parse_datetime(str(calibration.get("calibrated_at", "")))
            calibration_day = calibrated_at.date() if calibrated_at is not None else None
            if (
                calibration_day is not None
                and snapshot.last_fillup_date is not None
                and snapshot.last_fillup_date > calibration_day
            ):
                _LOGGER.info("Clearing legacy Fuelio range calibration after a newer fill-up")
                self._calibration = None
                await self._calibration_store.async_remove()
                return snapshot
            calibration["anchor_primary_fillup_marker"] = current_marker
            calibration["anchor_primary_fillup_count"] = snapshot.fuel_forecast.get(
                "primary_fillup_count"
            )
            self._calibration = calibration
            await self._calibration_store.async_save(calibration)
            anchor_marker = current_marker

        if current_marker != anchor_marker:
            _LOGGER.info("Clearing Fuelio range calibration after a new primary-tank fill-up")
            self._calibration = None
            await self._calibration_store.async_remove()
            return snapshot

        try:
            return apply_range_calibration(
                snapshot,
                calibration["consumption_l_per_100km"],
                target_range_km=calibration.get("target_range_km"),
                calibrated_at=calibration.get("calibrated_at"),
                today=dt_util.now().date(),
            )
        except (KeyError, TypeError, ValueError):
            _LOGGER.warning("Discarding invalid persisted Fuelio range calibration")
            self._calibration = None
            await self._calibration_store.async_remove()
            return snapshot

    async def async_calibrate_range(self, target_range_km: float) -> None:
        """Calibrate the current tank to the vehicle computer's remaining range."""
        base = self._raw_snapshot or self.data
        if base is None:
            raise ValueError("Fuelio data is not available")
        primary_fillups = base.fuel_forecast.get("primary_fillup_count")
        primary_marker = base.fuel_forecast.get("latest_primary_fillup_marker")
        if (
            not isinstance(primary_fillups, int)
            or primary_fillups < 1
            or not isinstance(primary_marker, str)
            or not primary_marker
        ):
            raise ValueError("A primary-tank fill-up is required before calibration")

        consumption = range_calibration_consumption(base, target_range_km)
        calibrated_at = dt_util.now().isoformat()
        self._calibration = {
            "anchor_primary_fillup_count": primary_fillups,
            "anchor_primary_fillup_marker": primary_marker,
            "consumption_l_per_100km": consumption,
            "target_range_km": round(float(target_range_km), 1),
            "calibrated_at": calibrated_at,
        }
        await self._calibration_store.async_save(self._calibration)
        self.async_set_updated_data(
            apply_range_calibration(
                base,
                consumption,
                target_range_km=target_range_km,
                calibrated_at=calibrated_at,
                today=dt_util.now().date(),
            )
        )

    async def async_clear_range_calibration(self) -> None:
        """Return immediately to the automatic Fuelio forecast."""
        self._calibration = None
        await self._calibration_store.async_remove()
        if self._raw_snapshot is not None:
            self.async_set_updated_data(self._raw_snapshot)
        else:
            await self.async_request_refresh()


async def _async_register_frontend(hass: HomeAssistant) -> None:
    """Serve the bundled Lovelace card directly from the HACS integration."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if domain_data.get(FRONTEND_REGISTERED):
        return
    await hass.http.async_register_static_paths(
        [StaticPathConfig(FRONTEND_URL, str(FRONTEND_FILE), cache_headers=False)]
    )
    domain_data[FRONTEND_REGISTERED] = True


def _coordinator_for_entity(hass: HomeAssistant, entity_id: str) -> FuelioCoordinator:
    registry_entry = er.async_get(hass).async_get(entity_id)
    if (
        registry_entry is None
        or registry_entry.platform != DOMAIN
        or registry_entry.config_entry_id is None
    ):
        raise ServiceValidationError("Select an entity from the Fuelio integration")
    coordinator = hass.data.get(DOMAIN, {}).get(registry_entry.config_entry_id)
    if not isinstance(coordinator, FuelioCoordinator):
        raise ServiceValidationError("Fuelio config entry is not loaded")
    return coordinator


async def _async_register_services(hass: HomeAssistant) -> None:
    """Register HA-local range calibration services once."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if domain_data.get(SERVICES_REGISTERED):
        return

    async def calibrate(call: ServiceCall) -> None:
        coordinator = _coordinator_for_entity(hass, call.data[ATTR_ENTITY_ID])
        try:
            await coordinator.async_calibrate_range(call.data[ATTR_RANGE_KM])
        except ValueError as exc:
            raise ServiceValidationError(str(exc)) from exc

    async def clear(call: ServiceCall) -> None:
        coordinator = _coordinator_for_entity(hass, call.data[ATTR_ENTITY_ID])
        await coordinator.async_clear_range_calibration()

    hass.services.async_register(
        DOMAIN,
        SERVICE_CALIBRATE_RANGE,
        calibrate,
        schema=vol.Schema({
            vol.Required(ATTR_ENTITY_ID): cv.entity_id,
            vol.Required(ATTR_RANGE_KM): vol.All(vol.Coerce(float), vol.Range(min=1, max=5000)),
        }),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CLEAR_RANGE_CALIBRATION,
        clear,
        schema=vol.Schema({
            vol.Required(ATTR_ENTITY_ID): cv.entity_id,
        }),
    )
    domain_data[SERVICES_REGISTERED] = True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a configured Fuelio backup."""
    await _async_register_frontend(hass)
    coordinator = FuelioCoordinator(hass, entry.data[CONF_FILE_PATH], entry.entry_id)
    await coordinator.async_initialize()
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await _async_register_services(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Fuelio sensors."""
    if await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id, None)
        return True
    return False
