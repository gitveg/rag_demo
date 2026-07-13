import argparse
import numpy as np
import torch
import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    parser.add_argument("-c", "--cpu", action="store_true", default=False)
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(backend=gs.cpu if args.cpu else gs.gpu)

    ########################## create a scene ##########################
    scene = gs.Scene(
        rigid_options=gs.options.RigidOptions(
            dt=0.01,
            constraint_solver=gs.constraint_solver.Newton,
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(-5.0, -5.0, 10.0),
            camera_lookat=(5.0, 5.0, 0.0),
            camera_fov=40,
        ),
        show_viewer=args.vis,
    )

    ########################## entities ##########################
    # ground plane
    scene.add_entity(gs.morphs.Plane())

    # rotating rigid box
    box = scene.add_entity(
        material=gs.materials.Rigid(rho=300, friction=1.0),
        morph=gs.morphs.Box(
            pos=(0.5, 0.0, 0.05),  # slightly above ground
            size=(0.1, 0.1, 0.1),
        ),
        surface=gs.surfaces.Default(color=(0.5, 1.0, 0.5)),
    )

    # fixed pole (optional, not strictly needed for lidar)
    pole = scene.add_entity(
        morph=gs.morphs.Box(
            pos=(-0.5, 0.0, 0.25),
            size=(0.05, 0.05, 0.5),
            fixed=True,
        ),
        material=gs.materials.Rigid(),
        surface=gs.surfaces.Plastic(color=(0.8, 0.3, 0.2, 0.8)),
    )

    ########################## lidar sensor ##########################
    lidar = scene.add_sensor(
        gs.sensors.Lidar(
            pos=(0.0, 1.0, 0.6),      # position on top of pole
            quat=(1.0, 0.0, 0.0, 0.0), # pointing at the box
            hz=10,                      # 10 Hz
            H=64,
            W=256,
            fov=(-90.0, 90.0),
            min_range=0.05,
            max_range=5.0,
        )
    )

    ########################## build & step ##########################
    scene.build()

    # give the box an initial angular velocity to make it rotate
    box.set_velocity(ang_vel=torch.tensor([0.0, 0.0, 2.0], device=box.device))

    # simulation loop
    num_steps = 200
    for i in range(num_steps):
        scene.step()

        # capture point cloud at each step (or periodically)
        points = lidar.get_pointcloud(as_numpy=True)
        if points is not None and points.shape[0] > 0:
            print(f"Step {i}: point cloud shape {points.shape}")
        else:
            print(f"Step {i}: empty point cloud")

        # option to slow down visualization
        if args.vis:
            scene.viewer.update()


if __name__ == "__main__":
    main()