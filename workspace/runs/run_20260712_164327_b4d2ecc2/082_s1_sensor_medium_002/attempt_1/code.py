import numpy as np
import genesis as gs

def main():
    gs.init()

    scene = gs.Scene(
        show_viewer=True,
        show_FPS=True,
    )

    # --- Room (floor and walls) ---
    scene.add_entity(gs.morphs.Plane())

    # Add some obstacles
    obstacle_positions = [
        (2.0, 0.0, 0.5),
        (1.0, -1.5, 0.5),
        (0.0, 2.0, 0.5),
        (-1.5, 0.5, 0.5),
        (2.5, 2.0, 0.5),
        (0.5, -2.0, 0.5),
    ]
    for pos in obstacle_positions:
        scene.add_entity(
            gs.morphs.Box(pos=pos, size=(0.4, 0.4, 1.0)),
            material=gs.materials.Rigid(),
        )

    # --- Mobile robot (simple box sliding on floor) ---
    robot = scene.add_entity(
        gs.morphs.Box(pos=(0.0, 0.0, 0.25), size=(0.5, 0.5, 0.5)),
        material=gs.materials.Rigid(),
    )

    # --- LiDAR sensor on the robot ---
    # Attach to robot's base link (torso) so it moves with the robot
    lidar = scene.add_sensor(
        gs.sensors.Lidar(
            attach_to=robot,
            link_name='torso',   # default link for a simple box is named 'torso'
        )
    )

    scene.build(n_envs=0)

    # Set constant forward velocity (x direction)
    robot.set_dofs_velocity([0.2, 0.0, 0.0, 0.0, 0.0, 0.0])

    # Simulation loop
    while scene.viewer.is_alive():
        scene.step()

if __name__ == "__main__":
    main()