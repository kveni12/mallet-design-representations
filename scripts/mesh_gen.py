import gmsh
import json

from pathlib import Path

HERE = Path(__file__).resolve().parent
STEP = str(HERE / "../cad/mallet.hh.sat.stp")
OUT_DIR = str(HERE / "../viewer")
STL_DIR = str(HERE / "../stl")

LEVELS = {
    "low":    0.12,
    "medium": 0.045,
    "high":   0.015,
}

def mesh_at(factor, label):
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.model.add(label)
    gmsh.model.occ.importShapes(STEP)
    gmsh.model.occ.synchronize()

    xmin, ymin, zmin, xmax, ymax, zmax = gmsh.model.getBoundingBox(-1, -1)
    diag = ((xmax - xmin) ** 2 + (ymax - ymin) ** 2 + (zmax - zmin) ** 2) ** 0.5
    size = diag * factor

    gmsh.option.setNumber("Mesh.MeshSizeMin", size)
    gmsh.option.setNumber("Mesh.MeshSizeMax", size)
    gmsh.option.setNumber("Mesh.Algorithm", 6)

    gmsh.model.mesh.generate(2)

    node_tags, node_coords, _ = gmsh.model.mesh.getNodes()
    tag_to_index = {tag: i for i, tag in enumerate(node_tags)}
    positions = [0.0] * (len(node_tags) * 3)
    for i in range(len(node_tags)):
        positions[3*i:3*i+3] = node_coords[3*i:3*i+3]

    indices = []
    surface_ids = []  # one entry per triangle: the geometric surface tag it belongs to
    surfaces = gmsh.model.getEntities(2)

    for (dim, surf_tag) in surfaces:
        etypes, etags, enodes_list = gmsh.model.mesh.getElements(2, surf_tag)
        for etype, enodes in zip(etypes, enodes_list):
            if etype == 2:  # 3-node triangle
                for j in range(0, len(enodes), 3):
                    a, b, c = enodes[j], enodes[j+1], enodes[j+2]
                    indices.extend([tag_to_index[a], tag_to_index[b], tag_to_index[c]])
                    surface_ids.append(surf_tag)
            elif etype == 3:  # 4-node quad -> split into 2 tris, same surface id
                for j in range(0, len(enodes), 4):
                    a, b, c, d = enodes[j], enodes[j+1], enodes[j+2], enodes[j+3]
                    ia, ib, ic, idd = tag_to_index[a], tag_to_index[b], tag_to_index[c], tag_to_index[d]
                    indices.extend([ia, ib, ic, ia, ic, idd])
                    surface_ids.extend([surf_tag, surf_tag])

    n_nodes = len(node_tags)
    n_tris = len(indices) // 3

    stl_path = f"{STL_DIR}/mallet_{label}.stl"
    gmsh.write(stl_path)

    gmsh.finalize()

    return {
        "level": label,
        "meshSize": size,
        "nodeCount": n_nodes,
        "triCount": n_tris,
        "surfaceCount": len(surfaces),
        "positions": positions,
        "indices": indices,
        "surfaceIds": surface_ids,
        "bbox": [xmin, ymin, zmin, xmax, ymax, zmax],
    }

results = {}
for label, factor in LEVELS.items():
    r = mesh_at(factor, label)
    print(f"{label}: nodes={r['nodeCount']} tris={r['triCount']} surfaces={r['surfaceCount']} meshSize={r['meshSize']:.3f}")
    results[label] = r

with open(f"{OUT_DIR}/mesh_data.json", "w") as f:
    json.dump(results, f)

print("done")
