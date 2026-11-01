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
    FuelioSensorDescription(key="trip_count", translation_key="trip_count", icon="mdi:routes"),
    FuelioSensorDescription(key="trip_distance_km", translation_key="trip_distance_km", native_unit_of_measurement="km", device_class=SensorDeviceClass.DISTANCE, state_class=SensorStateClass.TOTAL),
    FuelioSensorDescription(key="monthly_trip_distance_km", translation_key="monthly_trip_distance_km", native_unit_of_measurement="km", device_class=SensorDeviceClass.DISTANCE),
    FuelioSensorDescription(key="trip_duration_hours", translation_key="trip_duration_hours", native_unit_of_measurement="h", device_class=SensorDeviceClass.DURATION),
    FuelioSensorDescription(key="estimated_trip_cost", translation_key="estimated_trip_cost", native_unit_of_measurement="SEK", device_class=SensorDeviceClass.MONETARY),
    FuelioSensorDescription(key="fuel_count", translation_key="fuel_count", icon="mdi:gas-station"),
    FuelioSensorDescription(key="fuel_litres", translation_key="fuel_litres", native_unit_of_measurement="L", device_class=SensorDeviceClass.VOLUME),
    FuelioSensorDescription(key="fuel_cost", translation_key="fuel_cost", native_unit_of_measurement="SEK", device_class=SensorDeviceClass.MONETARY),
    FuelioSensorDescription(key="monthly_fuel_cost", translation_key="monthly_fuel_cost", native_unit_of_measurement="SEK", device_class=SensorDeviceClass.MONETARY),
    FuelioSensorDescription(key="last_fuel_price", translation_key="last_fuel_price", native_unit_of_measurement="SEK/L", icon="mdi:currency-usd"),
    FuelioSensorDescription(key="last_reported_consumption", translation_key="last_reported_consumption", native_unit_of_measurement="L/100km", icon="mdi:gas-station"),
    FuelioSensorDescription(key="last_fillup_date", translation_key="last_fillup_date", device_class=SensorDeviceClass.DATE),
    FuelioSensorDescription(key="expense_count", translation_key="expense_count", icon="mdi:receipt"),
    FuelioSensorDescription(key="other_expenses", translation_key="other_expenses", native_unit_of_measurement="SEK", device_class=SensorDeviceClass.MONETARY),
    FuelioSensorDescription(key="monthly_other_expenses", translation_key="monthly_other_expenses", native_unit_of_measurement="SEK", device_class=SensorDeviceClass.MONETARY),
    FuelioSensorDescription(key="upcoming_expense_count", translation_key="upcoming_expense_count", icon="mdi:calendar-clock"),
    FuelioSensorDescription(key="total_actual_cost", translation_key="total_actual_cost", native_unit_of_measurement="SEK", device_class=SensorDeviceClass.MONETARY),
    FuelioSensorDescription(key="last_trip_date", translation_key="last_trip_date", device_class=SensorDeviceClass.DATE),
    FuelioSensorDescription(key="latest_odometer_km", translation_key="latest_odometer_km", native_unit_of_measurement="km", device_class=SensorDeviceClass.DISTANCE),
    FuelioSensorDescription(key="distance_since_last_fillup_km", translation_key="distance_since_last_fillup_km", native_unit_of_measurement="km", device_class=SensorDeviceClass.DISTANCE, icon="mdi:map-marker-distance"),
    FuelioSensorDescription(key="estimated_fuel_remaining_l", translation_key="estimated_fuel_remaining_l", native_unit_of_measurement="L", device_class=SensorDeviceClass.VOLUME, icon="mdi:gas-station"),
    FuelioSensorDescription(key="estimated_range_remaining_km", translation_key="estimated_range_remaining_km", native_unit_of_measurement="km", device_class=SensorDeviceClass.DISTANCE, icon="mdi:map-marker-distance"),
    FuelioSensorDescription(key="estimated_days_to_next_fillup", translation_key="estimated_days_to_next_fillup", native_unit_of_measurement="d", icon="mdi:calendar-clock"),
    FuelioSensorDescription(key="estimated_next_fillup_date", translation_key="estimated_next_fillup_date", device_class=SensorDeviceClass.DATE, icon="mdi:calendar-alert"),
    FuelioSensorDescription(key="last_app_sync", translation_key="last_app_sync", device_class=SensorDeviceClass.TIMESTAMP, icon="mdi:cloud-sync"),
    # Six explicit calendar/lifetime ratios and two period-specific fill-up counters.
    # Keep stable unique keys/legacy entity IDs, but use OBD/tanking ODO deltas as denominator.
    FuelioSensorDescription(key="fuel_count_month", translation_key="fuel_count_month", icon="mdi:gas-station"),
    FuelioSensorDescription(key="fuel_count_year", translation_key="fuel_count_year", icon="mdi:gas-station"),
    FuelioSensorDescription(key="fuel_cost_per_km_month", translation_key="fuel_cost_per_km_month", native_unit_of_measurement="SEK/km", icon="mdi:cash"),
    FuelioSensorDescription(key="total_cost_per_km_month", translation_key="total_cost_per_km_month", native_unit_of_measurement="SEK/km", icon="mdi:cash-multiple"),
    FuelioSensorDescription(key="fuel_cost_per_km_year", translation_key="fuel_cost_per_km_year", native_unit_of_measurement="SEK/km", icon="mdi:cash"),
    FuelioSensorDescription(key="total_cost_per_km_year", translation_key="total_cost_per_km_year", native_unit_of_measurement="SEK/km", icon="mdi:cash-multiple"),
    FuelioSensorDescription(key="fuel_cost_per_km_all", translation_key="fuel_cost_per_km_all", native_unit_of_measurement="SEK/km", icon="mdi:cash"),
    FuelioSensorDescription(key="total_cost_per_km_all", translation_key="total_cost_per_km_all", native_unit_of_measurement="SEK/km", icon="mdi:cash-multiple"),
    # Eight real-observation extremes. Attribute recorded_on is the newest date on ties.
    FuelioSensorDescription(key="fuel_price_min_year", translation_key="fuel_price_min_year", native_unit_of_measurement="SEK/L", icon="mdi:arrow-down"),
    FuelioSensorDescription(key="fuel_price_max_year", translation_key="fuel_price_max_year", native_unit_of_measurement="SEK/L", icon="mdi:arrow-up"),
    FuelioSensorDescription(key="fuel_price_min_all", translation_key="fuel_price_min_all", native_unit_of_measurement="SEK/L", icon="mdi:arrow-down"),
    FuelioSensorDescription(key="fuel_price_max_all", translation_key="fuel_price_max_all", native_unit_of_measurement="SEK/L", icon="mdi:arrow-up"),
    FuelioSensorDescription(key="consumption_min_year", translation_key="consumption_min_year", native_unit_of_measurement="L/100km", icon="mdi:arrow-down"),
    FuelioSensorDescription(key="consumption_max_year", translation_key="consumption_max_year", native_unit_of_measurement="L/100km", icon="mdi:arrow-up"),
    FuelioSensorDescription(key="consumption_min_all", translation_key="consumption_min_all", native_unit_of_measurement="L/100km", icon="mdi:arrow-down"),
    FuelioSensorDescription(key="consumption_max_all", translation_key="consumption_max_all", native_unit_of_measurement="L/100km", icon="mdi:arrow-up"),
    # This entity's attributes contain aggregate-only YYYY-MM totals, max 120 months.
    FuelioSensorDescription(key="monthly_cost_breakdown", translation_key="monthly_cost_breakdown", native_unit_of_measurement="SEK", device_class=SensorDeviceClass.MONETARY, icon="mdi:calendar-month"),
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
                "trip_statistics": {
                    "years": list(snapshot.trip_statistics.get("years", ())),
                    "months": list(snapshot.trip_statistics.get("months", ())),
                    "weeks": list(snapshot.trip_statistics.get("weeks", ())),
                    "days": list(snapshot.trip_statistics.get("days", ())),
                    "distance_semantics": dict(snapshot.trip_statistics.get("distance_semantics", {})),
                    "days_limit": snapshot.trip_statistics.get("days_limit"),
                    "weeks_limit": snapshot.trip_statistics.get("weeks_limit"),
                },
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
