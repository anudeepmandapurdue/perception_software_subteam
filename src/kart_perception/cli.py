"""Replay one CSV point cloud and emit a versioned JSON record."""
import argparse
import csv
import json
from math import isfinite
from pathlib import Path
from time import perf_counter
from .baseline import Config, detect


def load_points(path):
    with Path(path).open(newline="") as stream:
        reader = csv.DictReader(stream)
        if not {"x", "y", "z"}.issubset(reader.fieldnames or []):
            raise ValueError("Point CSV needs x,y,z columns in meters")
        points = []
        for line, row in enumerate(reader, start=2):
            try:
                p = tuple(float(row[k]) for k in ("x", "y", "z"))
            except (ValueError, TypeError) as exc:
                raise ValueError(f"Invalid coordinate at CSV line {line}") from exc
            if not all(isfinite(v) for v in p):
                raise ValueError(f"Nonfinite coordinate at CSV line {line}")
            points.append(p)
        return points


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cloud", type=Path)
    parser.add_argument("--timestamp-ns", type=int, required=True,
                        help="Original sensor acquisition timestamp, not replay time")
    parser.add_argument("--frame-id", required=True, help="Ground-relative input coordinate frame")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.timestamp_ns < 0 or not args.frame_id.strip():
            raise ValueError("Timestamp must be nonnegative and frame ID nonempty")
        config = Config(**json.loads(args.config.read_text())) if args.config else Config()
        start = perf_counter()
        points = load_points(args.cloud)
        loaded = perf_counter()
        obstacles = detect(points, config)
        finished = perf_counter()
        record = {"schema_version": "0.1", "timestamp_ns": args.timestamp_ns,
                  "frame_id": args.frame_id, "status": "ok", "input_point_count": len(points),
                  "detections": obstacles,
                  "timing_ms": {"load": (loaded-start)*1000,
                                "detection": (finished-loaded)*1000,
                                "load_and_detection": (finished-start)*1000},
                  "limitations": ["flat_ground_height_crop", "no_camera_fusion", "offline_only"]}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(record, indent=2, allow_nan=False) + "\n")
        print(f"Wrote {len(obstacles)} obstacle(s) to {args.output}")
    except (ValueError, TypeError, OSError) as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    main()
