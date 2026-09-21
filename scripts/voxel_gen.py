import trimesh
import json

from pathlib import Path

HERE = Path(__file__).resolve().parent
STL = str(HERE / "../stl/mallet_high.stl")
OUT_DIR = str(HERE / "../viewer")

# calibrated so low/medium/high land around ~170 / ~1.3k / ~5.7k voxels
LEVELS = {
    "low":    16,
    "medium": 7,
    "high":   4,
}

mesh = trimesh.load(STL)
assert mesh.is_watertight, "mesh must be watertight to fill a solid voxel grid"

bounds = mesh.bounds  # [[xmin,ymin,zmin],[xmax,ymax,zmax]]
bbox = [bounds[0][0], bounds[0][1], bounds[0][2], bounds[1][0], bounds[1][1], bounds[1][2]]

results = {}
for label, pitch in LEVELS.items():
    vg = mesh.voxelized(pitch=pitch).fill()
    centers = vg.points  # (N,3) world-space voxel centers, solid interior included
    flat = centers.reshape(-1).tolist()
    results[label] = {
        "level": label,
        "pitch": pitch,
        "voxelCount": int(centers.shape[0]),
        "centers": flat,
        "bbox": bbox,
    }
    print(f"{label}: pitch={pitch} voxels={centers.shape[0]}")

with open(f"{OUT_DIR}/voxel_data.json", "w") as f:
    json.dump(results, f)

print("done")
