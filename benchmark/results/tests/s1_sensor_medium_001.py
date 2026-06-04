"""
User Query: Load a Franka Panda robot arm (use gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml")). Attach an IMU sensor to its end-effector. Move the arm and record the IMU readings.
task_id: s1_sensor_medium_001
"""

import genesis as gs
import math

def main():
    gs.init()

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(dt=0.01),
        renderer=gs.options.renderers.Rasterizer(),
    )

    scene.add_entity(
        gs.morphs.Plane(),
        material=gs.materials.Rigid(friction=1.0),
        surface=gs.surfaces.Default(color=(0.85, 0.85, 0.85, 1.0)),
    )

    robot = scene.add_entity(
        gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
    )

    imu_opts = gs.sensors.IMU(
        entity_idx=robot.idx,
        link_idx_local=8,
        pos_offset=(0.0, 0.0, 0.08),
        acc_noise=0.01,
        gyro_noise=0.001,
    )
    imu = scene.add_sensor(imu_opts)

    scene.build()

    if hasattr(robot, "set_dofs_kp"):
        robot.set_dofs_kp([2000, 2000, 1500, 1500, 1200, 800, 500, 100, 100])
    if hasattr(robot, "set_dofs_kv"):
        robot.set_dofs_kv([200, 200, 150, 150, 100, 80, 50, 10, 10])

    imu_log = []

    for step in range(600):
        t = step * 0.01

        q = [
            0.0 + 0.25 * math.sin(1.0 * t),
            -0.4 + 0.35 * math.sin(0.7 * t),
            0.0 + 0.30 * math.sin(1.3 * t),
            -2.0 + 0.25 * math.sin(0.9 * t),
            0.0 + 0.20 * math.sin(1.5 * t),
            1.8 + 0.20 * math.sin(1.1 * t),
            0.7 + 0.15 * math.sin(0.8 * t),
            0.04,
            0.04,
        ]

        if hasattr(robot, "control_dofs_position"):
            robot.control_dofs_position(q)
        elif hasattr(robot, "set_dofs_position"):
            robot.set_dofs_position(q)

        scene.step()

        data = imu.read()
        lin_acc = data.lin_acc
        ang_vel = data.ang_vel

        imu_log.append(
            {
                "step": step,
                "time": t,
                "lin_acc": [float(lin_acc[0]), float(lin_acc[1]), float(lin_acc[2])],
                "ang_vel": [float(ang_vel[0]), float(ang_vel[1]), float(ang_vel[2])],
            }
        )

        if step % 50 == 0:
            print(
                f"step={step:03d} "
                f"acc=({float(lin_acc[0]): .4f}, {float(lin_acc[1]): .4f}, {float(lin_acc[2]): .4f}) "
                f"gyro=({float(ang_vel[0]): .4f}, {float(ang_vel[1]): .4f}, {float(ang_vel[2]): .4f})"
            )

    print(f"\nRecorded {len(imu_log)} IMU samples.")
    print("Last sample:", imu_log[-1])

if __name__ == "__main__":
    main()