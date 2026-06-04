"""
User Query: Render a scene with a gold-colored torus and a semi-transparent glass sphere, adjusting their roughness so the gold is polished and the glass is slightly frosted.
task_id: s1_surface_complex_003
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01),
    renderer=gs.options.renderers.RayTracer(),
)

scene.add_entity(
    morph=gs.morphs.Plane(),
    material=gs.materials.Rigid(rho=200.0, friction=0.8, coup_friction=0.1, coup_restitution=0.0),
    surface=gs.surfaces.Rough(color=(0.85, 0.85, 0.85, 1.0)),
)

scene.add_entity(
    morph=gs.morphs.Mesh(
        file="meshes/torus.obj",
        pos=(-0.5, 0.0, 0.8),
        scale=0.6,
    ),
    material=gs.materials.Rigid(rho=200.0, friction=0.4, coup_friction=0.1, coup_restitution=0.0),
    surface=gs.surfaces.Gold(color=(1.0, 0.84, 0.0, 1.0)),
)

scene.add_entity(
    morph=gs.morphs.Sphere(
        pos=(0.7, 0.0, 0.8),
        radius=0.35,
    ),
    material=gs.materials.Rigid(rho=200.0, friction=0.3, coup_friction=0.1, coup_restitution=0.0),
    surface=gs.surfaces.Glass(color=(0.85, 0.95, 1.0, 0.45)),
)

scene.add_camera(
    pos=(3.0, -2.5, 1.8),
    lookat=(0.1, 0.0, 0.75),
    res=(1280, 720),
)

scene.build()

for _ in range(10):
    scene.step()