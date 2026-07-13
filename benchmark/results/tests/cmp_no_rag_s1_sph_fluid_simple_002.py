import genesis as gs

gs.init(backend=gs.cpu)

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=0.001,
        gravity=(0, 0, -9.81),
    ),
    sph_options=gs.options.SPHOptions(
        particle_size=0.01,
    ),
)

# Ground plane
scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid(),
)

# Container: floor + four walls
container_half = 0.15
wall_h = 0.2
wall_t = 0.02

# Floor
scene.add_entity(
    gs.morphs.Box(pos=(0, 0, 0.02), size=(container_half * 2, container_half * 2, 0.04)),
    material=gs.materials.Rigid(),
)

# Four walls
for sx, sy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
    cx = sx * container_half
    cy = sy * container_half
    if sx != 0:
        size = (wall_t, container_half * 2, wall_h)
    else:
        size = (container_half * 2, wall_t, wall_h)
    scene.add_entity(
        gs.morphs.Box(pos=(cx, cy, 0.02 + wall_h / 2), size=size),
        material=gs.materials.Rigid(),
    )

# Water blob starting above the container
water = scene.add_entity(
    material=gs.materials.SPH.Liquid(),
    morph=gs.morphs.Box(
        pos=(0.02, -0.02, 0.28),
        size=(0.10, 0.10, 0.06),
    ),
    surface=gs.surfaces.Default(color=(0.2, 0.5, 1.0, 0.7)),
)

# Camera to view the splashing
camera = scene.add_camera(
    pos=(0.45, -0.40, 0.35),
    lookat=(0, 0, 0.12),
    fov=40,
)

scene.build()

# Run the simulation
for _ in range(2000):
    scene.step()