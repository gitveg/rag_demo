import genesis as gs
import numpy as np

def main():
    gs.init(backend=gs.cpu, precision="32")

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=0.004,
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3, -3, 3),
            camera_lookat=(0.0, 0.0, 1.0),
        ),
        show_viewer=True,
    )

    # 地面缩小到 10x10，否则默认 1000x1000 会盖住视野、球体显得极小
    scene.add_entity(gs.morphs.Plane(plane_size=(10.0, 10.0)))

    # # 球体半径改为 0.5，更容易看到
    # scene.add_entity(
    #     morph=gs.morphs.Sphere(pos=(0, 0, 2), radius=0.5),
    #     material=gs.materials.FEM.Elastic(E=1.0e4, nu=0.45, rho=1000.0),
    #     surface=gs.surfaces.Default(color=(0.2, 0.4, 1.0, 1.0)),
    # )

    scene.add_entity(
        morph=gs.morphs.Sphere(pos=(0, 0, 2), radius=0.5),
        material=gs.materials.Rigid(),
        surface=gs.surfaces.Default(color=(0.2, 0.4, 1.0, 1.0)),
    )

    scene.build()

    horizon = 1000
    for _ in range(horizon):
        scene.step()

if __name__ == "__main__":
    main()