import csv
import tempfile
import unittest
from pathlib import Path

from kart_perception.ingestion import load_camera, load_lidar, replay


class IngestionTests(unittest.TestCase):
    def test_lidar_preserves_points_and_metadata(self):
        frame = load_lidar('examples/synthetic_cloud.csv', 123, 'lidar')
        self.assertEqual(frame.timestamp_ns, 123)
        self.assertEqual(frame.frame_id, 'lidar')
        self.assertEqual(len(frame.points), 9)
        self.assertEqual(frame.points[0], (2, 0, 0))

    def test_camera_pixels(self):
        frame = load_camera('examples/synthetic_camera.ppm', 456, 'camera_optical')
        self.assertEqual((frame.width, frame.height), (4, 2))
        self.assertEqual(len(frame.rgb), 24)
        self.assertEqual(frame.rgb[3:6], bytes([255, 128, 0]))
        self.assertEqual(frame.timestamp_ns, 456)

    def test_pairing_and_skew_limit(self):
        pairs = list(replay('examples/paired_manifest.csv', 10_000_000))
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0][1].timestamp_ns - pairs[0][0].timestamp_ns, 10_000_000)
        with self.assertRaises(ValueError):
            list(replay('examples/paired_manifest.csv', 9_999_999))

    def test_metadata_and_invalid_image(self):
        with self.assertRaises(ValueError):
            load_lidar('examples/synthetic_cloud.csv', -1, 'lidar')
        with self.assertRaises(ValueError):
            load_camera('examples/synthetic_camera.ppm', 0, '')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'bad.png'
            path.write_text('not an image')
            with self.assertRaises(OSError):
                load_camera(path, 0, 'camera')

    def test_rejects_duplicate_timestamps_and_missing_fields(self):
        with open('examples/paired_manifest.csv', newline='') as stream:
            reader = csv.DictReader(stream)
            fields, row = reader.fieldnames, next(reader)
        row['lidar_path'] = str(Path('examples/synthetic_cloud.csv').resolve())
        row['camera_path'] = str(Path('examples/synthetic_camera.ppm').resolve())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'manifest.csv'
            for rows in ([row, row], [{**row, 'camera_path': ''}]):
                with path.open('w', newline='') as stream:
                    writer = csv.DictWriter(stream, fieldnames=fields)
                    writer.writeheader()
                    writer.writerows(rows)
                with self.assertRaises(ValueError):
                    list(replay(path, 10_000_000))
