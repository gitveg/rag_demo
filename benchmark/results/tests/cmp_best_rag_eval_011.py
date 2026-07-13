import numpy as np
import genesis as gs

def main():
    gs.init(backend=gs.gpu)

    scene = gs.Scene(
        show_viewer=True,
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(0.0, -3.5, 2.0),
            camera_lookat=(0.25, 0.0, 0.5),
            camera_fov=40,
        ),
    )

    # Add two boxes with zero gravity compensation (effectively weightless)
    box1 = scene.add_entity(
        gs.morphs.Box(pos=(0.0, 0.0, 0.5), size=(0.2, 0.2, 0.2)),
        material=gs.materials.Rigid(gravity_compensation=1.0),
    )
    box2 = scene.add_entity(
        gs.morphs.Box(pos=(0.5, 0.0, 0.5), size=(0.2, 0.2, 0.2)),
        material=gs.materials.Rigid(gravity_compensation=1.0),
    )

    scene.build()

    # Give the left box a gentle push towards the right one
    box1.set_dofs_velocity(np.array([0.15, 0.0, 0.0, 0.0, 0.0, 0.0]))

    # Simulate for enough steps to see the collision
    for _ in range(600):
        scene.step()

if __name__ == "__main__":
    main()