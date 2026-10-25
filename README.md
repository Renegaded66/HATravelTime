![Travel Time](custom_components/traveltimefree/brand/logo.png)

# Travel Time for Home Assistant

A custom Home Assistant integration that answers one question: **how long does this trip take
right now?** It asks Google Maps (via a small companion add-on that runs a headless browser) and
exposes the result as a sensor, so automations can react to real traffic conditions.

* **Free and open source** – no API key, no registration, no subscription.
* **Real Google Maps data**, including current traffic.
* **Start and destination can be addresses *or* entities** – `person`, `zone`, `device_tracker`
  or any `sensor` that carries coordinates.
* **Entities are resolved when the value is requested**, so a `person` start point uses the
  coordinates that person has *at that moment*.
* **Everything on one page**: name, start, destination (and an optional update interval).
* **Editable at any time** – `Configure` / `Reconfigure` on the integration entry.
* **Manual or automatic** – press the button, or let it refresh on a schedule you choose.

## Requirements

| Component | Why |
| :-- | :-- |
| **Travel Time** add-on (this repository) | Scrapes Google Maps with Playwright/Firefox. Home Assistant integrations cannot ship browser engines, so the add-on is mandatory. |
| Home Assistant **2026.3** or newer for the logo | Local brand images (`brand/` inside the integration) are supported since 2026.3. Everything else works on older versions. |

## Installation

### 1. Add-on (backend)

1. **Settings → Add-ons → Add-on store → ⋮ → Repositories**
2. Add `https://github.com/Renegaded66/HATravelTime`
3. Install **Travel Time**, then **Start** it.
   `boot: auto` keeps it running across restarts; the watchdog restarts it if it crashes.

### 2. Integration (HACS)

1. **HACS → ⋮ → Custom repositories** → add `https://github.com/Renegaded66/HATravelTime`
   with category **Integration**.
2. Install **Travel Time**, then restart Home Assistant.

## Setup: one page, three fields

**Settings → Devices & services → Add integration → Travel Time**

| Field | What to enter |
| :-- | :-- |
| **Name** | Name of the trip, e.g. `Commute` – becomes the device name. |
| **Start** | An address (`Bahnhofstraße 1, 44532 Lünen`) **or** an entity from the list (`Devon (person.devon)`). |
| **Destination** | Same as start. |
| **Update automatically** | `0` = only when the refresh button is pressed. Any other value = refresh every *n* minutes. |

The start/destination pickers are combo boxes: they list every `person`, `zone`,
`device_tracker` and every `sensor` that currently has coordinates, and you can simply type an
address instead of picking an entity. Addresses are passed to Google Maps unchanged.

### Why entities instead of coordinates?

An address is fixed, but a person is not. When the travel time is requested, the integration reads
the entity's **current** `latitude`/`longitude` and sends those coordinates to Google Maps. So:

* *Start = `person.devon`* means "the way from wherever Devon is right now".
* *Start = `zone.home`, destination = `zone.arbeit`* always uses the zone centres.
* If a person has no GPS fix at that moment (state `unknown`, no coordinates), the request fails
  with a clear message instead of silently using stale coordinates.

## Entities

One device per trip, with three entities:

| Entity | Description |
| :-- | :-- |
| `sensor.<trip>_travel_time` | Travel time in **minutes** (`duration` device class, statistics enabled). |
| `sensor.<trip>_last_updated` | Timestamp of the last successful request. |
| `button.<trip>_refresh_now` | Triggers a request immediately. |

The travel time sensor carries the details of the last request as attributes:

| Attribute | Meaning |
| :-- | :-- |
| `start`, `end` | What you configured. |
| `start_query`, `end_query` | What was actually sent to Google Maps (address or `lat,lon`). |
| `start_label`, `end_label` | Friendly name of a resolved entity. |
| `start_source`, `end_source` | `address` or `entity`. |
| `distance_km` | Route distance, if the add-on provides it. |
| `last_successful_update` | Same timestamp as the *Last updated* sensor. |

If a request fails (add-on stopped, no GPS fix, Google unreachable) the entities become
**unavailable** and the reason is written to the log – never a fake value.

## Editing a trip

* **Settings → Devices & services → Travel Time → Configure** opens the same one-page form with
  the current values, including the name. Saving reloads the entry with the new settings.
* **⋮ → Reconfigure** does the same from the entry menu.

Existing trips from version 1.x are migrated automatically on first start; their entity ids and
history are preserved.

## Automations

```yaml
# Every weekday at 06:45: refresh the commute and report it
automation:
  - alias: "Commute travel time"
    triggers:
      - trigger: time
        at: "06:45:00"
    conditions:
      - condition: time
        weekday: [mon, tue, wed, thu, fri]
    actions:
      - action: button.press
        target:
          entity_id: button.commute_jetzt_aktualisieren
      - delay: "00:00:20"
      - action: notify.send_message
        data:
          message: >
            Commute: {{ states('sensor.commute_reisezeit') }} min
            ({{ state_attr('sensor.commute_reisezeit', 'distance_km') }} km)
```

Entity ids follow the Home Assistant UI language at creation time (German UI: `_reisezeit`,
`_jetzt_aktualisieren`; English UI: `_travel_time`, `_refresh_now`). Pick them from
**Developer tools → States** for your instance.

If you set an update interval, the button call becomes unnecessary – the sensor updates itself.

## Troubleshooting

| Symptom | Fix |
| :-- | :-- |
| *"Add-on is not reachable"* while adding a trip | The add-on is not running. **Settings → Add-ons → Travel Time → Start**, then retry. |
| Entities show `unavailable` | Check **Settings → System → Logs** for `traveltime`: the message names the exact cause (add-on, no coordinates, Google error). |
| Logo/icon missing in Home Assistant | HA serves brand images from `custom_components/traveltimefree/brand/` since 2026.3. Update the integration and restart; browsers cache brand images for up to 7 days. |
| Requests take a long time | A scrape needs 5–30 s. Do not poll more often than every 15 minutes; Google may throttle aggressive scraping. |
| Values are stale | Either press the refresh button, or set an update interval in the configuration. |

Diagnostics: **Settings → Devices & services → Travel Time → ⋮ → Download diagnostics** contains
the configuration, the last resolved endpoints and the last error.

## Known limitations

* Google Maps is scraped from the rendered page, not queried through an official API. If Google
  changes its markup, the add-on needs an update.
* Only *now* is supported – there is no "departure at 17:00" calculation.
* The add-on needs roughly 500 MB of disk space (Firefox + Playwright).

## Development

```bash
python3 -m pytest                      # integration unit tests (no Home Assistant needed)
python3 -m pytest addon/traveltime/tests   # add-on parser tests
python3 scripts/generate_brand_assets.py   # regenerate icon/logo (needs Pillow)
```

## License

See [License](License).
