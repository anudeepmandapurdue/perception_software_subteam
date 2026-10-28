"""Load recorded LiDAR and camera frames without performing detection or fusion."""
from dataclasses import dataclass
from pathlib import Path
import csv

from .cli import load_points


@dataclass(frozen=True)
class LidarFrame:
    timestamp_ns: int
    frame_id: str
    points: list[tuple[float, float, float]]


@dataclass(frozen=True)
class CameraFrame:
    timestamp_ns: int
    frame_id: str
    width: int
    height: int
    rgb: bytes  # Row-major RGB uint8: height * width * 3 bytes.


def _validate_metadata(timestamp_ns, frame_id):
    if not isinstance(timestamp_ns, int) or timestamp_ns < 0:
        raise ValueError("Acquisition timestamp must be a nonnegative integer in nanoseconds")
    if not frame_id.strip():
        raise ValueError("A sensor coordinate frame ID is required")


def load_lidar(path, timestamp_ns, frame_id):
    """Read x,y,z CSV in meters; retain input coordinates without transforming them."""
    _validate_metadata(timestamp_ns, frame_id)
    return LidarFrame(timestamp_ns, frame_id, load_points(path))


def load_camera(path, timestamp_ns, frame_id):
    """Decode a recorded image into RGB pixels, retaining its acquisition timestamp."""
    _validate_metadata(timestamp_ns, frame_id)
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Camera ingestion requires Pillow: pip install -e '.[ingestion]'") from exc
    with Image.open(path) as image:
        image.load()
        rgb = image.convert("RGB")
        return CameraFrame(timestamp_ns, frame_id, rgb.width, rgb.height, rgb.tobytes())


def replay(manifest, max_skew_ns):
    """Yield explicitly paired frames in manifest order; reject excessive clock skew.

    Paths are relative to the manifest. Timestamps must already share a clock.
    This checks declared pairs; it does not estimate synchronization or calibration.
    """
    if max_skew_ns < 0:
        raise ValueError("Maximum timestamp skew must be nonnegative")
    manifest = Path(manifest)
    required = {"lidar_path", "lidar_timestamp_ns", "lidar_frame_id",
                "camera_path", "camera_timestamp_ns", "camera_frame_id"}
    with manifest.open(newline="") as stream:
        reader = csv.DictReader(stream)
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("Manifest requires columns: " + ", ".join(sorted(required)))
        previous = None
        for line, row in enumerate(reader, 2):
            try:
                if any(not row.get(key, "").strip() for key in required):
                    raise ValueError("Both sensor paths, timestamps, and frame IDs are required")
                lidar_time = int(row["lidar_timestamp_ns"])
                camera_time = int(row["camera_timestamp_ns"])
                _validate_metadata(lidar_time, row["lidar_frame_id"])
                _validate_metadata(camera_time, row["camera_frame_id"])
                if previous is not None and (lidar_time <= previous[0] or camera_time <= previous[1]):
                    raise ValueError("Each sensor's timestamps must strictly increase")
                if abs(lidar_time - camera_time) > max_skew_ns:
                    raise ValueError("Sensor timestamp skew exceeds the configured limit")
                lidar = load_lidar(manifest.parent / row["lidar_path"], lidar_time, row["lidar_frame_id"])
                camera = load_camera(manifest.parent / row["camera_path"], camera_time, row["camera_frame_id"])
                previous = lidar_time, camera_time
            except (ValueError, TypeError, OSError) as exc:
                raise ValueError(f"Manifest line {line}: {exc}") from exc
            yield lidar, camera
