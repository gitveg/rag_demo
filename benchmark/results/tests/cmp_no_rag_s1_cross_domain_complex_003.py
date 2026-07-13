import genesis as gs

gs.init(backend=gs.cpu)

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=0.01,
        gravity=(0, 0, -9.81),
    ),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(5, 5, 5),
        camera_lookat=(0, 0, 1.0),
    ),
    show_viewer=True,
)

drone = scene.add_entity(
    gs.morphs.Drone(
        file="urdf/drones/cf2x.urdf",
        model="CF2X",
    ),
    pos=(0, 0, 1.0),
)

terrain = scene.add_entity(
    gs.morphs.Terrain(
        method="fractal_terrain",
    ),
    pos=(0, 0, 0),
)

wind = scene.add_force_field(
    gs.forces.WindField(
        direction=(1, 0, 0),
        magnitude=1.5,
        turbulence_intensity=0.3,
    ),
)

scene.build()

# Run simulation for a while
for _ in range(500):
    scene.step()