# Data inventory and experiments

## Details needed from the recordings

Record the following before writing a format adapter:

| Item | Current knowledge |
| --- | --- |
| LiDAR model, firmware, channels, scan rate | Unknown |
| Camera model, lens, resolution, frame rate | Unknown |
| Jetson model, JetPack and available resources | Proposal names Jetson; details unknown |
| Recording format and location | User has data; not supplied in workspace |
| Timestamp unit, clock source and synchronization | Unknown |
| Intrinsics and distortion model | Unknown |
| Rigid LiDAR-to-camera transform and mounting height | Unknown |
| Labels and obstacle classes | Unknown |
| Controls interface, speed and stopping requirements | Unknown |

Preserve originals. Keep bulky recordings and weights out of Git. Record checksums, collection date, session IDs, conversion commands, and ownership/access constraints in a local inventory. Avoid committing identifiable camera imagery without checking team sharing expectations.

## Initial interchange formats

LiDAR CSV: one frame per file with `x,y,z` float columns in meters. Additional columns are ignored by the initial reader. Points must already be transformed into the declared ground-relative frame. Malformed and nonfinite coordinates are rejected by the CLI; an empty well-formed file produces an empty result, which does not prove free space.

`examples/manifest.csv` shows a planned sequence index: session ID, split, relative LiDAR path and acquisition timestamp in integer nanoseconds, camera path and acquisition timestamp, and calibration ID. The current CLI reads one cloud; it does not consume this manifest. The example contains no camera data. Never infer synchronization from filenames alone. Preserve individual sensor timestamps, clock offsets and uncertainty. Set the permitted matching skew based on measured sensor rates and motion; reject or flag pairs outside that limit.

Calibration records should include camera matrix, image size, distortion model/coefficients, transform direction (e.g. `T_camera_lidar` maps LiDAR points into camera optical coordinates), units, axes, measurement method, and version. Validate transforms with overlays across near/far targets and the full image; reject points behind the camera. Raw images require the distortion model or consistent rectification. The ground-relative frame used by this baseline differs from camera optical coordinates.

## Experiment record template

```text
Experiment ID:
Git revision:
Dataset/manifest revision and session split:
Calibration revision:
Method and configuration:
Model weights identifier/checksum (if used):
Hardware/runtime/power settings:
Labeling and matching rules:
Number of frames/objects:
Recall / precision / false positives per frame:
Localization error and range breakdown:
Latency p50 / p95 / p99 and frame age:
Failures and next experiment:
```

Do not treat synthetic data as an evaluation set. Start with hand-reviewed real frames and expand coverage before making general performance claims.
