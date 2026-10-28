import tempfile
import unittest
from pathlib import Path
from kart_perception.baseline import Config, detect
from kart_perception.cli import load_points


class BaselineTests(unittest.TestCase):
    def test_synthetic_scene(self):
        boxes = detect(load_points("examples/synthetic_cloud.csv"))
        self.assertEqual(len(boxes), 2)
        self.assertEqual(boxes[0]["point_count"], 3)
        for actual, expected in zip(boxes[0]["center_m"], [4.1, 1.05, 0.5]):
            self.assertAlmostEqual(actual, expected)

    def test_transitive_cluster_across_cells(self):
        self.assertEqual(len(detect([(1, 0, .3), (1.5, 0, .3), (2, 0, .3)])), 1)

    def test_empty_noise_ground_and_nonfinite(self):
        self.assertEqual(detect([]), [])
        self.assertEqual(detect([(1, 0, 0), (-1, 0, .5), (2, 0, .5), (float("nan"), 0, .5)]), [])

    def test_configuration_rejects_invalid_values(self):
        for changes in ({"radius": 0}, {"min_z": 3}, {"max_x": float("inf")}):
            with self.assertRaises(ValueError):
                Config(**changes)

    def test_malformed_csv_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "bad.csv"
            for content in ("a,b,c\n1,2,3\n", "x,y,z\n1,nan,3\n", "x,y,z\n1,bad,3\n"):
                p.write_text(content)
                with self.assertRaises(ValueError):
                    load_points(p)


if __name__ == "__main__":
    unittest.main()
