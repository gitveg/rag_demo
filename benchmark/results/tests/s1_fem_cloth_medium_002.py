"""
User Query: Hang a rectangular cloth by its two top corners above the ground and apply a gentle sideways wind so the fabric swings back and forth.
task_id: s1_fem_cloth_medium_002
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(2.5, -2.0, 1.8),
        camera_lookat=(0.0, 0.0, 0.8),
        camera_fov=50,
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid(rho=200.0, friction=0.8, coup_friction=0.1, coup_restitution=0.0),
    surface=gs.surfaces.Default(color=(0.85, 0.85, 0.85, 1.0)),
)

cloth = scene.add_entity(
    gs.morphs.Box(
        pos=(0.0, 0.0, 1.1),
        size=(1.0, 0.02, 0.8),
    ),
    material=gs.materials.FEM.Cloth(
        rho=0.5,
        E=5e4,
        nu=0.49,
        thickness=0.001,
        model="stable_neohookean",
    ),
    surface=gs.surfaces.Rough(color=(0.3, 0.5, 0.9, 1.0)),
)

left_pin = scene.add_entity(
    gs.morphs.Sphere(pos=(-0.5, 0.0, 1.5), radius=0.04),
    material=gs.materials.Rigid(rho=500.0, friction=0.5, coup_friction=0.1, coup_restitution=0.0),
    surface=gs.surfaces.Iron(color=(0.55, 0.57, 0.62, 1.0)),
)

right_pin = scene.add_entity(
    gs.morphs.Sphere(pos=(0.5, 0.0, 1.5), radius=0.04),
    material=gs.materials.Rigid(rho=500.0, friction=0.5, coup_friction=0.1, coup_restitution=0.0),
    surface=gs.surfaces.Iron(color=(0.55, 0.57, 0.62, 1.0)),
)

scene.add_force_field(gs.force_fields.Constant(direction=(0.0, 1.0, 0.0), strength=3.0))
scene.add_force_field(gs.force_fields.Turbulence(strength=0.4, frequency=0.6))

cam = scene.add_camera(
    res=(960, 640),
    pos=(2.5, -2.0, 1.8),
    lookat=(0.0, 0.0, 0.8),
    fov=50,
)

scene.build()

if hasattr(cloth, "set_pinned_particles"):
    cloth.set_pinned_particles(
        positions=[
            (-0.5, 0.0, 1.5),
            (0.5, 0.0, 1.5),
        ]
    )
elif hasattr(cloth, "pin_particles_near"):
    cloth.pin_particles_near(
        positions=[
            (-0.5, 0.0, 1.5),
            (0.5, 0.0, 1.5),
        ],
        radius=0.08,
    )

for i in range(1200):
    if i == 400:
        scene.add_force_field(gs.force_fields.Constant(direction=(0.0, -1.0, 0.0), strength=3.0))
    if i == 800:
        scene.add_force_field(gs.force_fields.Constant(direction=(0.0, 1.0, 0.0), strength=3.0))
    scene.step()
    if i % 10 == 0:
        cam.render()