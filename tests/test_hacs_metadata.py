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
        manifest = json.loads((component / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["domain"], "fuelio")
        self.assertTrue(manifest.get("config_flow"))
        self.assertIn("version", manifest)
        self.assertTrue(manifest.get("issue_tracker"))


if __name__ == "__main__":
    unittest.main()
