"""
User Query: Build a showroom scene containing a sports car model with glossy paint, reflective windows, metallic wheels, and a polished floor that reflects the environment lighting.
task_id: s1_surface_complex_002
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01),
    renderer=gs.options.renderers.RayTracer(),
)

floor = scene.add_entity(
    morph=gs.morphs.Box(pos=(0.0, 0.0, -0.05), size=(12.0, 12.0, 0.1)),
    material=gs.materials.Rigid(rho=1200, friction=0.6, restitution=0.05),
    surface=gs.surfaces.Glass(color=(0.92, 0.92, 0.95, 0.35)),
)

body_main = scene.add_entity(
    morph=gs.morphs.Box(pos=(0.0, 0.0, 0.55), size=(3.2, 1.5, 0.5)),
    material=gs.materials.Rigid(rho=900, friction=0.5, restitution=0.05),
    surface=gs.surfaces.Default(color=(0.82, 0.08, 0.08, 1.0)),
)

hood = scene.add_entity(
    morph=gs.morphs.Box(pos=(0.95, 0.0, 0.5), size=(1.0, 1.45, 0.18)),
    material=gs.materials.Rigid(rho=900, friction=0.5, restitution=0.05),
    surface=gs.surfaces.Default(color=(0.86, 0.1, 0.1, 1.0)),
)

roof = scene.add_entity(
    morph=gs.morphs.Box(pos=(-0.15, 0.0, 0.92), size=(1.35, 1.25, 0.32)),
    material=gs.materials.Rigid(rho=850, friction=0.5, restitution=0.05),
    surface=gs.surfaces.Default(color=(0.8, 0.08, 0.08, 1.0)),
)

rear = scene.add_entity(
    morph=gs.morphs.Box(pos=(-1.15, 0.0, 0.56), size=(0.8, 1.45, 0.32)),
    material=gs.materials.Rigid(rho=900, friction=0.5, restitution=0.05),
    surface=gs.surfaces.Default(color=(0.78, 0.07, 0.07, 1.0)),
)

windshield = scene.add_entity(
    morph=gs.morphs.Box(pos=(0.25, 0.0, 0.82), size=(0.75, 1.18, 0.04)),
    material=gs.materials.Rigid(rho=1000, friction=0.2, restitution=0.02),
    surface=gs.surfaces.Glass(color=(0.45, 0.55, 0.65, 0.35)),
)

rear_window = scene.add_entity(
    morph=gs.morphs.Box(pos=(-0.7, 0.0, 0.82), size=(0.55, 1.1, 0.04)),
    material=gs.materials.Rigid(rho=1000, friction=0.2, restitution=0.02),
    surface=gs.surfaces.Glass(color=(0.42, 0.5, 0.6, 0.35)),
)

left_window = scene.add_entity(
    morph=gs.morphs.Box(pos=(-0.12, 0.63, 0.82), size=(1.2, 0.04, 0.26)),
    material=gs.materials.Rigid(rho=1000, friction=0.2, restitution=0.02),
    surface=gs.surfaces.Glass(color=(0.4, 0.5, 0.62, 0.35)),
)

right_window = scene.add_entity(
    morph=gs.morphs.Box(pos=(-0.12, -0.63, 0.82), size=(1.2, 0.04, 0.26)),
    material=gs.materials.Rigid(rho=1000, friction=0.2, restitution=0.02),
    surface=gs.surfaces.Glass(color=(0.4, 0.5, 0.62, 0.35)),
)

wheel_positions = [
    (1.0, 0.82, 0.28),
    (1.0, -0.82, 0.28),
    (-1.0, 0.82, 0.28),
    (-1.0, -0.82, 0.28),
]

for pos in wheel_positions:
    scene.add_entity(
        morph=gs.morphs.Cylinder(pos=pos, radius=0.34, height=0.24),
        material=gs.materials.Rigid(rho=7800, friction=0.9, restitution=0.03),
        surface=gs.surfaces.Iron(color=(0.18, 0.18, 0.2, 1.0)),
    )
    scene.add_entity(
        morph=gs.morphs.Cylinder(pos=pos, radius=0.18, height=0.26),
        material=gs.materials.Rigid(rho=2700, friction=0.6, restitution=0.03),
        surface=gs.surfaces.Aluminium(color=(0.9, 0.9, 0.92, 1.0)),
    )

for x, y in [(1.52, 0.48), (1.52, -0.48)]:
    scene.add_entity(
        morph=gs.morphs.Sphere(pos=(x, y, 0.54), radius=0.09),
        material=gs.materials.Rigid(rho=1000, friction=0.3, restitution=0.02),
        surface=gs.surfaces.Emission(color=(1.0, 0.95, 0.8, 1.0)),
    )

for x, y in [(-1.56, 0.4), (-1.56, -0.4)]:
    scene.add_entity(
        morph=gs.morphs.Sphere(pos=(x, y, 0.5), radius=0.07),
        material=gs.materials.Rigid(rho=1000, friction=0.3, restitution=0.02),
        surface=gs.surfaces.Emission(color=(1.0, 0.15, 0.1, 1.0)),
    )

scene.add_entity(
    morph=gs.morphs.Box(pos=(0.0, -3.8, 2.0), size=(12.0, 0.12, 4.0)),
    material=gs.materials.Rigid(rho=800, friction=0.5, restitution=0.05),
    surface=gs.surfaces.Emission(color=(1.0, 1.0, 1.0, 1.0)),
)

scene.add_entity(
    morph=gs.morphs.Box(pos=(0.0, 3.8, 2.0), size=(12.0, 0.12, 4.0)),
    material=gs.materials.Rigid(rho=800, friction=0.5, restitution=0.05),
    surface=gs.surfaces.Emission(color=(1.0, 1.0, 1.0, 1.0)),
)

scene.add_entity(
    morph=gs.morphs.Box(pos=(0.0, 0.0, 4.2), size=(8.0, 8.0, 0.12)),
    material=gs.materials.Rigid(rho=800, friction=0.5, restitution=0.05),
    surface=gs.surfaces.Emission(color=(0.95, 0.97, 1.0, 1.0)),
)

scene.add_camera(
    pos=(6.0, -5.0, 2.8),
    lookat=(0.0, 0.0, 0.7),
    fov=40,
)

scene.build()

for _ in range(240):
    scene.step()