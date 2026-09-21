# Mallet — Design Representations I: Data Structures

Four representations of one part — a mallet from the NIST Engineering Design
Model Repository (`CMU/Tools/mallet.hh.sat.stp`) — each with low/medium/high
resolution levels:

- **B-rep surface mesh** (gmsh, triangulated boundary, tagged per geometric surface)
- **Tetrahedral volume mesh** (gmsh, with a slice-plane cutaway)
- **Voxel grid** (trimesh `voxelized().fill()`, solid/opaque, sliceable)
- **Implicit signed-distance field** (trimesh `signed_distance` + `skimage.measure.marching_cubes`, with an erode/dilate iso-surface slider)

## Contents

- `cad/mallet.hh.sat.stp` — the original CAD source used for every representation below
- `stl/` — triangulated exports of the surface mesh (low/medium/high), used as the input solid for the voxel and SDF pipelines
- `scripts/` — the four generation scripts (gmsh + trimesh + scikit-image)
- `viewer/mallet_mesh_viewer.html` — the interactive Three.js viewer, plus the JSON data each script produces

## Running the viewer

Browsers block `fetch()` on local `file://` pages, so serve the folder instead of
double-clicking the HTML:

```bash
cd viewer
python3 -m http.server 8000
```

Then open `http://localhost:8000/mallet_mesh_viewer.html`.

## Regenerating the data

```bash
pip install gmsh trimesh scipy rtree scikit-image numpy
python3 scripts/mesh_gen.py          # -> viewer/mesh_data.json, stl/*.stl
python3 scripts/volume_mesh_gen.py   # -> viewer/volume_data.json
python3 scripts/voxel_gen.py         # -> viewer/voxel_data.json
python3 scripts/sdf_gen.py           # -> viewer/sdf_data.json
```
