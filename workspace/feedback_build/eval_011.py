import numpy as np
import genesis as gs


def main():
    gs.init(backend=gs.cpu, precision="32")

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(dt=0.01),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(0, -5.5, 2.5),
            camera_lookat=(0, 0.0, 1.5),
            max_FPS=60,
        ),
        show_viewer=True,
    )

    plane = scene.add_entity(gs.morphs.Plane())

    box1 = scene.add_entity(
        morph=gs.morphs.Box(pos=(0, -1.0, 0.5), size=(0.2, 0.2, 0.2)),
        material=gs.materials.Rigid(rho=300, gravity_compensation=1.0),
        surface=gs.surfaces.Default(color=(0.5, 1, 0.5)),
    )
    box2 = scene.add_entity(
        morph=gs.morphs.Box(pos=(0, 1.0, 0.5), size=(0.2, 0.2, 0.2)),
        material=gs.materials.Rigid(rho=300, gravity_compensation=1.0),
        surface=gs.surfaces.Default(color=(0.5, 0.5, 1)),
    )

    scene.build()

    box1.set_velocity(lin_vel=(0.0, 0.3, 0.0), ang_vel=(0.0, 0.0, 0.0))
    box2.set_velocity(lin_vel=(0.0, -0.3, 0.0), ang_vel=(0.0, 0.0, 0.0))

    for _ in range(200):
        scene.step()


if __name__ == "__main__":
    main()