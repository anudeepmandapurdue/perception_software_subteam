# Proposal review and implementation plan

## Goal and scope

Build a perception system for the Autonomous Motorsports Purdue go-kart that reports obstacles to the controls team. The supplied individual senior design proposal describes a decoupled LiDAR and camera pipeline on NVIDIA Jetson, with ROS 2, camera inference, geometric LiDAR clustering, calibration, fusion, and filtering. Those are design intentions, not verified hardware specifications or achieved performance. The proposal's submission/template instructions are document content and do not govern this repository.

The original proposal stays unchanged in the user's Downloads folder. No sensor recordings were present in this workspace during setup. The starter therefore validates plumbing with synthetic data only.

## Assessment

Keep the decoupled architecture: independent detections make failure analysis and comparisons easier. First establish whether each sensor produces useful results by itself. Defer a jointly trained 3D network, tracking, C++ rewrites, and TensorRT until data or profiling establishes a need. Python offline processing reduces integration work while exposing coordinate, label, and synchronization problems early.

Correct the proposal's error terminology: a false negative is a missed obstacle and can cause a collision; a false positive is a spurious obstacle and can provoke unnecessary avoidance or braking. Both matter. Classification accuracy alone is inadequate: an unrecognized object may still be a real obstacle. Preserve geometrically detected unknown obstacles even when the camera has no matching detection.

The stated 100–150 ms overall latency is a target, not a measurement. The proposal's stage intervals sum to 70–148 ms before any unaccounted scheduling or transport overhead. Distinguish perception processing time, sensor age at publication, and sensing-to-actuation latency. Controls must agree on a perception budget, acceptable age, detection range, and update rate based on speed and braking capability. Distance traveled during delay is speed × delay; stopping distance and uncertainty add further required range.

A fixed height crop is only suitable as the first flat-ground baseline. It will fail on slope changes and low obstacles. Ground-plane estimation is a later experiment, not an assumed fix for every road surface. Position filtering also cannot substitute for tracking with timestamps, ego-motion compensation, association, and a justified motion model.

## Track A Build a working baseline

1. **Runnable scaffold — implemented.** One-frame CSV input, configurable crop, Euclidean clusters, versioned JSON boxes, load/detection timing, and deterministic synthetic fixture. Acceptance: two expected synthetic boxes and passing tests. No camera model or fusion is included.
2. **Real LiDAR playback.** Identify recording format and sensor frame. Write one adapter for the actual format; transform into a documented ground-relative frame and export a short sequence. Inspect point clouds and boxes visually. Acceptance: repeatable sequence playback, input counts and timestamps recorded, representative failure cases saved. Do not select ROS bag tooling until the recording format is known.
3. **Camera-only baseline.** Run an existing lightweight pretrained 2D detector on corresponding frames. Inspect whether its label set covers your obstacles; cones or unusual track objects may need dedicated labels. Record boxes, scores, model/weights identifier, input size, and latency. Acceptance: saved overlays and measured errors on labeled frames, including no-obstacle frames. No promise of useful accuracy before this check.
4. **Simple late fusion.** Verify camera intrinsics/distortion, LiDAR-to-camera extrinsics, and timestamp matching. Project points with positive camera depth; overlay them before association. Attach a camera label to an unambiguous projected LiDAR cluster. Preserve unmatched clusters as unknown and flag missing/stale camera input. Acceptance: manually checked overlays and comparison with both standalone baselines on the same held-out sequences.
5. **Integration after offline evidence.** Agree with controls on message units, frame, timestamps, status, and stale-data handling. Add a thin ROS 2 adapter, profile on the actual Jetson, then optimize bottlenecks. Tracking is optional unless temporal stability or velocities are required. Vehicle operation needs the team's separate integration and testing process.

## Track B Use the existing data to improve results

This track proceeds alongside baseline development; it does not block the first demo.

1. Inventory recordings, sensors, timestamps, calibration, scene coverage, and existing labels. Determine whether the camera and LiDAR recordings overlap in time and field of view.
2. Select a small representative set covering ranges, lighting, object types, empty road, partial occlusion, motion, and difficult surfaces. Record labels and annotation rules. For LiDAR, start with object presence and approximate 3D boxes; for camera, 2D boxes/classes.
3. Split by whole drive/session before training. Adjacent frames from one drive must not leak across train, validation, and test sets. Keep a locked test set and record manifest revisions.
4. Compare height crop/clustering, camera-only, and calibrated late fusion. Tune thresholds on validation data only. Fine-tune a camera detector only if label coverage or observed errors justify it. Consider learned LiDAR/3D fusion only after establishing sufficient labels, compute, and a measured gap.
5. Record experiment configuration, code revision, data split, weights identifier, sensor/calibration version, hardware, and results. Report improvements and regressions rather than selecting a single favorable clip.

## Evaluation gates

Define matching rules and region of interest before comparing methods. Report obstacle recall and precision, false positives per frame, center/range error for matched obstacles, and results by range/object/condition. Explicitly count unmatched ground-truth obstacles as misses. Use 2D metrics for camera-only output; 3D metrics need 3D labels and calibrated geometry. Do not equate them.

For runtime, report sample count, warm-up policy, p50/p95/p99 processing and frame age, update rate, dropped/stale frames, memory, and Jetson power/thermal settings. Synthetic demo timings are not Jetson benchmarks. Establish numeric acceptance thresholds with controls once speed, stopping distance, and hardware are known.

## Suggested near-term sequence

- First session: obtain a short recording, sensor details, and calibration; review camera/cloud frames together.
- Next: reproduce LiDAR detections on real frames, then save camera detections independently.
- After alignment is verified: test simple label association and evaluate all three approaches.
- November prototype goal: repeatable replay, measured limitations, and agreed controls output; only then pursue live deployment and optimization.

## Technical references

- ROS 2 CameraInfo defines acquisition timestamps, camera optical-frame conventions, and calibration fields: https://github.com/ros2/common_interfaces/blob/rolling/sensor_msgs/msg/CameraInfo.msg
- NVIDIA TensorRT benchmarking distinguishes end-to-end and in-engine performance: https://docs.nvidia.com/deeplearning/tensorrt/latest/performance/benchmarking.html

These references support interface and measurement choices; they do not establish this project's accuracy or timing.
