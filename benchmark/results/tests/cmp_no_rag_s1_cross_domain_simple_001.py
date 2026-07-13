import genesis as gs

gs.init(backend=gs.cpu, logger_level=50)

scene = gs.Scene(
    gravity=(0.0, 0.0, -9.81),
    show_viewer=True,
)

rigid_material = gs.materials.Rigid()
fluid_material = gs.materials.Fluid(
    density=1000.0,
    viscosity=0.01,
)

# Container dimensions
length = 1.0
width = 1.0
height = 0.6
wall_thickness = 0.05

# Floor
floor = scene.add_entity(
    gs.morphs.Box(
        half_size=(length / 2, width / 2, wall_thickness / 2),
        pos=(0.0, 0.0, wall_thickness / 2),
    ),
    material=rigid_material,
)

# Walls
walls = [
    ((-length / 2 + wall_thickness / 2, 0.0), (0.0, width / 2, height / 2)),   # left
    ((length / 2 - wall_thickness / 2, 0.0), (0.0, width / 2, height / 2)),    # right
    ((0.0, width / 2 - wall_thickness / 2), (length / 2, 0.0, height / 2)),    # front
    ((0.0, -width / 2 + wall_thickness / 2), (length / 2, 0.0, height / 2)),   # back
]
for (x, y), hsize in walls:
    scene.add_entity(
        gs.morphs.Box(
            half_size=(wall_thickness / 2, hsize[1], hsize[2]),
            pos=(x, y, height / 2),
        ),
        material=rigid_material,
    )

# Particle emitter for fluid
emitter = scene.add_particle_emitter(
    particle_type=gs.particle.Fluid(
        density=1000.0,
        viscosity=0.01,
    ),
    surface=gs.surfaces.FluidSurface(color=(0.2, 0.6, 0.8, 1.0)),
)

scene.build()

# Fill container with fluid
emitter.emit(
    pos=(0.0, 0.0, height * 0.25),
    size=(length - wall_thickness * 2, width - wall_thickness * 2, height * 0.5),
    spacing=0.08,
)

# Let fluid settle
for _ in range(500):
    scene.step()

# Drop sphere
sphere = scene.add_entity(
    gs.morphs.Sphere(
        radius=0.08,
        pos=(0.0, 0.0, height + 0.3),
    ),
    material=gs.materials.Rigid(density=500.0),
    surface=gs.surfaces.Default(color=(1.0, 0.5, 0.0)),
)

# Simulate splash
for _ in range(2500):
    scene.step()