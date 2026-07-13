import numpy as np
import genesis as gs

def main():
    gs.init(backend=gs.cpu)

    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3, -2, 2),
            camera_lookat=(0.0, 0.0, 0.5),
            max_FPS=60,
        ),
    )

    scene.add_entity(gs.morphs.Plane())

    # Place several boxes on the ground
    box_count = 5
    boxes = []
    for i in range(box_count):
        x = (i - (box_count - 1) / 2) * 0.2
        box = scene.add_entity(
            gs.morphs.Box(pos=(x, 0.0, 0.05), size=(0.1, 0.1, 0.1))
        )
        boxes.append(box)

    scene.build()

    # Pulsing upward force
    pulse_amplitude = 5.0
    pulse_frequency = 1.0

    for step in range(600):
        t = step * 0.01
        upward_force = pulse_amplitude * np.sin(2 * np.pi * pulse_frequency * t)
        for box in boxes:
            box.set_force([0.0, 0.0, upward_force])
        scene.step()

if __name__ == "__main__":
    main()