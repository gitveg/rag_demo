import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=4e-3,
        substeps=10,
    ),
    sph_options=gs.options.SPHOptions(
        lower_bound=(-0.3, -0.3, 0.0),
        upper_bound=(0.3, 0.3, 0.8),
        particle_size=0.012,
    ),
    vis_options=gs.options.VisOptions(
        visualize_sph_boundary=True,
    ),
    show_viewer=True,
)

# Camera for a good view of the container and splashing
scene.add_camera(res=(1280, 720), pos=(1.0, 0.6, 0.7), lookat=(0.0, 0.0, 0.3), fov=35)

# Ground plane (infinite floor)
scene.add_entity(gs.morphs.Plane())

# Initial water block above the container
water = scene.add_entity(
    gs.morphs.Box(
        pos=(0.0, 0.0, 0.5),
        size=(0.2, 0.2, 0.1),
    ),
    material=gs.materials.SPH.Liquid(rho=1000.0),
)

scene.build()

for _ in range(2000):
    scene.step()