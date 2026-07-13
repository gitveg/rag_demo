import genesis as gs

def main():
    gs.init(seed=0, backend=gs.gpu)

    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.0, 2.0, 2.0),
            camera_lookat=(1.0, 0.0, 0.5),
            camera_fov=40,
        ),
        show_viewer=True,
    )

    # ground plane
    scene.add_entity(gs.morphs.Plane())

    # tilted static box as a ramp
    scene.add_entity(
        gs.morphs.Box(
            pos=(1.0, 0.0, 0.2),
            euler=(0.0, -20.0, 0.0),
            size=(2.0, 0.2, 1.0),
        ),
        surface=gs.surfaces.Rough(),
    )

    # dynamic sphere at the top of the ramp
    scene.add_entity(
        gs.morphs.Sphere(
            pos=(0.3, 0.0, 0.9),
            radius=0.15,
        ),
        material=gs.materials.Rigid(),
        surface=gs.surfaces.Rough(),
    )

    # stack of three dynamic boxes at the bottom
    box_size = 0.2
    stack_x = 2.5
    stack_y = 0.0
    for i in range(3):
        z = 0.1 + i * box_size  # centers at 0.1, 0.3, 0.5
        scene.add_entity(
            gs.morphs.Box(
                pos=(stack_x, stack_y, z),
                size=(box_size, box_size, box_size),
            ),
            material=gs.materials.Rigid(),
            surface=gs.surfaces.Rough(),
        )

    scene.build()

    # simulate
    for _ in range(500):
        scene.step()

if __name__ == "__main__":
    main()