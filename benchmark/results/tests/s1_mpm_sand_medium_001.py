"""
User Query: Simulate sand particles being released from a container that tips over, causing the sand to pour out and form a pile on the ground.
task_id: s1_mpm_sand_medium_001
"""

import math
import genesis as gs

gs.init()

scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        dt=0.005,
        substeps=10,
        gravity=(0.0, 0.0, -9.81),
    ),
    mpm_options=gs.options.MPMOptions(
        lower_bound=(-2.0, -2.0, -0.2),
        upper_bound=(2.0, 2.0, 2.0),
    ),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(2.8, -2.2, 1.8),
        camera_lookat=(0.0, 0.0, 0.5),
        camera_fov=40,
    ),
    renderer=gs.options.renderers.Rasterizer(),
)

scene.add_entity(
    material=gs.materials.Rigid(
        rho=300.0,
        friction=1.2,
        coup_friction=0.1,
        coup_restitution=0.0,
    ),
    morph=gs.morphs.Plane(),
    surface=gs.surfaces.Rough(color=(0.75, 0.75, 0.78, 1.0)),
)

container_base = scene.add_entity(
    material=gs.materials.Rigid(
        rho=500.0,
        friction=1.0,
        coup_friction=0.1,
        coup_restitution=0.0,
    ),
    morph=gs.morphs.Box(
        pos=(0.0, 0.0, 0.55),
        size=(0.42, 0.28, 0.04),
    ),
    surface=gs.surfaces.Iron(color=(0.55, 0.57, 0.62, 1.0)),
)

left_wall = scene.add_entity(
    material=gs.materials.Rigid(
        rho=500.0,
        friction=1.0,
        coup_friction=0.1,
        coup_restitution=0.0,
    ),
    morph=gs.morphs.Box(
        pos=(0.0, 0.14, 0.68),
        size=(0.42, 0.02, 0.26),
    ),
    surface=gs.surfaces.Iron(color=(0.55, 0.57, 0.62, 1.0)),
)

right_wall = scene.add_entity(
    material=gs.materials.Rigid(
        rho=500.0,
        friction=1.0,
        coup_friction=0.1,
        coup_restitution=0.0,
    ),
    morph=gs.morphs.Box(
        pos=(0.0, -0.14, 0.68),
        size=(0.42, 0.02, 0.26),
    ),
    surface=gs.surfaces.Iron(color=(0.55, 0.57, 0.62, 1.0)),
)

back_wall = scene.add_entity(
    material=gs.materials.Rigid(
        rho=500.0,
        friction=1.0,
        coup_friction=0.1,
        coup_restitution=0.0,
    ),
    morph=gs.morphs.Box(
        pos=(-0.20, 0.0, 0.68),
        size=(0.02, 0.24, 0.26),
    ),
    surface=gs.surfaces.Iron(color=(0.55, 0.57, 0.62, 1.0)),
)

sand = scene.add_entity(
    material=gs.materials.MPM.Sand(
        sampler="regular",
    ),
    morph=gs.morphs.Box(
        pos=(-0.04, 0.0, 0.73),
        size=(0.26, 0.18, 0.18),
    ),
    surface=gs.surfaces.Default(color=(0.87, 0.77, 0.52, 1.0)),
)

cam = scene.add_camera(
    res=(960, 640),
    pos=(2.8, -2.2, 1.8),
    lookat=(0.0, 0.0, 0.5),
    fov=40,
)

scene.build()

total_steps = 900
tilt_start = 120
tilt_end = 520
max_angle = math.radians(105.0)

for i in range(total_steps):
    if i < tilt_start:
        angle = 0.0
    elif i < tilt_end:
        alpha = (i - tilt_start) / float(tilt_end - tilt_start)
        alpha = 0.5 - 0.5 * math.cos(math.pi * alpha)
        angle = max_angle * alpha
    else:
        angle = max_angle

    pivot_x = -0.21
    pivot_z = 0.55

    cos_a = math.cos(angle)
    sin_a = math.sin(angle)

    def rot_xz(local_x, local_z):
        rx = local_x * cos_a - local_z * sin_a
        rz = local_x * sin_a + local_z * cos_a
        return rx, rz

    base_local = (0.21, 0.0)
    left_local = (0.21, 0.13)
    right_local = (0.21, 0.13)
    back_local = (0.01, 0.13)

    base_rx, base_rz = rot_xz(base_local[0], base_local[1])
    left_rx, left_rz = rot_xz(left_local[0], left_local[1])
    right_rx, right_rz = rot_xz(right_local[0], right_local[1])
    back_rx, back_rz = rot_xz(back_local[0], back_local[1])

    base_pos = (pivot_x + base_rx, 0.0, pivot_z + base_rz)
    left_pos = (pivot_x + left_rx, 0.14, pivot_z + left_rz)
    right_pos = (pivot_x + right_rx, -0.14, pivot_z + right_rz)
    back_pos = (pivot_x + back_rx, 0.0, pivot_z + back_rz)

    quat = gs.utils.geom.xyz_to_quat((0.0, angle, 0.0))

    container_base.set_pos(base_pos)
    container_base.set_quat(quat)

    left_wall.set_pos(left_pos)
    left_wall.set_quat(quat)

    right_wall.set_pos(right_pos)
    right_wall.set_quat(quat)

    back_wall.set_pos(back_pos)
    back_wall.set_quat(quat)

    scene.step()

    if i % 60 == 0:
        print(f"step={i}, tilt_deg={math.degrees(angle):.1f}")

img = cam.render()
print("Simulation complete.")