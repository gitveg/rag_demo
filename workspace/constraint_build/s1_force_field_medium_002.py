import argparse
import numpy as np
import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(backend=gs.gpu)

    ########################## create a scene ##########################
    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(0, -3.5, 2.5),
            camera_lookat=(0.0, 0.0, 1.0),
            camera_fov=40,
            max_FPS=60,
        ),
        show_viewer=args.vis,
    )

    ########################## add entities ##########################
    # ground plane
    scene.add_entity(morph=gs.morphs.Plane())

    # several boxes with different densities (lighter ones will be lifted by the force field)
    boxes = []
    positions = [
        (-0.3, -0.3, 0.05),
        (0.3, -0.3, 0.05),
        (-0.3, 0.3, 0.05),
        (0.3, 0.3, 0.05),
        (0.0, 0.0, 0.05),
    ]
    densities = [100.0, 200.0, 50.0, 300.0, 150.0]  # rho values (kg/m^3)
    for pos, rho in zip(positions, densities):
        box = scene.add_entity(
            morph=gs.morphs.Box(size=(0.1, 0.1, 0.1), pos=pos),
            material=gs.materials.Rigid(rho=rho),
        )
        boxes.append(box)

    ########################## build ##########################
    scene.build()

    ########################## simulation loop ##########################
    freq = 2.0      # oscillation frequency (Hz)
    amp = 600.0     # amplitude of upward force (N)
    dt = 0.01       # time step (assumed, we just use for time tracking)

    for i in range(1000):
        t = i * dt
        force_z = amp * np.sin(2 * np.pi * freq * t)

        # apply upward force to each box
        for box in boxes:
            box.set_force(np.array([0.0, 0.0, force_z]))

        scene.step()


if __name__ == "__main__":
    main()