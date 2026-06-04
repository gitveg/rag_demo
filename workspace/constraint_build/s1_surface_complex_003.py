import torch
import genesis as gs


def main():
    gs.init(precision="32", logging_level="info")

    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            res=(1920, 1080),
            camera_pos=(8.0, 0.0, 4.0),
            camera_lookat=(0.0, 0.0, 0.0),
            camera_fov=40,
        ),
        renderer=gs.renderers.RayTracer(),
        show_viewer=True,
    )

    # Gold torus with polished (low roughness) surface
    gold_surface = gs.options.surfaces.Gold(roughness=0.05)
    scene.add_entity(
        morph=gs.options.morphs.Torus(pos=(1.5, 0.0, 0.0)),
        surface=gold_surface,
    )

    # Semi-transparent glass sphere with slightly frosted (moderate roughness) surface
    glass_surface = gs.options.surfaces.Glass(roughness=0.3)
    scene.add_entity(
        morph=gs.options.morphs.Sphere(pos=(-1.5, 0.0, 0.0), radius=0.8),
        surface=glass_surface,
    )

    scene.build()

    # Run a few steps to let the visualizer refresh
    for _ in range(100):
        scene.step()


if __name__ == "__main__":
    main()