import genesis as gs
import numpy as np

gs.init()

scene = gs.Scene(
    show_viewer=True,
    viewer_options=gs.options.ViewerOptions(
        res=(1280, 720),
        camera_fov=30,
        camera_pos=(3, 3, 3),
        camera_lookat=(0, 0, 0.3),
    ),
)

def create_bowl_mesh(R=0.5, H=0.3, segments=20):
    """Generate a cylinder with closed bottom, open top (bowl shape)."""
    n = segments
    vertices = []
    # bottom rim
    for i in range(n):
        angle = 2 * np.pi * i / n
        vertices.append([R * np.cos(angle), R * np.sin(angle), 0.0])
    # top rim
    for i in range(n):
        angle = 2 * np.pi * i / n
        vertices.append([R * np.cos(angle), R * np.sin(angle), H])
    # bottom center
    bottom_center = np.array([[0, 0, 0]])
    vertices = np.vstack([vertices, bottom_center])
    faces = []
    # bottom fan
    center_idx = len(vertices) - 1
    for i in range(n):
        j = (i + 1) % n
        faces.append([center_idx, i, j])
    # side walls (quads -> triangles)
    for i in range(n):
        j = (i + 1) % n
        a, b = i, j
        c, d = i + n, j + n
        faces.append([a, c, b])
        faces.append([b, c, d])
    return vertices, np.array(faces)

bowl_verts, bowl_faces = create_bowl_mesh(R=0.6, H=0.35, segments=30)
bowl = scene.add_entity(
    morph=gs.morphs.Mesh(vertices=bowl_verts, faces=bowl_faces),
    material=gs.materials.Rigid(fixed=True),
    collision_primitive='trimesh',
    surface=gs.surfaces.Default(color=(0.8, 0.8, 0.8, 1.0)),
)

# SPH fluid solver
sph = gs.fluid.SPH(scene)

# create a fluid body
fluid = gs.fluid.Fluid(sph)
scene.add(fluid)

# left stream: red liquid flowing from the left side inward and downward
emitter_left = gs.fluid.Emitter(
    fluid,
    shape='box',
    pos=(-0.4, 0.0, 0.7),
    vel=(2.0, 0.0, -2.0),
    rate=200,
    liquid_color=(1.0, 0.0, 0.0),
)
scene.add(emitter_left)

# right stream: blue liquid flowing from the right side inward and downward
emitter_right = gs.fluid.Emitter(
    fluid,
    shape='box',
    pos=(0.4, 0.0, 0.7),
    vel=(-2.0, 0.0, -2.0),
    rate=200,
    liquid_color=(0.0, 0.0, 1.0),
)
scene.add(emitter_right)

scene.build()

# run simulation for a few seconds (2000 steps at default dt)
for _ in range(2000):
    scene.step()