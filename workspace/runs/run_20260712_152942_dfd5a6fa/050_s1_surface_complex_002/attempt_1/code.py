import torch

import genesis as gs


def main():
    ########################## init ##########################
    gs.init(precision="32", logging_level="info")

    ########################## create a scene ##########################
    scene = gs.Scene(
        rigid_options=gs.options.RigidOptions(enable_collision=False, gravity=(0, 0, 0)),
        viewer_options=gs.options.ViewerOptions(
            res=(1920, 1080),
            camera_pos=(5.0, 5.0, 3.0),
            camera_lookat=(0.0, 0.0, 0.6),
            camera_fov=50,
        ),
        renderer=gs.renderers.RayTracer(  # type: ignore
            env_surface=gs.surfaces.Emission(
                emissive_texture=gs.textures.ImageTexture(
                    image_path="textures/indoor_bright.png",
                ),
            ),
            env_radius=15.0,
            env_euler=(0, 0, 180),
            lights=[
                {"pos": (0.0, 0.0, 10.0), "radius": 3.0, "color": (15.0, 15.0, 15.0)},
            ],
            # remaining parameters are left at their defaults
        ),
        show_viewer=True,
    )

    ########################## add entities ##########################
    # Polished floor
    scene.add_entity(
        morph=gs.morphs.Plane(),
        surface=gs.surfaces.Plastic(color=(0.1, 0.1, 0.1, 1.0)),
    )

    # Sports car model (glossy paint)
    scene.add_entity(
        morph=gs.morphs.Mesh(
            file="meshes/sports_car.obj",
            pos=(0.0, 0.0, 0.5),
            scale=(1.0, 1.0, 1.0),
        ),
        material=gs.materials.Rigid(rho=500),
        surface=gs.surfaces.Plastic(color=(0.8, 0.1, 0.1, 1.0)),
        # Windows and wheels are part of the same mesh;
        # for a real demo separate subparts would be needed.
    )

    ########################## build and run ##########################
    scene.build(n_envs=0)

    # Record a short clip
    scene.reset()
    scene.start_recording()
    for _ in range(120):
        scene.step()
    scene.viewer.save_video("showroom.mp4")


if __name__ == "__main__":
    main()