"""Static contract checks; the actual Home Assistant runtime needs separate tests."""
from __future__ import annotations

from pathlib import Path
import unittest

COMPONENT = Path(__file__).resolve().parents[1] / "custom_components" / "fuelio"


class NamingContractTests(unittest.TestCase):
    def test_config_entry_does_not_use_vehicle_name(self):
        flow = (COMPONENT / "config_flow.py").read_text(encoding="utf-8")
        self.assertIn('title="Fuelio vehicle"', flow)
        self.assertNotIn("snapshot.vehicle_name", flow)

    def test_entity_ids_remain_stable(self):
        sensor = (COMPONENT / "sensor.py").read_text(encoding="utf-8")
        self.assertIn('f"{entry.entry_id}_{description.key}"', sensor)
        self.assertIn("identifiers={(DOMAIN, entry.entry_id)}", sensor)


if __name__ == "__main__":
    unittest.main()
