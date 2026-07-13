import genesis as gs
import math

def main():
    gs.init(backend=gs.cpu)

    scene = gs.Scene()

    # Ground plane
    scene.add_entity(gs.morphs.Plane())

    # Obstacles (boxes placed arbitrarily in the room)
    obstacle_positions = [
        (2.0, 0.5, 0.3),
        (3.0, -0.8, 0.3),
        (1.5, 1.2, 0.3),
        (-1.0, -1.5, 0.3),
        (2.5, -1.8, 0.3),
    ]
    for pos in obstacle_positions:
        scene.add_entity(
            gs.morphs.Box(pos=pos, size=(0.4, 0.4, 0.4)),
            material=gs.materials.Rigid(),
        )

    # --- Mobile robot ---
    # Chassis
    robot = scene.add_entity(
        gs.morphs.Box(pos=(0.0, 0.0, 0.3), size=(0.4, 0.6, 0.2)),
        material=gs.materials.Rigid(),
    )

    # Wheel geometry
    wheel_radius = 0.12
    wheel_width = 0.05
    # Cylinder default axis is Z, we rotate so axis is Y (wheel spins around Y)
    wheel_orientation = gs.utils.quat_from_euler([math.pi/2, 0.0, 0.0])

    left_wheel = scene.add_entity(
        gs.morphs.Cylinder(
            pos=(-0.2, -0.35, wheel_radius),
            radius=wheel_radius,
            height=wheel_width,
            orientation=wheel_orientation,
        ),
        material=gs.materials.Rigid(),
    )
    right_wheel = scene.add_entity(
        gs.morphs.Cylinder(
            pos=(0.2, -0.35, wheel_radius),
            radius=wheel_radius,
            height=wheel_width,
            orientation=wheel_orientation,
        ),
        material=gs.materials.Rigid(),
    )

    # Revolute joints for the wheels
    motor_left = scene.add_joint(
        "revolute",
        left_wheel,
        robot,
        pivot=(-0.2, -0.35, wheel_radius),
        axis=(0.0, 1.0, 0.0),
    )
    motor_right = scene.add_joint(
        "revolute",
        right_wheel,
        robot,
        pivot=(0.2, -0.35, wheel_radius),
        axis=(0.0, 1.0, 0.0),
    )

    # Lidar sensor mounted on top of the robot
    lidar = scene.add_sensor(
        gs.sensors.Lidar(
            pos=(0.0, 0.0, 0.3),
            parent=robot,
            range_max=5.0,
            n_rays=360,
            angle_min=-math.pi,
            angle_max=math.pi,
        ),
    )

    scene.build()

    # Move forward with constant wheel velocity
    for step in range(1000):
        motor_left.set_velocity(5.0)
        motor_right.set_velocity(5.0)

        scene.step()

        # Read lidar ranges every 10 steps
        if step % 10 == 0:
            ranges = lidar.get_data()["ranges"]
            print(f"Step {step}: {ranges[:5]}")

    scene.viewer.stop()

if __name__ == "__main__":
    main()