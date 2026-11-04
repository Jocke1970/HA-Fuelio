"""Regression tests for HACS compatibility of release source trees."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class HacsMetadataTests(unittest.TestCase):
    def test_repository_metadata_present_and_valid(self):
        metadata_path = ROOT / "hacs.json"
        self.assertTrue(metadata_path.is_file(), "HACS requires hacs.json at the selected release ref")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        self.assertIsInstance(metadata, dict)
        self.assertEqual(metadata.get("name"), "Fuelio")

    def test_integration_layout_and_manifest(self):
        component = ROOT / "custom_components" / "fuelio"
        self.assertTrue((component / "__init__.py").is_file())
        self.assertTrue((component / "calendar.py").is_file(), "Fuelio must bundle its calendar platform")
        manifest = json.loads((component / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["domain"], "fuelio")
        self.assertTrue(manifest.get("config_flow"))
        self.assertIn("version", manifest)
        self.assertTrue(manifest.get("issue_tracker"))
        card = component / "www" / "ha-fuelio-card.js"
        mobile_card = component / "www" / "ha-fuelio-mobile-card.js"
        self.assertTrue(card.is_file(), "HACS release must bundle the Lovelace card")
        self.assertTrue(mobile_card.is_file(), "HACS release must bundle the mobile Lovelace card")
        init_text = (component / "__init__.py").read_text(encoding="utf-8")
        self.assertIn('PLATFORMS = ["sensor", "calendar"]', init_text)
        self.assertIn('FRONTEND_URL = "/fuelio/ha-fuelio-card.js"', init_text)
        self.assertIn('MOBILE_FRONTEND_URL = "/fuelio/ha-fuelio-mobile-card.js"', init_text)
        self.assertIn("async_register_static_paths", init_text)
        self.assertIn("cache_headers=False", init_text)
        self.assertIn("async def async_setup(hass: HomeAssistant, config: dict)", init_text)
        setup_entry_tail = init_text.split("async def async_setup_entry", 1)[1]
        self.assertNotIn("await _async_register_services(hass)", setup_entry_tail)
        services = (component / "services.yaml").read_text(encoding="utf-8")
        self.assertIn("calibrate_range:", services)
        self.assertIn("calibrate_fuel_left:", services)
        self.assertIn("fuel_left_l:", services)
        self.assertIn("consumption_l_per_100km:", services)
        self.assertIn("clear_range_calibration:", services)

    def test_bilingual_translation_contract(self):
        component = ROOT / "custom_components" / "fuelio"
        strings = json.loads((component / "strings.json").read_text(encoding="utf-8"))
        en = json.loads((component / "translations" / "en.json").read_text(encoding="utf-8"))
        sv = json.loads((component / "translations" / "sv.json").read_text(encoding="utf-8"))

        def shape(value):
            if isinstance(value, dict):
                return {key: shape(value[key]) for key in sorted(value)}
            return None

        self.assertEqual(shape(strings), shape(en))
        self.assertEqual(shape(en), shape(sv))
        self.assertIn("options", en)
        self.assertIn("enable_calendar", en["options"]["step"]["init"]["data"])
        self.assertIn("services", en)
        self.assertIn("calibrate_range", en["services"])
        self.assertIn("calibrate_fuel_left", en["services"])
        self.assertEqual(len(en["entity"]["sensor"]), 42)

        sensor_text = (component / "sensor.py").read_text(encoding="utf-8")
        self.assertEqual(sensor_text.count("translation_key="), 42)
        self.assertNotIn('FuelioSensorDescription(key="trip_count", name=', sensor_text)

    def test_calendar_option_defaults_on_and_is_reloadable(self):
        component = ROOT / "custom_components" / "fuelio"
        const_text = (component / "const.py").read_text(encoding="utf-8")
        flow_text = (component / "config_flow.py").read_text(encoding="utf-8")
        init_text = (component / "__init__.py").read_text(encoding="utf-8")
        self.assertIn('CONF_ENABLE_CALENDAR = "enable_calendar"', const_text)
        self.assertIn("DEFAULT_ENABLE_CALENDAR = True", const_text)
        self.assertIn("FuelioOptionsFlow", flow_text)
        self.assertIn("async_get_options_flow", flow_text)
        self.assertIn("entry.add_update_listener(_async_reload_entry)", init_text)
        self.assertIn("entry.options.get(CONF_ENABLE_CALENDAR, DEFAULT_ENABLE_CALENDAR)", init_text)


if __name__ == "__main__":
    unittest.main()
