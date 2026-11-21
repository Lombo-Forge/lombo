"""Run with: python3 -m unittest discover -s tests"""

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("check_manifest", ROOT / "scripts" / "check-manifest.py")
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

GOOD_VERSION = {
    "version": "1.0.0.0",
    "changelog": "x",
    "targetAbi": "12.4.0.0",
    "sourceUrl": "https://github.com/Lombo-Forge/x/releases/download/v1/x.zip",
    "checksum": "0" * 32,
    "timestamp": "2026-01-01T00:00:00Z",
}


def plugin(**over):
    base = {"guid": "6f1c2a54-3b7d-4e0a-9c85-2d41a7e0b913", "name": "P", "description": "d", "overview": "o",
            "owner": "Lombo-Forge", "category": "General", "versions": []}
    return {**base, **over}


class ManifestTests(unittest.TestCase):
    def test_real_manifest_is_valid(self):
        self.assertEqual(mod.problems(json.loads((ROOT / "manifest.json").read_text())), [])

    def test_good_version_passes(self):
        self.assertEqual(mod.problems([plugin(versions=[GOOD_VERSION])]), [])

    def test_bad_values_are_named(self):
        bad = {**GOOD_VERSION, "version": "1.0", "checksum": "REPLACE", "sourceUrl": "http://x", "timestamp": "soon"}
        text = " ".join(mod.problems([plugin(versions=[bad])]))
        for word in ("four numbers", "MD5", "Lombo-Forge release", "ISO 8601"):
            self.assertIn(word, text)

    def test_structure_errors(self):
        self.assertTrue(mod.problems({}))
        self.assertTrue(mod.problems([plugin(guid="nope")]))
        self.assertTrue(mod.problems([plugin(), plugin()]))
        self.assertTrue(mod.problems([{"name": "x"}]))

    def test_odd_input_is_reported_not_raised(self):
        self.assertIn("must be an object", " ".join(mod.problems([plugin(versions=["x", 3, None])])))
        self.assertIn("must be a list", " ".join(mod.problems([plugin(versions="x")])))
        self.assertTrue(mod.problems([plugin(versions=[{}])]))
        self.assertTrue(mod.problems([None, 5, "x"]))

    def test_target_abi_and_zip_are_checked(self):
        bad = {**GOOD_VERSION, "targetAbi": "12.x", "sourceUrl": "https://github.com/Lombo-Forge/x/releases/x.tar"}
        text = " ".join(mod.problems([plugin(versions=[bad])]))
        self.assertIn("targetAbi", text)
        self.assertIn("end in .zip", text)


if __name__ == "__main__":
    unittest.main()
