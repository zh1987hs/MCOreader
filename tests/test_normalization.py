import pathlib
import sys
import unittest

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from enzyme_miner.normalization.substrate import DEFAULT_SUBSTRATE_DICT, normalize_substrate
from enzyme_miner.normalization.units import normalize_value


class TestNormalization(unittest.TestCase):
    def test_substrate_normalizer(self):
        result = normalize_substrate("ABTS", DEFAULT_SUBSTRATE_DICT)
        self.assertEqual(result.normalized, "ABTS")
        self.assertEqual(result.category, "dye")
        self.assertEqual(result.warnings, [])

    def test_unit_normalization_kcat(self):
        result = normalize_value("kcat", 60.0, "min^-1")
        self.assertAlmostEqual(result.value, 1.0)
        self.assertEqual(result.unit_normalized, "s^-1")

    def test_unit_normalization_km(self):
        result = normalize_value("Km", 10.0, "mM")
        self.assertAlmostEqual(result.value, 0.01)
        self.assertEqual(result.unit_normalized, "M")


if __name__ == "__main__":
    unittest.main()
