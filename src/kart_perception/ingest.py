"""Replay paired LiDAR CSVs and camera images and write ingestion summaries."""
import argparse
import json
import os
from pathlib import Path
import tempfile

from .ingestion import replay


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--max-skew-ms", type=float, default=50.0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    temporary = None
    try:
        import math
        if not math.isfinite(args.max_skew_ms) or args.max_skew_ms < 0:
            raise ValueError("Maximum skew must be finite and nonnegative")
        if args.output.resolve() == args.manifest.resolve():
            raise ValueError("Output cannot overwrite the input manifest")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        count = 0
        with tempfile.NamedTemporaryFile(mode="w", dir=args.output.parent, delete=False) as stream:
            temporary = Path(stream.name)
            for lidar, camera in replay(args.manifest, int(args.max_skew_ms * 1_000_000)):
                record = {"schema_version": "0.1", "status": "ingested",
                          "lidar": {"timestamp_ns": lidar.timestamp_ns, "frame_id": lidar.frame_id,
                                    "point_count": len(lidar.points)},
                          "camera": {"timestamp_ns": camera.timestamp_ns, "frame_id": camera.frame_id,
                                     "width": camera.width, "height": camera.height,
                                     "encoding": "rgb8", "decoded_bytes": len(camera.rgb)},
                          "skew_ns": camera.timestamp_ns - lidar.timestamp_ns}
                stream.write(json.dumps(record) + "\n")
                count += 1
            if not count:
                raise ValueError("Manifest has no sensor pairs")
        os.replace(temporary, args.output)
        print(f"Ingested {count} LiDAR/camera pair(s); summary: {args.output}")
    except (ValueError, TypeError, OSError, RuntimeError) as exc:
        parser.exit(2, f"error: {exc}\n")
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
