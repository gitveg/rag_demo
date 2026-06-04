"""
User Query: Load a rubber duck mesh as a soft body (use gs.morphs.Mesh(file="meshes/duck.obj")). Give it high elasticity and drop it into a narrow container made of boxes so it compresses significantly.
task_id: s1_fem_elastic_complex_003
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.005),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    morph=gs.morphs.Plane(),
    material=gs.materials.Rigid(rho=200.0, friction=1.0, coup_friction=0.1, coup_restitution=0.0),
    surface=gs.surfaces.Default(color=(0.8, 0.8, 0.8, 1.0)),
)

wall_thickness = 0.08
container_height = 1.0
inner_w = 0.42
inner_d = 0.42
floor_thickness = 0.08
container_center = (0.0, 0.0)

scene.add_entity(
    morph=gs.morphs.Box(
        pos=(container_center[0], container_center[1], floor_thickness * 0.5),
        size=(inner_w + 2 * wall_thickness, inner_d + 2 * wall_thickness, floor_thickness),
    ),
    material=gs.materials.Rigid(rho=400.0, friction=1.2, coup_friction=0.1, coup_restitution=0.0),
    surface=gs.surfaces.Iron(color=(0.45, 0.47, 0.52, 1.0)),
)

scene.add_entity(
    morph=gs.morphs.Box(
        pos=(container_center[0] + inner_w * 0.5 + wall_thickness * 0.5, container_center[1], container_height * 0.5),
        size=(wall_thickness, inner_d + 2 * wall_thickness, container_height),
    ),
    material=gs.materials.Rigid(rho=400.0, friction=1.2, coup_friction=0.1, coup_restitution=0.0),
    surface=gs.surfaces.Iron(color=(0.55, 0.57, 0.62, 1.0)),
)

scene.add_entity(
    morph=gs.morphs.Box(
        pos=(container_center[0] - inner_w * 0.5 - wall_thickness * 0.5, container_center[1], container_height * 0.5),
        size=(wall_thickness, inner_d + 2 * wall_thickness, container_height),
    ),
    material=gs.materials.Rigid(rho=400.0, friction=1.2, coup_friction=0.1, coup_restitution=0.0),
    surface=gs.surfaces.Iron(color=(0.55, 0.57, 0.62, 1.0)),
)

scene.add_entity(
    morph=gs.morphs.Box(
        pos=(container_center[0], container_center[1] + inner_d * 0.5 + wall_thickness * 0.5, container_height * 0.5),
        size=(inner_w, wall_thickness, container_height),
    ),
    material=gs.materials.Rigid(rho=400.0, friction=1.2, coup_friction=0.1, coup_restitution=0.0),
    surface=gs.surfaces.Iron(color=(0.55, 0.57, 0.62, 1.0)),
)

scene.add_entity(
    morph=gs.morphs.Box(
        pos=(container_center[0], container_center[1] - inner_d * 0.5 - wall_thickness * 0.5, container_height * 0.5),
        size=(inner_w, wall_thickness, container_height),
    ),
    material=gs.materials.Rigid(rho=400.0, friction=1.2, coup_friction=0.1, coup_restitution=0.0),
    surface=gs.surfaces.Iron(color=(0.55, 0.57, 0.62, 1.0)),
)

duck = scene.add_entity(
    morph=gs.morphs.Mesh(
        file="meshes/duck.obj",
        pos=(0.0, 0.0, 0.85),
        scale=0.55,
        euler=(90.0, 0.0, 25.0),
    ),
    material=gs.materials.FEM.Elastic(
        rho=850.0,
        E=4.0e4,
        nu=0.45,
        model="linear",
    ),
    surface=gs.surfaces.Gold(color=(1.0, 0.85, 0.1, 1.0)),
)

scene.build()

for i in range(1200):
    scene.step()
    if i % 200 == 0:
        try:
            print(f"step={i}, duck_pos={duck.get_pos()}")
        except Exception:
            pass