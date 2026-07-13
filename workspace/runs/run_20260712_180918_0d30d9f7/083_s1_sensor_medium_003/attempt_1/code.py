import argparse
import numpy as np
import torch

import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    parser.add_argument("-c", "--cpu", action="store_true", default=False)
    args = parser.parse_args()

    gs.init(backend=gs.cpu if args.cpu else gs.gpu)

    scene = gs.Scene(
        rigid_options=gs.options.RigidOptions(
            dt=0.01,
            constraint_solver=gs.constraint_solver.Newton,
        ),
        show_viewer=args.vis,
    )

    # platform (ground plane)
    scene.add_entity(gs.morphs.Plane())

    # falling rigid body (sphere)
    sphere = scene.add_entity(
        gs.morphs.Sphere(
            pos=(0.0, 0.0, 2.0),
            radius=0.1,
        ),
    )

    # attach IMU sensor to sphere's base link
    imu_sensor = scene.add_sensor(
        gs.options.sensors.IMU(link=sphere.links[0])
    )

    scene.build()

    acc_history = []
    for _ in range(300):
        scene.step()
        acc = imu_sensor.accelerometer  # linear acceleration (3,)
        acc_history.append(acc.cpu().numpy())

    acc_history = np.array(acc_history)
    np.save("imu_acc.npy", acc_history)
    print(f"Recorded IMU data of shape {acc_history.shape}")


if __name__ == "__main__":
    main()