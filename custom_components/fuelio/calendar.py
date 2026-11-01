"""Read-only Fuelio calendar built from sanitized cost and trip records."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import override

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

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
    """Expose sanitized Fuelio trips and current/future costs as calendar events."""

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

    def _local_datetime(self, raw: object) -> datetime:
        """Interpret Fuelio's timezone-less trip timestamp in HA's local zone."""
        parsed = datetime.fromisoformat(str(raw))
        if parsed.tzinfo is not None:
            return dt_util.as_local(parsed)
        zone = dt_util.get_time_zone(self.hass.config.time_zone)
        if zone is None:
            zone = dt_util.DEFAULT_TIME_ZONE
        return parsed.replace(tzinfo=zone)

    def _events(self) -> list[CalendarEvent]:
        """Convert the bounded parser projection to Home Assistant events."""
        events: list[CalendarEvent] = []
        for item in self.coordinator.data.upcoming_calendar_events:
            kind = str(item.get("kind") or "expense")

            if kind == "trip":
                try:
                    start_dt = self._local_datetime(item["start"])
                    end_dt = self._local_datetime(item["end"])
                except (KeyError, TypeError, ValueError):
                    continue
                if end_dt <= start_dt:
                    end_dt = start_dt + timedelta(minutes=1)

                title = str(item.get("title") or "Resa")
                details: list[str] = []
                category = item.get("category")
                if category:
                    details.append(str(category))
                distance = item.get("distance_km")
                duration = item.get("duration_minutes")
                travel = []
                if isinstance(distance, (int, float)):
                    travel.append(f"{distance:.2f} km")
                if isinstance(duration, (int, float)):
                    travel.append(f"{duration:.0f} min")
                if travel:
                    details.append(" · ".join(travel))
                end_odo = item.get("end_odometer_km")
                if isinstance(end_odo, (int, float)):
                    details.append(f"ODO: {end_odo:.0f} km")
                note = item.get("note")
                if note:
                    details.append(f"📝 {note}")
                details.append("Fuelio · read-only")
                events.append(
                    CalendarEvent(
                        start=start_dt,
                        end=end_dt,
                        summary=f"🚗 {title}",
                        description="\n".join(details),
                    )
                )
                continue

            try:
                start = date.fromisoformat(str(item["date"]))
            except (KeyError, TypeError, ValueError):
                continue
            category = str(item.get("category") or "Okategoriserat")
            title = str(item.get("title") or category)
            amount = item.get("amount")
            prefix = "🔧" if kind == "maintenance" else "💳"
            details = [category] if title != category else []
            if isinstance(amount, (int, float)):
                details.append(f"{amount:.2f} SEK")
            note = item.get("note")
            if note:
                details.append(f"Notering: {note}")
            details.append("Fuelio · read-only")
            events.append(
                CalendarEvent(
                    start=start,
                    end=start + timedelta(days=1),
                    summary=f"{prefix} {title}",
                    description="\n".join(details),
                )
            )

        events.sort(key=lambda event: event.start_datetime_local)
        return events

    @property
    @override
    def event(self) -> CalendarEvent | None:
        """Return the current or next upcoming Fuelio event, not an old trip."""
        now = dt_util.now()
        for event in self._events():
            if event.end_datetime_local > now:
                return event
        return None

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
