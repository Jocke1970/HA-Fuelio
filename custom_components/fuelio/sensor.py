"""Aggregate-only Fuelio sensors: never expose raw trips, GPS or identifiers."""
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
    """Description mapping a sensor to one aggregate snapshot field."""


DESCRIPTIONS: tuple[FuelioSensorDescription, ...] = (
    # Stable beta.3 entities: do not rename keys or change the unique_id formula.
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
    FuelioSensorDescription(key="distance_since_last_fillup_km", name="Distance since last fuel-up", native_unit_of_measurement="km", device_class=SensorDeviceClass.DISTANCE, icon="mdi:map-marker-distance"),
    FuelioSensorDescription(key="estimated_fuel_remaining_l", name="Estimated fuel remaining", native_unit_of_measurement="L", device_class=SensorDeviceClass.VOLUME, icon="mdi:gas-station"),
    FuelioSensorDescription(key="estimated_range_remaining_km", name="Estimated range remaining", native_unit_of_measurement="km", device_class=SensorDeviceClass.DISTANCE, icon="mdi:map-marker-distance"),
    FuelioSensorDescription(key="estimated_days_to_next_fillup", name="Estimated days to next fuel-up", native_unit_of_measurement="d", icon="mdi:calendar-clock"),
    FuelioSensorDescription(key="estimated_next_fillup_date", name="Estimated next fuel-up", device_class=SensorDeviceClass.DATE, icon="mdi:calendar-alert"),
    FuelioSensorDescription(key="last_app_sync", name="Last Fuelio app sync", device_class=SensorDeviceClass.TIMESTAMP, icon="mdi:cloud-sync"),
    # Six explicit calendar/lifetime ratios and two period-specific fill-up counters.
    # Keep stable unique keys/legacy entity IDs, but use OBD/tanking ODO deltas as denominator.
    FuelioSensorDescription(key="fuel_count_month", name="Fuel-ups this month", icon="mdi:gas-station"),
    FuelioSensorDescription(key="fuel_count_year", name="Fuel-ups this year", icon="mdi:gas-station"),
    FuelioSensorDescription(key="fuel_cost_per_km_month", name="Fuel cost per odometer km this month", native_unit_of_measurement="SEK/km", icon="mdi:cash"),
    FuelioSensorDescription(key="total_cost_per_km_month", name="Total cost per odometer km this month", native_unit_of_measurement="SEK/km", icon="mdi:cash-multiple"),
    FuelioSensorDescription(key="fuel_cost_per_km_year", name="Fuel cost per odometer km this year", native_unit_of_measurement="SEK/km", icon="mdi:cash"),
    FuelioSensorDescription(key="total_cost_per_km_year", name="Total cost per odometer km this year", native_unit_of_measurement="SEK/km", icon="mdi:cash-multiple"),
    FuelioSensorDescription(key="fuel_cost_per_km_all", name="Fuel cost per odometer km since import start", native_unit_of_measurement="SEK/km", icon="mdi:cash"),
    FuelioSensorDescription(key="total_cost_per_km_all", name="Total cost per odometer km since import start", native_unit_of_measurement="SEK/km", icon="mdi:cash-multiple"),
    # Eight real-observation extremes. Attribute recorded_on is the newest date on ties.
    FuelioSensorDescription(key="fuel_price_min_year", name="Lowest fuel price this year", native_unit_of_measurement="SEK/L", icon="mdi:arrow-down"),
    FuelioSensorDescription(key="fuel_price_max_year", name="Highest fuel price this year", native_unit_of_measurement="SEK/L", icon="mdi:arrow-up"),
    FuelioSensorDescription(key="fuel_price_min_all", name="Lowest fuel price since import start", native_unit_of_measurement="SEK/L", icon="mdi:arrow-down"),
    FuelioSensorDescription(key="fuel_price_max_all", name="Highest fuel price since import start", native_unit_of_measurement="SEK/L", icon="mdi:arrow-up"),
    FuelioSensorDescription(key="consumption_min_year", name="Lowest reported consumption this year", native_unit_of_measurement="L/100km", icon="mdi:arrow-down"),
    FuelioSensorDescription(key="consumption_max_year", name="Highest reported consumption this year", native_unit_of_measurement="L/100km", icon="mdi:arrow-up"),
    FuelioSensorDescription(key="consumption_min_all", name="Lowest reported consumption since import start", native_unit_of_measurement="L/100km", icon="mdi:arrow-down"),
    FuelioSensorDescription(key="consumption_max_all", name="Highest reported consumption since import start", native_unit_of_measurement="L/100km", icon="mdi:arrow-up"),
    # This entity's attributes contain aggregate-only YYYY-MM totals, max 120 months.
    FuelioSensorDescription(key="monthly_cost_breakdown", name="Monthly cost breakdown", native_unit_of_measurement="SEK", device_class=SensorDeviceClass.MONETARY, icon="mdi:calendar-month"),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Create summary sensors for one configured vehicle."""
    coordinator: FuelioCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(FuelioSensor(coordinator, entry, description) for description in DESCRIPTIONS)


class FuelioSensor(CoordinatorEntity[FuelioCoordinator], SensorEntity):
    """Expose only one aggregate value and, optionally, bounded aggregate attributes."""

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
        """Read one summary; no source rows leave the parser."""
        if self.entity_description.key == "monthly_cost_breakdown":
            return round(self.coordinator.data.monthly_fuel_cost + self.coordinator.data.monthly_other_expenses, 2)
        return getattr(self.coordinator.data, self.entity_description.key)

    @property
    def extra_state_attributes(self) -> dict | None:
        """Expose dates for records or a capped, identifier-free monthly summary."""
        key = self.entity_description.key
        snapshot = self.coordinator.data
        if key == "monthly_cost_breakdown":
            return {
                "months": list(snapshot.monthly_cost_history),
                "years": list(snapshot.yearly_cost_history),
                "categories_all": list(snapshot.all_cost_categories),
                "distance_basis": "odometer_checkpoints",
                "lifetime_odometer_km": snapshot.odometer_lifetime_km,
                "lifetime_odo_coverage": snapshot.odometer_lifetime_coverage,
                "estimated_lifetime": snapshot.estimated_lifetime,
                "latest_two_consumption": snapshot.latest_two_consumption,
                "latest_two_consumption_count": snapshot.latest_two_consumption_count,
                "history_truncated": snapshot.monthly_history_truncated,
                "months_limit": 120,
            }
        if key in {
            "estimated_fuel_remaining_l",
            "estimated_range_remaining_km",
            "estimated_days_to_next_fillup",
            "estimated_next_fillup_date",
        }:
            return dict(snapshot.fuel_forecast)
        if key == "distance_since_last_fillup_km":
            return {"last_fillup_date": snapshot.last_fillup_date.isoformat() if snapshot.last_fillup_date else None}
        if key == "last_app_sync":
            return {"source": "local_zip_mtime", "meaning": "Fuelio/Drive source modification time preserved by rclone"}
        if key in snapshot.record_dates:
            return {"recorded_on": snapshot.record_dates[key]}
        return None
