import gmsh
import json

from pathlib import Path

HERE = Path(__file__).resolve().parent
STEP = str(HERE / "../cad/mallet.hh.sat.stp")
OUT_DIR = str(HERE / "../viewer")

# calibrated so low/medium/high land around ~250 / ~1.2k / ~6.5k tets
LEVELS = {
    "low":    0.075,
    "medium": 0.033,
    "high":   0.017,
}

# (local i, local j, local k, local opposite) for the 4 faces of a tet
FACE_DEF = [(1, 2, 3, 0), (0, 2, 3, 1), (0, 1, 3, 2), (0, 1, 2, 3)]


def sub(p, q):
    return (p[0]-q[0], p[1]-q[1], p[2]-q[2])

def cross(u, v):
    return (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])

def dot(u, v):
    return u[0]*v[0]+u[1]*v[1]+u[2]*v[2]


def mesh_at(factor, label):
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.model.add(f"vol_{label}")
    gmsh.model.occ.importShapes(STEP)
    gmsh.model.occ.synchronize()

    xmin, ymin, zmin, xmax, ymax, zmax = gmsh.model.getBoundingBox(-1, -1)
    diag = ((xmax - xmin) ** 2 + (ymax - ymin) ** 2 + (zmax - zmin) ** 2) ** 0.5
    size = diag * factor

    gmsh.option.setNumber("Mesh.MeshSizeMin", size)
    gmsh.option.setNumber("Mesh.MeshSizeMax", size)
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    gmsh.option.setNumber("Mesh.Algorithm3D", 1)

    gmsh.model.mesh.generate(3)

    node_tags, node_coords, _ = gmsh.model.mesh.getNodes()
    tag_to_index = {tag: i for i, tag in enumerate(node_tags)}
    positions = [0.0] * (len(node_tags) * 3)
    for i in range(len(node_tags)):
        positions[3*i:3*i+3] = node_coords[3*i:3*i+3]

    def P(idx):
        return (positions[3*idx], positions[3*idx+1], positions[3*idx+2])

    etypes, etags, enodes_list = gmsh.model.mesh.getElements(3)
    tet_nodes = []  # flat, 4 indices per tet
    for etype, enodes in zip(etypes, enodes_list):
        if etype != 4:  # 4-node tetrahedron only
            continue
        for j in range(0, len(enodes), 4):
            tet_nodes.extend(tag_to_index[enodes[j+k]] for k in range(4))

    n_tets = len(tet_nodes) // 4

    centroids = [0.0] * (n_tets * 3)
    face_dict = {}  # sorted (a,b,c) -> list of (tetIndex, (a,b,c) oriented outward from that tet)

    for t in range(n_tets):
        n = tet_nodes[t*4:t*4+4]
        px = (P(n[0])[0] + P(n[1])[0] + P(n[2])[0] + P(n[3])[0]) / 4
        py = (P(n[0])[1] + P(n[1])[1] + P(n[2])[1] + P(n[3])[1]) / 4
        pz = (P(n[0])[2] + P(n[1])[2] + P(n[2])[2] + P(n[3])[2]) / 4
        centroids[t*3:t*3+3] = [px, py, pz]

        for (i, j, k, opp) in FACE_DEF:
            a, b, c = n[i], n[j], n[k]
            pa, pb, pc, po = P(a), P(b), P(c), P(n[opp])
            normal = cross(sub(pb, pa), sub(pc, pa))
            if dot(normal, sub(po, pa)) > 0:
                a, b, c = a, c, b  # flip winding so normal points away from opposite vertex
            key = tuple(sorted((a, b, c)))
            face_dict.setdefault(key, []).append((t, (a, b, c)))

    face_verts = []
    face_tetA = []
    face_tetB = []
    for key, entries in face_dict.items():
        if len(entries) == 1:
            tetA, tri = entries[0]
            tetB = -1
        elif len(entries) == 2:
            tetA, tri = entries[0]
            tetB, _ = entries[1]
        else:
            continue  # non-manifold face, skip defensively
        face_verts.extend(tri)
        face_tetA.append(tetA)
        face_tetB.append(tetB)

    gmsh.finalize()

    return {
        "level": label,
        "meshSize": size,
        "nodeCount": len(node_tags),
        "tetCount": n_tets,
        "faceCount": len(face_tetA),
        "positions": positions,
        "tetNodes": tet_nodes,
        "tetCentroids": centroids,
        "faceVerts": face_verts,
        "faceTetA": face_tetA,
        "faceTetB": face_tetB,
        "bbox": [xmin, ymin, zmin, xmax, ymax, zmax],
    }


results = {}
for label, factor in LEVELS.items():
    r = mesh_at(factor, label)
    print(f"{label}: nodes={r['nodeCount']} tets={r['tetCount']} faces={r['faceCount']} meshSize={r['meshSize']:.3f}")
    results[label] = r

with open(f"{OUT_DIR}/volume_data.json", "w") as f:
    json.dump(results, f)

print("done")
