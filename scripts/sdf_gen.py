import trimesh
import numpy as np
from skimage import measure
import json
import time

from pathlib import Path

HERE = Path(__file__).resolve().parent
STL = str(HERE / "../stl/mallet_high.stl")
OUT_DIR = str(HERE / "../viewer")

# grid resolution (samples per axis) for the dense SDF grid, per level
GRID_N = {
    "low":    20,
    "medium": 32,
    "high":   44,
}

# iso-offset levels the slider steps through (trimesh convention: signed_distance
# is POSITIVE inside, NEGATIVE outside — so level>0 eats inward (erode),
# level<0 grows outward (dilate))
ISO_MIN, ISO_MAX, ISO_STEPS = -15.0, 18.0, 13
ISO_LEVELS = list(np.linspace(ISO_MIN, ISO_MAX, ISO_STEPS))

mesh = trimesh.load(STL)
bounds = mesh.bounds
pad = 0.12 * float(max(bounds[1] - bounds[0]))
lo = bounds[0] - pad
hi = bounds[1] + pad
bbox = [float(lo[0]), float(lo[1]), float(lo[2]), float(hi[0]), float(hi[1]), float(hi[2])]

results = {}
for label, n in GRID_N.items():
    xs = np.linspace(lo[0], hi[0], n)
    ys = np.linspace(lo[1], hi[1], n)
    zs = np.linspace(lo[2], hi[2], n)
    spacing = (xs[1] - xs[0], ys[1] - ys[0], zs[1] - zs[0])
    X, Y, Z = np.meshgrid(xs, ys, zs, indexing="ij")
    pts = np.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=1)

    t0 = time.time()
    sd = trimesh.proximity.signed_distance(mesh, pts).reshape(n, n, n)
    grid_time = time.time() - t0

    levels_out = []
    for iso in ISO_LEVELS:
        if sd.max() <= iso or sd.min() >= iso:
            levels_out.append({"iso": float(iso), "triCount": 0, "positions": [], "indices": []})
            continue
        try:
            verts, faces, _, _ = measure.marching_cubes(sd, level=float(iso), spacing=spacing)
        except (ValueError, RuntimeError):
            levels_out.append({"iso": float(iso), "triCount": 0, "positions": [], "indices": []})
            continue
        verts = verts + lo  # index-space (already spacing-scaled) -> world space
        levels_out.append({
            "iso": float(iso),
            "triCount": int(faces.shape[0]),
            "positions": verts.reshape(-1).astype(float).tolist(),
            "indices": faces.reshape(-1).astype(int).tolist(),
        })

    results[label] = {
        "level": label,
        "gridN": n,
        "gridTime": grid_time,
        "isoLevels": levels_out,
        "bbox": bbox,
    }
    tri_counts = [lv["triCount"] for lv in levels_out]
    print(f"{label}: grid={n}^3 grid_time={grid_time:.2f}s tri range=({min(tri_counts)}..{max(tri_counts)})")

with open(f"{OUT_DIR}/sdf_data.json", "w") as f:
    json.dump(results, f)

print("done")
