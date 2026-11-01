# Fuelio calendar model

HA-Fuelio `2026.11.0b3` adds one read-only Home Assistant calendar entity from the local Fuelio ZIP.

## Source and scope

The calendar is derived only from non-template, non-income rows in Fuelio's `Costs` section whose date is today or later.

The parser keeps a bounded projection of at most 256 events. Each projection contains only:

- date
- sanitized cost-category display name
- amount in SEK
- coarse kind: `maintenance` or `expense`

Fuelio cost titles, notes, internal IDs, vehicle identifiers and other raw row data are never retained in the Home Assistant snapshot.

## Calendar presentation

Events are all-day Home Assistant `CalendarEvent` objects.

- Categories containing `Underhåll`, `Service` or `Reparation` are shown as maintenance events with a wrench marker.
- Other future costs are shown as general expense events.
- The description contains only the aggregate amount and a read-only marker.

The calendar is read-only. It does not support creating, editing or deleting Fuelio data.

## Deliberate exclusions in b3

- Fuelio `isTemplate=1` rows are excluded because a template is not proof of a realized future obligation.
- Income rows are excluded.
- Estimated next fuel-up is not a calendar event because its forecast date can move as driving pace and range change.
- Historical costs before today's date are not retained for calendar browsing.

## Refresh behavior

The existing Fuelio coordinator polls the local ZIP about every five minutes. Calendar data therefore changes with the same source refresh and does not require a separate poller.

Release flow remains `dev → beta → main`; validate entity creation and calendar rendering in a real Home Assistant installation before stable promotion.
