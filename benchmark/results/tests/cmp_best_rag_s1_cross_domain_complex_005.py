import numpy as np
import genesis as gs

def main():
    ########################## init ##########################
    gs.init()

    ########################## create a scene ##########################
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=0.01,
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(2.5, 2.0, 1.5),
            camera_lookat=(0.5, 0.0, 0.5),
        ),
    )

    ########################## entities ##########################
    # ground plane
    plane = scene.add_entity(
        gs.morphs.Plane(),
    )

    # bumpy terrain: scatter small boxes on the plane to imitate bumpiness
    np.random.seed(0)
    for _ in range(30):
        x = np.random.uniform(-0.3, 1.0)
        y = np.random.uniform(-0.6, 0.6)
        z = 0.0
        h = np.random.uniform(0.005, 0.02)
        sz = (0.04, 0.04, h)
        scene.add_entity(
            gs.morphs.Box(pos=(x, y, z + h / 2), size=sz),
            surface=gs.options.surfaces.Plastic(color=(0.4, 0.4, 0.4, 1.0)),
        )

    # Franka Panda robot
    franka = scene.add_entity(
        gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
    )

    # soft elastic cube – represented here as a rigid box (deformable simulation
    # would require additional solvers and material setups not shown in reference)
    cube = scene.add_entity(
        gs.morphs.Box(pos=(0.5, 0.0, 0.05), size=(0.05, 0.05, 0.05)),
        surface=gs.options.surfaces.Plastic(color=(1.0, 0.0, 0.0, 1.0)),
    )

    ########################## build scene ##########################
    scene.build()

    ########################## simple pick-and-place sequence ##########################
    # joint order: 7 arm + 2 gripper (assuming MJCF model)
    # pre-pick pose
    pre_pick_q = np.array([0.0, -0.5, 0.0, -1.5, 0.0, 1.0, 0.5, 0.04, 0.04])
    franka.set_dofs_position(pre_pick_q)
    for _ in range(150):
        scene.step()

    # move down to cube
    pick_q = np.array([0.0, -0.6, 0.0, -1.6, 0.0, 1.2, 0.5, 0.04, 0.04])
    franka.set_dofs_position(pick_q)
    for _ in range(150):
        scene.step()

    # close gripper
    close_q = np.array([0.0, -0.6, 0.0, -1.6, 0.0, 1.2, 0.5, 0.0, 0.0])
    franka.set_dofs_position(close_q)
    for _ in range(100):
        scene.step()

    # lift
    lift_q = np.array([0.0, -0.4, 0.0, -1.4, 0.0, 1.0, 0.5, 0.0, 0.0])
    franka.set_dofs_position(lift_q)
    for _ in range(150):
        scene.step()

    # move to target position (right and forward)
    place_q = np.array([0.4, -0.3, 0.1, -1.3, 0.1, 0.9, 0.7, 0.0, 0.0])
    franka.set_dofs_position(place_q)
    for _ in range(200):
        scene.step()

    # lower and open gripper
    lower_q = np.array([0.4, -0.5, 0.1, -1.5, 0.1, 1.1, 0.7, 0.04, 0.04])
    franka.set_dofs_position(lower_q)
    for _ in range(150):
        scene.step()

    # idle
    for _ in range(500):
        scene.step()

if __name__ == "__main__":
    main()