import genesis as gs

def main():
    gs.init()

    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.5, 0.0, 2.5),
            camera_lookat=(0.0, 0.0, 1.0),
        ),
    )

    # Ground plane
    scene.add_entity(gs.morphs.Plane())

    # Two rigid spheres side by side
    sphere1 = scene.add_entity(
        gs.morphs.Sphere(radius=0.2, pos=(-0.3, 0.0, 0.5)),
        material=gs.materials.Rigid(),
    )
    sphere2 = scene.add_entity(
        gs.morphs.Sphere(radius=0.2, pos=(0.3, 0.0, 0.5)),
        material=gs.materials.Rigid(),
    )

    scene.build()

    # Run simulation
    import numpy as np
    for i in range(1000):
        scene.step()

if __name__ == "__main__":
    main()