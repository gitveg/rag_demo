import genesis as gs

gs.init(backend=gs.gpu)

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=1e-3,
        substeps=5,
        gravity=(0, 0, -9.81),
    ),
    show_viewer=True,
)

# Ground plane
scene.add_entity(gs.morphs.Plane())

# Container: four walls and a floor, all static
floor_size = 1.2
wall_height = 0.6
wall_thickness = 0.02
water_level = 0.3
water_size = 1.0

# Floor
scene.add_entity(
    gs.morphs.Box(pos=(0, 0, -wall_thickness/2), size=(floor_size, floor_size, wall_thickness)),
    material=gs.materials.Rigid(solver='static'),
)

# Walls
scene.add_entity(
    gs.morphs.Box(pos=(-floor_size/2 + wall_thickness/2, 0, wall_height/2), size=(wall_thickness, floor_size, wall_height)),
    material=gs.materials.Rigid(solver='static'),
)
scene.add_entity(
    gs.morphs.Box(pos=(floor_size/2 - wall_thickness/2, 0, wall_height/2), size=(wall_thickness, floor_size, wall_height)),
    material=gs.materials.Rigid(solver='static'),
)
scene.add_entity(
    gs.morphs.Box(pos=(0, -floor_size/2 + wall_thickness/2, wall_height/2), size=(floor_size - 2*wall_thickness, wall_thickness, wall_height)),
    material=gs.materials.Rigid(solver='static'),
)
scene.add_entity(
    gs.morphs.Box(pos=(0, floor_size/2 - wall_thickness/2, wall_height/2), size=(floor_size - 2*wall_thickness, wall_thickness, wall_height)),
    material=gs.materials.Rigid(solver='static'),
)

# Water (SPH liquid)
fluid = scene.add_entity(
    morph=gs.morphs.Box(
        pos=(0, 0, water_level/2),
        size=(water_size, water_size, water_level),
    ),
    material=gs.materials.Liquid(
        density=1000,
        viscosity=0.01,
    ),
    surface=gs.surfaces.Fluid(),
)

# Sphere
sphere = scene.add_entity(
    gs.morphs.Sphere(radius=0.08, pos=(0, 0, 1.2)),
    material=gs.materials.Rigid(),
)

scene.build()

# Simulation loop
for i in range(3000):
    scene.step()