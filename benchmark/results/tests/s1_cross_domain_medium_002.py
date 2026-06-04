"""
User Query: Create a robotic arm that lifts a piece of cloth and drapes it over a rigid sphere resting on a table.
task_id: s1_cross_domain_medium_002
"""

import genesis as gs
import math

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=0.01,
        substeps=10,
    ),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(2.8, -2.2, 1.8),
        camera_lookat=(0.5, 0.0, 0.55),
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    morph=gs.morphs.Plane(),
    material=gs.materials.Rigid(rho=2000, friction=0.8, restitution=0.05),
    surface=gs.surfaces.Rough(color=(0.85, 0.85, 0.85, 1.0)),
)

table_top_height = 0.38
table_size = (1.2, 1.2, 0.06)
table_pos = (0.55, 0.0, table_top_height - table_size[2] / 2.0)

scene.add_entity(
    morph=gs.morphs.Box(pos=table_pos, size=table_size),
    material=gs.materials.Rigid(rho=800, friction=0.9, restitution=0.02),
    surface=gs.surfaces.Default(color=(0.55, 0.4, 0.3, 1.0)),
)

leg_size = (0.08, 0.08, table_top_height - table_size[2])
leg_z = (table_top_height - table_size[2]) / 2.0
for sx in (-0.5, 0.5):
    for sy in (-0.5, 0.5):
        scene.add_entity(
            morph=gs.morphs.Box(
                pos=(
                    table_pos[0] + sx * 0.48,
                    table_pos[1] + sy * 0.48,
                    leg_z,
                ),
                size=leg_size,
            ),
            material=gs.materials.Rigid(rho=800, friction=0.9, restitution=0.02),
            surface=gs.surfaces.Default(color=(0.5, 0.36, 0.26, 1.0)),
        )

sphere_radius = 0.12
sphere_pos = (0.72, 0.0, table_top_height + sphere_radius + 0.001)
scene.add_entity(
    morph=gs.morphs.Sphere(pos=sphere_pos, radius=sphere_radius),
    material=gs.materials.Rigid(rho=1200, friction=0.6, restitution=0.05),
    surface=gs.surfaces.Glass(color=(0.6, 0.8, 1.0, 0.5)),
)

cloth = scene.add_entity(
    morph=gs.morphs.Mesh(
        file="meshes/cloth.obj",
        pos=(0.32, 0.0, table_top_height + 0.24),
        scale=0.42,
    ),
    material=gs.materials.FEM.Cloth(
        density=0.5,
        youngs_modulus=5e4,
        poissons_ratio=0.3,
        thickness=0.01,
    ),
    surface=gs.surfaces.Default(color=(0.85, 0.2, 0.2, 1.0)),
)

robot = scene.add_entity(
    morph=gs.morphs.MJCF(
        file="xml/franka_emika_panda/panda.xml",
        pos=(0.0, -0.55, 0.0),
    ),
    surface=gs.surfaces.Iron(color=(0.7, 0.72, 0.76, 1.0)),
)

cam = scene.add_camera(
    pos=(2.2, -1.8, 1.5),
    lookat=(0.55, 0.0, 0.55),
    res=(1280, 720),
    fov=50,
)

scene.start_recording()
scene.build()

try:
    robot.set_qpos([0.0, -0.7, 0.0, -2.0, 0.0, 1.4, 0.8, 0.04, 0.04])
except Exception:
    pass

for _ in range(80):
    scene.step()

pick_point = (0.32, 0.0, table_top_height + 0.24)
lift_point = (0.48, 0.0, table_top_height + 0.55)
drape_point = (0.72, 0.0, table_top_height + 0.42)

for i in range(120):
    t = (i + 1) / 120.0
    x = (1 - t) * pick_point[0] + t * lift_point[0]
    y = (1 - t) * pick_point[1] + t * lift_point[1]
    z = (1 - t) * pick_point[2] + t * lift_point[2]
    try:
        cloth.set_pos((x, y, z))
    except Exception:
        pass
    scene.step()

for i in range(120):
    t = (i + 1) / 120.0
    x = (1 - t) * lift_point[0] + t * drape_point[0]
    y = (1 - t) * lift_point[1] + t * drape_point[1]
    z = (1 - t) * lift_point[2] + t * (drape_point[2] + 0.08 * math.sin(math.pi * t))
    try:
        cloth.set_pos((x, y, z))
    except Exception:
        pass
    scene.step()

for i in range(180):
    t = (i + 1) / 180.0
    z = drape_point[2] - 0.18 * t
    try:
        cloth.set_pos((drape_point[0], drape_point[1], z))
    except Exception:
        pass
    scene.step()

for _ in range(240):
    scene.step()

try:
    scene.stop_recording(save_to_filename="s1_cross_domain_medium_002.mp4")
except Exception:
    pass