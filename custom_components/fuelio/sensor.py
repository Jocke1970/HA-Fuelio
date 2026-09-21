"""Summary-only Fuelio sensors; never expose GPS or identifying attributes."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import FuelioCoordinator
from .const import DOMAIN


@dataclass(frozen=True, kw_only=True)
class FuelioSensorDescription(SensorEntityDescription):
    """Description mapping one sensor to a snapshot field."""


DESCRIPTIONS: tuple[FuelioSensorDescription, ...] = (
    FuelioSensorDescription(key="trip_count", name="Trips", icon="mdi:routes"),
    FuelioSensorDescription(key="trip_distance_km", name="Trip distance", native_unit_of_measurement="km", device_class=SensorDeviceClass.DISTANCE, state_class=SensorStateClass.TOTAL),
    FuelioSensorDescription(key="monthly_trip_distance_km", name="Trip distance this month", native_unit_of_measurement="km", device_class=SensorDeviceClass.DISTANCE),
    FuelioSensorDescription(key="trip_duration_hours", name="Travel time", native_unit_of_measurement="h", device_class=SensorDeviceClass.DURATION),
    FuelioSensorDescription(key="estimated_trip_cost", name="Estimated trip costs (not actual spend)", native_unit_of_measurement="SEK", device_class=SensorDeviceClass.MONETARY),
    FuelioSensorDescription(key="fuel_count", name="Fuel-ups", icon="mdi:gas-station"),
    FuelioSensorDescription(key="fuel_litres", name="Fuel volume", native_unit_of_measurement="L", device_class=SensorDeviceClass.VOLUME),
    FuelioSensorDescription(key="fuel_cost", name="Fuel expenditure", native_unit_of_measurement="SEK", device_class=SensorDeviceClass.MONETARY),
    FuelioSensorDescription(key="monthly_fuel_cost", name="Fuel expenditure this month", native_unit_of_measurement="SEK", device_class=SensorDeviceClass.MONETARY),
    FuelioSensorDescription(key="last_fuel_price", name="Last fuel price", native_unit_of_measurement="SEK/L", icon="mdi:currency-usd"),
    FuelioSensorDescription(key="last_reported_consumption", name="Last reported fuel consumption", native_unit_of_measurement="L/100km", icon="mdi:gas-station"),
    FuelioSensorDescription(key="last_fillup_date", name="Last fuel-up", device_class=SensorDeviceClass.DATE),
    FuelioSensorDescription(key="expense_count", name="Expense entries", icon="mdi:receipt"),
    FuelioSensorDescription(key="other_expenses", name="Other expenditure", native_unit_of_measurement="SEK", device_class=SensorDeviceClass.MONETARY),
    FuelioSensorDescription(key="monthly_other_expenses", name="Other expenditure this month", native_unit_of_measurement="SEK", device_class=SensorDeviceClass.MONETARY),
    FuelioSensorDescription(key="upcoming_expense_count", name="Future expense entries", icon="mdi:calendar-clock"),
    FuelioSensorDescription(key="total_actual_cost", name="Total actual expenditure", native_unit_of_measurement="SEK", device_class=SensorDeviceClass.MONETARY),
    FuelioSensorDescription(key="last_trip_date", name="Last trip", device_class=SensorDeviceClass.DATE),
    FuelioSensorDescription(key="latest_odometer_km", name="Latest odometer", native_unit_of_measurement="km", device_class=SensorDeviceClass.DISTANCE),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Create summary sensor entities for one vehicle."""
    coordinator: FuelioCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(FuelioSensor(coordinator, entry, description) for description in DESCRIPTIONS)


class FuelioSensor(CoordinatorEntity[FuelioCoordinator], SensorEntity):
    """Expose an individual snapshot field."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: FuelioCoordinator, entry: ConfigEntry, description: FuelioSensorDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=coordinator.data.vehicle_name,
            manufacturer="Fuelio",
        )

    @property
    def native_value(self):
        """Read one summary value; raw routes and locations never leave parser."""
        return getattr(self.coordinator.data, self.entity_description.key)
