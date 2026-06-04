import time
import numpy as np
import genesis as gs

def main():
    ########################## init ##########################
    gs.init(backend=gs.gpu)

    ########################## create a scene ##########################
    viewer_options = gs.options.ViewerOptions(
        camera_pos=(0.0, -0.8, 0.6),
        camera_lookat=(0.0, 0.0, 0.3),
        camera_fov=40,
        max_FPS=200,
    )

    scene = gs.Scene(
        viewer_options=viewer_options,
        show_viewer=True,
    )

    ########################## add entities ##########################

    # Narrow container: floor and four walls
    floor = scene.add_entity(
        morph=gs.morphs.Plane(pos=(0.0, 0.0, 0.0), normal=(0.0, 0.0, 1.0)),
    )

    # Left wall
    scene.add_entity(
        morph=gs.morphs.Plane(pos=(0.0, -0.2, 0.3), normal=(0.0, 1.0, 0.0)),
    )

    # Right wall
    scene.add_entity(
        morph=gs.morphs.Plane(pos=(0.0, 0.2, 0.3), normal=(0.0, -1.0, 0.0)),
    )

    # Back wall
    scene.add_entity(
        morph=gs.morphs.Plane(pos=(-0.2, 0.0, 0.3), normal=(1.0, 0.0, 0.0)),
    )

    # Front wall
    scene.add_entity(
        morph=gs.morphs.Plane(pos=(0.2, 0.0, 0.3), normal=(-1.0, 0.0, 0.0)),
    )

    # Rubber duck as soft body with high elasticity
    duck_material = gs.materials.FEM.Elastic(
        E=50000.0,      # low Young's modulus -> soft
        nu=0.45,        # near incompressible (rubber-like)
        rho=500.0,      # density
        model='linear', # linear elastic model (stable_neohookean not listed as string, use default)
    )

    duck = scene.add_entity(
        morph=gs.morphs.Mesh(
            file='duck.obj',
            pos=(0.0, 0.0, 0.8),  # above container
            scale=(1.0, 1.0, 1.0),
            euler=(0.0, 0.0, 0.0),
        ),
        material=duck_material,
    )

    ########################## build the scene ##########################
    scene.build()

    ########################## run simulation ##########################
    for i in range(2000):
        scene.step()
        time.sleep(0.01)  # slight delay to watch in viewer

if __name__ == "__main__":
    main()