"""Read-only Fuelio calendar built from sanitized future cost records."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import override

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import FuelioCoordinator
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create one read-only Fuelio calendar for the configured vehicle."""
    coordinator: FuelioCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([FuelioCalendar(coordinator, entry)])


class FuelioCalendar(CoordinatorEntity[FuelioCoordinator], CalendarEntity):
    """Expose sanitized current/future Fuelio costs as all-day calendar events."""

    _attr_name = "Fuelio"
    _attr_icon = "mdi:calendar-car"
    _attr_should_poll = False

    def __init__(self, coordinator: FuelioCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_calendar"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=coordinator.data.vehicle_name,
            manufacturer="Fuelio",
        )

    def _events(self) -> list[CalendarEvent]:
        """Convert the bounded parser projection to HA all-day events."""
        events: list[CalendarEvent] = []
        for item in self.coordinator.data.upcoming_calendar_events:
            try:
                start = date.fromisoformat(str(item["date"]))
            except (KeyError, TypeError, ValueError):
                continue
            category = str(item.get("category") or "Okategoriserat")
            kind = str(item.get("kind") or "expense")
            amount = item.get("amount")
            prefix = "🔧" if kind == "maintenance" else "💳"
            if isinstance(amount, (int, float)):
                description = f"Fuelio · {amount:.2f} SEK · read-only"
            else:
                description = "Fuelio · read-only"
            events.append(
                CalendarEvent(
                    start=start,
                    end=start + timedelta(days=1),
                    summary=f"{prefix} {category}",
                    description=description,
                )
            )
        return events

    @property
    @override
    def event(self) -> CalendarEvent | None:
        """Return the current or next upcoming Fuelio event."""
        events = self._events()
        return events[0] if events else None

    @override
    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return events overlapping the requested Home Assistant time range."""
        assert start_date < end_date
        return [
            event
            for event in self._events()
            if event.start_datetime_local < end_date
            and event.end_datetime_local > start_date
        ]
