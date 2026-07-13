import genesis as gs


def main():
    # Initialize Genesis
    gs.init(precision="32", logging_level="info")

    # Create scene with no collisions/gravity for a pure rendering setup
    scene = gs.Scene(
        rigid_options=gs.options.RigidOptions(enable_collision=False, gravity=(0, 0, 0)),
        viewer_options=gs.options.ViewerOptions(
            res=(1280, 720),
            camera_pos=(5.0, -5.0, 3.0),
            camera_lookat=(0.0, 0.0, 0.5),
            camera_fov=45,
        ),
        renderer=gs.renderers.RayTracer(
            env_surface=gs.surfaces.Emission(
                emissive_texture=gs.textures.ColorTexture(color=(1.0, 1.0, 1.0)),
            ),
            env_radius=10.0,
            lights=[
                {"pos": (5.0, 5.0, 8.0), "radius": 2.0, "color": (10.0, 10.0, 10.0)},
            ],
        ),
    )

    # Gray ground plane
    scene.add_entity(
        morph=gs.morphs.Plane(),
        material=gs.materials.Rigid(),
        surface=gs.surfaces.Default(color=(0.4, 0.4, 0.4)),
    )

    # Red metallic sphere (placed left)
    scene.add_entity(
        morph=gs.morphs.Sphere(radius=0.2, pos=(-0.5, 0.0, 0.2)),
        material=gs.materials.Rigid(),
        surface=gs.surfaces.Default(color=(0.9, 0.1, 0.1)),
    )

    # Yellow matte box (placed right, sitting on the plane)
    scene.add_entity(
        morph=gs.morphs.Box(
            pos=(0.5, 0.0, 0.1),       # half size in z to rest on plane
            size=(0.25, 0.25, 0.25),
        ),
        material=gs.materials.Rigid(),
        surface=gs.surfaces.Default(color=(1.0, 0.9, 0.2)),
    )

    # Build the scene
    scene.build()

    # Run a few steps to let the viewer initialize
    for _ in range(10):
        scene.step()

    # Keep the viewer open until closed manually
    scene.viewer.start()


if __name__ == "__main__":
    main()