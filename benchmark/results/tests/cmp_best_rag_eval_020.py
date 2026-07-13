import os
import numpy as np
import genesis as gs

def main():
    ########################## init ##########################
    gs.init(precision="32", logging_level="info")

    ########################## create a scene ##########################
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=2e-3,
            substeps=10,
        ),
        mpm_options=gs.options.MPMOptions(
            lower_bound=(-0.5, -0.5, 0.0),
            upper_bound=(0.5, 0.5, 0.5),
        ),
        vis_options=gs.options.VisOptions(
            visualize_mpm_boundary=True,
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_fov=30,
            res=(960, 640),
        ),
        show_viewer=True,
    )

    ########################## add entities ##########################
    # robotic gripper (Franka hand) fixed in space
    hand = scene.add_entity(
        gs.morphs.MJCF(file="xml/franka_emika_panda/panda_hand.xml", fixed=True),
        material=gs.materials.Rigid(),
    )

    # soft MPM sphere placed between the fingers
    sphere = scene.add_entity(
        gs.morphs.Sphere(pos=(0.0, 0.0, 0.03), radius=0.02),
        material=gs.materials.MPM.Elastic(rho=1000, E=300000),
    )

    ########################## build ##########################
    scene.build()

    # let the system settle briefly
    for _ in range(50):
        scene.step()

    # close the gripper onto the sphere
    hand.control_dofs_position([0.04, 0.04])
    for _ in range(500):
        scene.step()

if __name__ == "__main__":
    main()