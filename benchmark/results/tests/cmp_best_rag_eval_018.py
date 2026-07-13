import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=4e-3,
        substeps=10,
    ),
    mpm_options=gs.options.MPMOptions(
        lower_bound=(-1.0, -1.0, 0.0),
        upper_bound=(1.0, 1.0, 1.2),
    ),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(1.5, -1.5, 1.0),
        camera_lookat=(0.0, 0.0, 0.4),
    ),
    show_viewer=True,
)

# static ground plane
plane = scene.add_entity(gs.morphs.Plane())

# bathtub mesh as static rigid container
bathtub = scene.add_entity(
    gs.morphs.Mesh(
        file='meshes/bathtub.obj',   # replace with your bathtub mesh file
        pos=(0.0, 0.0, 0.05),
        euler=(0, 0, 0),
        scale=1.0,
        fixed=True,                   # makes the mesh static
        convexify=False,              # required for concave shapes like a bathtub
    ),
)

# MPM liquid emitter pouring from above
emitter = scene.add_emitter(
    material=gs.materials.MPM.Liquid(),
    max_particles=30000,
)
emitter.set_transform(pos=(0.0, 0.0, 1.0))  # position above the bathtub

scene.build()

# run the simulation for a few seconds to let the liquid pour
for _ in range(500):
    scene.step()