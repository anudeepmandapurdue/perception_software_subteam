"""Simple height crop and Euclidean connected components, in meters."""
from dataclasses import dataclass
from itertools import product
from math import floor, isfinite


@dataclass(frozen=True)
class Config:
    min_x: float = 0.0
    max_x: float = 30.0
    max_abs_y: float = 10.0
    min_z: float = 0.15
    max_z: float = 2.5
    radius: float = 0.6
    min_points: int = 3

    def __post_init__(self):
        if not all(isfinite(v) for v in (self.min_x, self.max_x, self.max_abs_y,
                                         self.min_z, self.max_z, self.radius)):
            raise ValueError("Configuration values must be finite")
        if (self.min_x >= self.max_x or self.min_z >= self.max_z
                or self.max_abs_y <= 0 or self.radius <= 0 or self.min_points < 1):
            raise ValueError("Invalid crop, cluster radius, or minimum point count")


def detect(points, config=Config()):
    """Points must already be in a ground-relative frame: x forward, y left, z up.

    Height cropping assumes flat ground at z=0; this is NOT plane fitting.
    Return unknown-class 3D axis-aligned boxes. No calibrated confidence or IDs.
    """
    kept = [tuple(p) for p in points if len(p) == 3 and all(isfinite(v) for v in p)
            and config.min_x <= p[0] <= config.max_x
            and abs(p[1]) <= config.max_abs_y
            and config.min_z <= p[2] <= config.max_z]
    def cell(p):
        return tuple(floor(v / config.radius) for v in p)
    buckets = {}
    for i, p in enumerate(kept):
        buckets.setdefault(cell(p), []).append(i)
    visited, detections = set(), []
    for seed in range(len(kept)):
        if seed in visited:
            continue
        visited.add(seed)
        stack, cluster = [seed], []
        while stack:
            i = stack.pop()
            p = kept[i]
            cluster.append(p)
            key = cell(p)
            for offset in product((-1, 0, 1), repeat=3):
                near = tuple(a + b for a, b in zip(key, offset))
                for j in buckets.get(near, ()):
                    if j not in visited and sum((a-b)**2 for a, b in zip(p, kept[j])) <= config.radius**2:
                        visited.add(j)
                        stack.append(j)
        if len(cluster) >= config.min_points:
            low = [min(p[k] for p in cluster) for k in range(3)]
            high = [max(p[k] for p in cluster) for k in range(3)]
            detections.append({"label": "unknown", "source": "lidar",
                               "center_m": [(a+b)/2 for a, b in zip(low, high)],
                               "size_m": [b-a for a, b in zip(low, high)],
                               "point_count": len(cluster)})
    return detections
