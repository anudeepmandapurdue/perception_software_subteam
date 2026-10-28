# Autonomous Go Kart Perception

An offline starting point for Anudeep Manda's Autonomous Motorsports Purdue senior design project: detect obstacles with LiDAR and computer vision and provide usable observations to the controls team.

The first executable baseline uses **LiDAR only**: crop points by position and height, cluster nearby points, and emit unknown-class 3D bounding boxes. It requires no model weights, GPU, ROS installation, or third-party runtime packages. It is a reference implementation for experiments, not a validated driving system. Camera inference, calibration, sensor fusion, tracking, and ROS integration are planned and are not implemented.

## Ingest LiDAR and camera recordings

The ingestion layer loads LiDAR points and decoded camera RGB pixels together, without running detection. Install the camera dependency, then replay the supplied synthetic pair:

```bash
python3 -m pip install -e '.[ingestion]'
PYTHONPATH=src python3 -m kart_perception.ingest examples/paired_manifest.csv --max-skew-ms 50 --output outputs/ingestion.jsonl
```

Use `examples/paired_manifest.csv` as the template for your own data. Paths are relative to the manifest file. Each row specifies one LiDAR CSV and one camera image, their original acquisition timestamps in nanoseconds, and their coordinate frame IDs. PNG, JPEG, and other Pillow-supported images decode to RGB. This currently supports saved frames, not video streams, live hardware, ROS bags, or native LiDAR binary formats.

The Python `replay()` iterator in `src/kart_perception/ingestion.py` yields a `LidarFrame` containing XYZ points and a `CameraFrame` containing RGB pixels. The CLI writes metadata summaries as JSONL rather than copying sensor payloads. Both timestamps must already use the same clock; the skew check does not synchronize sensors. Input coordinates are preserved without calibration or transformation. Unlike the detection baseline, ingestion itself does not require a ground-relative frame.

The demo image is an artificial 4×2 pixel fixture, not track imagery. Ingestion is working when the output reports 9 LiDAR points, a 4×2 RGB image, and 10,000,000 ns skew. Empty clouds are retained with point count zero. Missing or corrupt files, missing fields, excessive skew, and non-increasing timestamps fail explicitly. Output is replaced only after the complete replay succeeds; a failed run leaves any previous output unchanged, so check the command exit code.

## Run the baseline

From this repository, with Python 3.10 or newer:

```bash
PYTHONPATH=src python3 -m kart_perception.cli examples/synthetic_cloud.csv --timestamp-ns 0 --frame-id demo_ground --config examples/baseline.json --output outputs/demo.json
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

The demo contains synthetic points, ground, isolated noise, and two obstacle clusters. Expect two detections; this checks plumbing, not real-world detection accuracy. Timestamp zero is a synthetic fixture value only. Output timing measures CSV loading and detection on your computer, excluding acquisition, queues, camera inference, transport, and actuation.

Optional installation in a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
kart-perception --help
```

## Use a real recording

Keep original recordings outside Git or in ignored `data/raw/`. Convert one point-cloud frame to CSV with `x,y,z` columns in meters. The current detector requires **x forward, y left, z up, with flat ground at z=0**. Raw LiDAR coordinates generally need a measured rigid transformation before use. Do not simply rename the frame. Set the original acquisition timestamp and actual frame name when running the CLI. Configure the crop using `examples/baseline.json` as a starting point.

The height cutoff is a deliberately simple ground filter. Slopes, mounting errors, distant sparse returns, low obstacles, and connected objects can defeat it. Cluster boxes bound observed returns, not full object extents. Unknown class is intentional; point count is not a confidence score. Dense clouds can still be expensive despite spatial buckets.

## Project map

- `src/kart_perception/`: baseline detector, CSV reader, and CLI.
- `examples/`: small committed synthetic fixtures and configuration.
- `tests/`: meaningful behavior and invalid-input checks.
- `docs/PLAN.md`: proposal review and staged implementation plan.
- `docs/DATA.md`: data inventory, alignment, and evaluation requirements.
- `docs/INTERFACES.md`: current output contract and planned camera/fusion interface.
- `data/raw/`, `data/processed/`, `outputs/`: ignored local artifacts.

Start with the [plan](docs/PLAN.md), then complete the [data inventory](docs/DATA.md) using a short real recording. This repository does not issue steering, throttle, or braking commands.
