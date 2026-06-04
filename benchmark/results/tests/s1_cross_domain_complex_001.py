"""
User Query: Simulate a robot arm pushing a rigid box off a table into a pool of water below. The box should splash into the water and sink.
task_id: s1_cross_domain_complex_001
"""

import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(dt=0.01),
    rigid_options=gs.options.RigidOptions(
        gravity=(0.0, 0.0, -9.81),
    ),
    sph_options=gs.options.SPHOptions(
        lower_bound=(-2.0, -2.0, -1.0),
        upper_bound=(2.0, 2.0, 2.0),
        particle_size=0.04,
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    gs.morphs.Plane(),
    material=gs.materials.Rigid(friction=1.0),
    surface=gs.surfaces.Default(color=(0.7, 0.7, 0.7, 1.0)),
)

table_top = scene.add_entity(
    gs.morphs.Box(pos=(0.0, 0.0, 0.75), size=(1.2, 1.2, 0.08)),
    material=gs.materials.Rigid(rho=500.0, friction=1.2),
    surface=gs.surfaces.Rough(color=(0.45, 0.3, 0.2, 1.0)),
)

for leg_x in (-0.5, 0.5):
    for leg_y in (-0.5, 0.5):
        scene.add_entity(
            gs.morphs.Box(pos=(leg_x, leg_y, 0.35), size=(0.08, 0.08, 0.7)),
            material=gs.materials.Rigid(rho=500.0, friction=1.0),
            surface=gs.surfaces.Rough(color=(0.4, 0.25, 0.18, 1.0)),
        )

scene.add_entity(
    gs.morphs.Box(pos=(0.0, 0.0, 0.02), size=(1.4, 1.4, 0.04)),
    material=gs.materials.Rigid(rho=800.0, friction=1.0),
    surface=gs.surfaces.Default(color=(0.55, 0.55, 0.6, 1.0)),
)

pool_wall_thickness = 0.08
pool_depth = 0.55
pool_center = (0.0, 0.0)
pool_half = 0.55

scene.add_entity(
    gs.morphs.Box(pos=(0.0, 0.0, -0.25), size=(1.1, 1.1, 0.1)),
    material=gs.materials.Rigid(rho=1000.0, friction=1.0),
    surface=gs.surfaces.Default(color=(0.5, 0.5, 0.55, 1.0)),
)

scene.add_entity(
    gs.morphs.Box(pos=(pool_half + pool_wall_thickness / 2, 0.0, 0.0), size=(pool_wall_thickness, 1.1, pool_depth)),
    material=gs.materials.Rigid(rho=1200.0, friction=1.0),
    surface=gs.surfaces.Default(color=(0.6, 0.6, 0.65, 1.0)),
)
scene.add_entity(
    gs.morphs.Box(pos=(-(pool_half + pool_wall_thickness / 2), 0.0, 0.0), size=(pool_wall_thickness, 1.1, pool_depth)),
    material=gs.materials.Rigid(rho=1200.0, friction=1.0),
    surface=gs.surfaces.Default(color=(0.6, 0.6, 0.65, 1.0)),
)
scene.add_entity(
    gs.morphs.Box(pos=(0.0, pool_half + pool_wall_thickness / 2, 0.0), size=(1.1, pool_wall_thickness, pool_depth)),
    material=gs.materials.Rigid(rho=1200.0, friction=1.0),
    surface=gs.surfaces.Default(color=(0.6, 0.6, 0.65, 1.0)),
)
scene.add_entity(
    gs.morphs.Box(pos=(0.0, -(pool_half + pool_wall_thickness / 2), 0.0), size=(1.1, pool_wall_thickness, pool_depth)),
    material=gs.materials.Rigid(rho=1200.0, friction=1.0),
    surface=gs.surfaces.Default(color=(0.6, 0.6, 0.65, 1.0)),
)

water = scene.add_entity(
    gs.morphs.Box(pos=(0.0, 0.0, -0.02), size=(0.92, 0.92, 0.36)),
    material=gs.materials.SPH.Liquid(sampler="regular"),
    surface=gs.surfaces.Glass(color=(0.35, 0.55, 0.95, 0.5)),
)

robot = scene.add_entity(
    gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
)

box = scene.add_entity(
    gs.morphs.Box(pos=(0.38, 0.0, 0.84), size=(0.12, 0.12, 0.12)),
    material=gs.materials.Rigid(rho=2500.0, friction=0.8, coup_friction=0.15, coup_restitution=0.0),
    surface=gs.surfaces.Iron(color=(0.4, 0.45, 0.5, 1.0)),
)

cam = scene.add_camera(
    pos=(2.2, -2.0, 1.8),
    lookat=(0.0, 0.0, 0.2),
    res=(1280, 720),
)

scene.build()

try:
    robot.set_qpos([0.0, -0.7, 0.0, -2.0, 0.0, 1.3, 0.78, 0.04, 0.04])
except Exception:
    pass

try:
    scene.step()
except Exception:
    pass

hover_steps = 80
for _ in range(hover_steps):
    scene.step()

push_steps = 220
for i in range(push_steps):
    phase = i / max(push_steps - 1, 1)
    try:
        ee_target = (0.18 + 0.42 * phase, 0.0, 0.90)
        q_target = robot.inverse_kinematics(
            link_name="panda_hand",
            pos=ee_target,
        )
        robot.control_dofs_position(q_target)
    except Exception:
        pass
    scene.step()

settle_steps = 700
for _ in range(settle_steps):
    scene.step()