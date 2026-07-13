import os
import numpy as np
import genesis as gs

########################## init ##########################
gs.init(precision="32", logging_level="info")

########################## create a scene ##########################
dt = 5e-4
scene = gs.Scene(
    sim_options=gs.options.SimOptions(
        substeps=10,
        gravity=(0, 0, -9.81),
    ),
    viewer_options=gs.options.ViewerOptions(
        camera_pos=(1.2, 0.5, 0.8),
        camera_lookat=(0.0, 0.0, 0.4),
        camera_fov=40,
    ),
    mpm_options=gs.options.MPMOptions(
        dt=dt,
        lower_bound=(-0.5, -0.5, 0.0),
        upper_bound=(0.5, 0.5, 1.0),
    ),
    vis_options=gs.options.VisOptions(
        show_world_frame=True,
    ),
    show_viewer=True,
)

########################## entities ##########################
scene.add_entity(morph=gs.morphs.Plane())

# Gripper: adjust path to your MJCF file
gripper = scene.add_entity(
    morph=gs.morphs.MJCF(
        file="gripper.xml",          # TODO: replace with actual gripper MJCF path
        pos=(0.0, 0.0, 0.4),
        euler=(0, 0, 0),
    ),
    material=gs.materials.Rigid(),
)

# Soft MPM elastic sphere placed between the fingers
sphere = scene.add_entity(
    morph=gs.morphs.Sphere(
        pos=(0.0, 0.0, 0.4),        # approximate center between fingers
        radius=0.05,
    ),
    material=gs.materials.MPM.Elastic(
        E=5e4,
        nu=0.3,
        rho=1000.0,
    ),
    surface=gs.surfaces.Default(
        color=(0.8, 0.2, 0.2, 1.0),
        vis_mode="particle",
    ),
)

########################## build and simulate ##########################
scene.build()

for _ in range(500):
    scene.step()