import argparse
import os
import threading

import numpy as np

import genesis as gs
from genesis.utils.geom import euler_to_quat

IS_PYNPUT_AVAILABLE = False
try:
    from pynput import keyboard

    IS_PYNPUT_AVAILABLE = True
except ImportError:
    pass

# Position and angle increments for keyboard teleop control
KEY_DPOS = 0.1
KEY_DANGLE = 0.1

# Movement when no keyboard control is available
MOVE_RADIUS = 1.0
MOVE_RATE = 1.0 / 100.0

# Number of obstacles to create in a ring around the robot
NUM_CYLINDERS = 8
NUM_BOXES = 6
CYLINDER_RING_RADIUS = 3.0
BOX_RING_RADIUS = 5.0


class KeyboardDriver:
    """Keyboard driver for moving the platform."""

    def __init__(self):
        self.pos = np.array([0.0, 0.0, 0.0])
        self.rot = np.array([0.0, 0.0, 0.0])
        self.vel = np.array([0.0, 0.0, 0.0])
        self.ang_vel = np.array([0.0, 0.0, 0.0])
        self.lock = threading.Lock()

    def update(self, pressed_keys):
        with self.lock:
            self.vel = np.zeros(3)
            self.ang_vel = np.zeros(3)
            if "w" in pressed_keys:
                self.vel[0] += KEY_DPOS
            if "s" in pressed_keys:
                self.vel[0] -= KEY_DPOS
            if "a" in pressed_keys:
                self.vel[1] += KEY_DPOS
            if "d" in pressed_keys:
                self.vel[1] -= KEY_DPOS
            if "q" in pressed_keys:
                self.ang_vel[2] += KEY_DANGLE
            if "e" in pressed_keys:
                self.ang_vel[2] -= KEY_DANGLE

    def step(self):
        with self.lock:
            self.pos += self.vel
            self.rot += self.ang_vel
            self.vel *= 0.9
            self.ang_vel *= 0.9

    def get_pose(self):
        with self.lock:
            return self.pos.copy(), self.rot.copy()


def main():
    gs.init()
    scene = gs.Scene(
        show_viewer=True,
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.0, 0.0, 1.5),
        ),
    )

    # Add floor
    scene.add_entity(
        morph=gs.options.morphs.Plane(),
    )

    # Add obstacles: cylinders
    for i in range(NUM_CYLINDERS):
        theta = 2 * np.pi * i / NUM_CYLINDERS
        x = CYLINDER_RING_RADIUS * np.cos(theta)
        y = CYLINDER_RING_RADIUS * np.sin(theta)
        scene.add_entity(
            morph=gs.options.morphs.Cylinder(
                pos=(x, y, 0.5),
                radius=0.3,
                height=1.0,
            ),
            material=gs.materials.Rigid(),
        )

    # Add obstacles: boxes
    for i in range(NUM_BOXES):
        theta = 2 * np.pi * i / NUM_BOXES
        x = BOX_RING_RADIUS * np.cos(theta)
        y = BOX_RING_RADIUS * np.sin(theta)
        scene.add_entity(
            morph=gs.options.morphs.Box(
                pos=(x, y, 0.5),
                size=(0.5, 0.5, 1.0),
            ),
            material=gs.materials.Rigid(),
        )

    # Add moving platform (robot base)
    platform = scene.add_entity(
        morph=gs.options.morphs.Box(
            pos=(0.0, 0.0, 0.1),
            size=(0.5, 0.5, 0.2),
        ),
        material=gs.materials.Rigid(),
    )

    # Add Lidar sensor attached to platform
    lidar_sensor = scene.add_sensor(
        gs.options.sensors.Lidar(
            entity=platform,
            pattern=gs.options.sensors.SphericalPattern(
                fov=(360.0, 60.0),
                n_points=(128, 64),
            ),
        )
    )

    scene.build()

    # Keyboard driver
    driver = KeyboardDriver()
    pressed_keys = set()

    if IS_PYNPUT_AVAILABLE:

        def on_press(key):
            try:
                if key.char in "wasdqee":
                    pressed_keys.add(key.char)
            except AttributeError:
                pass

        def on_release(key):
            try:
                if key.char in "wasdqee":
                    pressed_keys.discard(key.char)
            except AttributeError:
                pass

        listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        listener.start()
    else:
        print("pynput not available, platform will move automatically in a circle.")

    # Main loop
    for step in range(5000):
        # Update platform pose based on keyboard input or automatic movement
        if IS_PYNPUT_AVAILABLE:
            driver.update(pressed_keys)
            driver.step()
            pos, rot = driver.get_pose()
            quat = euler_to_quat(rot)
            platform.set_qpos(np.concatenate([pos, quat]))
        else:
            # Automatic circular movement
            t = step * MOVE_RATE
            pos = np.array([MOVE_RADIUS * np.cos(t), MOVE_RADIUS * np.sin(t), 0.1])
            rot = np.array([0, 0, t])
            quat = euler_to_quat(rot)
            platform.set_qpos(np.concatenate([pos, quat]))

        scene.step()

        # Get lidar data
        data = lidar_sensor.get_data()
        if "points" in data:
            points = data["points"]
            # Draw the point cloud as debug points
            if len(points) > 0:
                scene.draw_debug_points(
                    poss=points,
                    colors=(0.0, 1.0, 0.0, 0.5),
                )


if __name__ == "__main__":
    main()