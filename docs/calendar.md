# Fuelio calendar model

HA-Fuelio `2026.11.0b4` extends the existing read-only Home Assistant calendar with sanitized Fuelio costs and recent journeys from the local ZIP.

## Source and scope

The calendar combines two bounded projections:

- up to 256 non-template, non-income rows from Fuelio `Costs` whose date is today or later
- up to 256 most recent rows from Fuelio `TripLog`

The source remains the local Fuelio ZIP. Nothing is written back to Fuelio.

## Cost events

Cost events are all-day Home Assistant calendar events.

The parser may retain only these calendar-facing fields:

- date
- sanitized cost-category display name
- amount in SEK
- coarse kind: `maintenance` or `expense`
- sanitized user-entered title when present (`CostTitle` or `Title`)
- sanitized user-entered `Notes` when present

Categories containing `Underhåll`, `Service` or `Reparation` are shown as maintenance events with a wrench marker. Other rows are general expense events. When a title is present it becomes the visible event title; category, amount and note are shown in the description.

Internal Fuelio IDs, vehicle identifiers and raw cost rows are not projected.

## Trip events

TripLog rows are exposed as timed Home Assistant calendar events.

Calendar presentation uses:

- `StartDate` and `EndDate` for event time
- `title` / `Title` for the visible journey title when present
- `TripCategory` and `TripNote` as sanitized local text when present
- `TripDist` as the logged trip distance
- `TripDuration` for duration
- `EndOdo` only as an ending odometer checkpoint

`TripDist` and ODO distance are deliberately not treated as the same measurement. Fuelio can log GPS-derived trip distance with decimals while the vehicle odometer advances differently because of measurement method, rounding and driving conditions.

A zero or blank `StartOdo` is not treated as a broken trip. Fuelio may derive the trip start from the previous ending odometer. HA-Fuelio does not reconstruct trip distance from `EndOdo - StartOdo`.

The calendar projection deliberately excludes GPS coordinates, route geometry, start/end place names and other location fields even if they exist in the ZIP.

## Read-only behavior and exclusions

The calendar does not support creating, editing or deleting Fuelio data.

- Fuelio `isTemplate=1` cost rows remain excluded because a template is not proof of a realized obligation.
- Income rows remain excluded.
- Estimated next fuel-up remains excluded because its forecast date can move as driving pace and range change.
- Historical cost rows are not retained for calendar browsing; historical/recent TripLog rows are retained within the 256-trip bound so the calendar can act as a local journey timeline.

## Refresh behavior

The existing Fuelio coordinator polls the local ZIP about every five minutes. Calendar data therefore changes with the same source refresh and does not require a separate poller.

Release flow remains `dev → beta → main`. For b4, real-HA validation should confirm timed trip rendering, cost title/note rendering, correct TripDist values, and absence of GPS/place data before stable promotion.
