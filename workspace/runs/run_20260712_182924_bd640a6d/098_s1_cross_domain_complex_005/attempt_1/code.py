import argparse
import os

import genesis as gs
from genesis.utils.terrain import mesh_to_heightfield
import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    parser.add_argument("-c", "--cpu", action="store_true", default=False)
    args = parser.parse_args()

    gs.init(backend=gs.cpu if args.cpu else gs.gpu)

    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(1.5, -2.0, 1.2),
            camera_lookat=(0.6, 0.0, 0.2),
        ),
        coupler_options=gs.options.IPCCouplerOptions(),
        mpm_options=gs.options.MPMOptions(),
        show_viewer=args.vis,
    )

    # Bumpy terrain from heightfield
    horizontal_scale = 2.0
    gs_root = os.path.dirname(os.path.abspath(gs.__file__))
    path_terrain = os.path.join(gs_root, "assets", "meshes", "terrain_45.obj")
    hf_terrain, xs, ys = mesh_to_heightfield(path_terrain, spacing=horizontal_scale, oversample=1)
    terrain = scene.add_entity(
        gs.morphs.Terrain(height_field=hf_terrain, pos=(0, 0, 0), visualization=True, collision=True, fixed=True),
    )

    # Soft deformable cube
    cube = scene.add_entity(
        material=gs.materials.MPM.Elastic(E=300000.0, nu=0.2, rho=1000.0),
        morph=gs.morphs.Box(pos=(0.65, 0.0, 0.08), size=(0.05, 0.05, 0.05), euler=(0, 0, 0)),
        surface=gs.surfaces.Default(color=(0.2, 0.6, 1.0, 1.0)),
    )

    # Robotic arm (Franka Panda with gripper)
    robot = scene.add_entity(
        material=gs.materials.Rigid(
            needs_coup=True,
            coup_friction=0.2,
        ),
        morph=gs.morphs.URDF(
            file="urdf/3763/mobility_vhacd.urdf",
            scale=0.09,
            pos=(0.5, 0.0, 0.05),
            euler=(0, 0, 0),
        ),
    )

    scene.build()

    # Let the cube settle on terrain
    for _ in range(200):
        scene.step()

    # Control the arm to pick and place the cube
    # Joint order: 7 arm DOFs + 2 finger DOFs
    q_initial = np.array([0, -0.5, 0, -1.5, 0, 1.0, 0.0, 0.0, 0.0])
    q_pre_grasp = np.array([0, -0.2, 0, -1.5, 0, 1.0, 0.0, 0.04, 0.04])  # open gripper
    q_grasp = np.array([0, -0.2, 0, -1.5, 0, 1.0, 0.0, 0.0, 0.0])       # close
    q_lift = np.array([0, -0.4, 0, -1.5, 0, 1.0, 0.0, 0.0, 0.0])
    q_release = np.array([0, -0.4, 0, -1.5, 0, 1.3, 0.0, 0.04, 0.04])

    robot.set_qpos(q_initial)
    for _ in range(100):
        scene.step()

    robot.set_qpos(q_pre_grasp)
    for _ in range(150):
        scene.step()

    robot.set_qpos(q_grasp)
    for _ in range(100):
        scene.step()

    robot.set_qpos(q_lift)
    for _ in range(200):
        scene.step()

    # Move to a new location (adjust arm to place)
    q_place = np.array([0.5, -0.4, 0, -1.5, 0, 1.0, 0.0, 0.0, 0.0])
    robot.set_qpos(q_place)
    for _ in range(200):
        scene.step()

    robot.set_qpos(q_release)
    for _ in range(150):
        scene.step()

    if args.vis:
        scene.viewer.save_video("pick_and_place.mp4")


if __name__ == "__main__":
    main()