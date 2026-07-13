import genesis as gs

gs.init()

dt = 2e-2
particle_size = 1e-2

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=dt,
        substeps=10,
    ),
    pbd_options=gs.options.PBDOptions(
        particle_size=particle_size,
    ),
    viewer_options=gs.options.ViewerOptions(),
    show_viewer=True,
)

# Static floor
plane = scene.add_entity(
    morph=gs.morphs.Plane(),
    material=gs.materials.Rigid(),
)

# Square cloth mesh
cloth = scene.add_entity(
    material=gs.materials.PBD.Cloth(),
    morph=gs.morphs.Mesh(
        file="meshes/grid20x20.obj",
        scale=0.5,
        pos=(0, 0, 0.5),
        euler=(0, 0, 0),
    ),
    surface=gs.surfaces.Default(color=(0.2, 0.6, 0.8, 1.0)),
)

scene.build(n_envs=0)

# Run simulation for a few seconds
for _ in range(200):
    scene.step()