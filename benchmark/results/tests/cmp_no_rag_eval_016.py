import genesis as gs

gs.init(backend=gs.cpu)

scene = gs.Scene(
    show_viewer=True,
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(0, 2, 5),
        camera_lookat=(0, 0, 0),
    ),
)

# Ground plane (rigid)
plane = scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid(),
)

# Soft bunny mesh (FEM elastic)
bunny = scene.add_entity(
    gs.morphs.Mesh(
        file='bunny.obj',           # place your bunny mesh here
        pos=(0, 1.5, 0),
        scale=0.2,
        euler=(0, 0, 0),
    ),
    material=gs.materials.FEM.Soft(
        E=1e5,
        nu=0.3,
        rho=1000,
    ),
    surface=gs.surfaces.Default(
        color=(0.8, 0.6, 0.4, 1.0),
    ),
)

scene.build()

for _ in range(500):
    scene.step()