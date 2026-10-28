# Perception output contract

## Implemented offline LiDAR output version 0.1

The CLI writes one JSON object per input frame:

- `schema_version`: `0.1`.
- `timestamp_ns`: original cloud acquisition time in integer nanoseconds; caller must provide the correct clock and unit.
- `frame_id`: actual ground-relative coordinate frame of every box.
- `status`: `ok` means processing succeeded, not that the scene is safe or sensors are healthy.
- `input_point_count`: number of finite parsed input points before crop.
- `detections`: list of `label` (`unknown`), `source` (`lidar`), `center_m` and `size_m` arrays in x/y/z order, plus `point_count`.
- `timing_ms`: CSV load, detection, and their sum, excluding output serialization.
- `limitations`: explicit baseline constraints.

An empty detection list may mean no clusters survived filtering, an empty cloud, or missed objects. It is not a clearance command. Invalid input exits nonzero and writes no new result; an existing output file from an older run may remain, so consumers must check exit status and timestamps. No confidence, object velocity, track ID, or camera-derived class is estimated. Box orientation follows the input axes.

## Planned camera and fusion boundary

Camera detections should carry camera acquisition timestamp/frame ID, image size, pixel boxes `[xmin,ymin,xmax,ymax]`, label, score, and model version. They remain 2D observations until calibrated geometry supplies range. Store each sensor's original timestamp and association skew.

Initial fusion consumes independently produced detections plus verified calibration. Use projected LiDAR geometry to associate camera boxes; document ambiguity handling, positive-depth filtering, occlusion behavior and class thresholds. A camera non-detection must not delete a LiDAR obstacle. Unmatched camera detections have no assumed metric depth. Missing calibration or excessive skew means no association, with explicit degraded status rather than a fabricated fused result.

Before adding a controls adapter, agree on publication frame, acquisition/publication times, sensor availability, stale timeout, and validity semantics. Proposed future statuses include degraded and unavailable; these are not implemented in the current CLI. Perception publishes observations; planning and vehicle actuation belong to separate components.
