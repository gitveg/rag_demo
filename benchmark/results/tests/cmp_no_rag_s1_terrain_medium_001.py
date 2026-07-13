import genesis as gs

gs.init(backend=gs.gpu)

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=0.01,
        gravity=(0, 0, -9.81),
    ),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(10, -10, 8),
        camera_lookat=(0, 0, 0),
    ),
)

terrain = scene.add_entity(
    gs.morphs.Terrain(
        n_subterrains=(3, 3),
        subterrain_types=[
            "random_uniform_terrain", "wave_terrain", "random_uniform_terrain",
            "wave_terrain", "random_uniform_terrain", "wave_terrain",
            "random_uniform_terrain", "wave_terrain", "random_uniform_terrain",
        ],
    ),
)

sphere_positions = [
    (0.5, 0.5, 2.0),
    (-0.5, -0.5, 3.0),
    (0.0, 0.0, 2.5),
]

for pos in sphere_positions:
    scene.add_entity(
        gs.morphs.Sphere(pos=pos, radius=0.2),
        material=gs.materials.Rigid(),
    )

scene.build()

for _ in range(2000):
    scene.step()
    scene.viewer.render()