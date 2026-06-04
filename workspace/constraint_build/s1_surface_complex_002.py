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
            camera_pos=(6.0, -6.0, 3.0),
            camera_lookat=(0.0, 0.0, 0.5),
            camera_fov=50,
        ),
        renderer=gs.renderers.RayTracer(),
        show_viewer=True,
    )

    ########################## add entities ##########################
    # Polished floor
    floor_surface = gs.surfaces.Aluminium(color=(0.9, 0.9, 0.9))
    floor = scene.add_entity(
        morph=gs.options.morphs.Plane(),
        surface=floor_surface,
    )

    # Car body (box) with glossy paint
    car_body_surface = gs.surfaces.Smooth(color=(0.8, 0.1, 0.1))
    car_body = scene.add_entity(
        morph=gs.options.morphs.Box(
            pos=(0.0, 0.0, 0.3),
            size=(2.0, 1.0, 0.5),
        ),
        surface=car_body_surface,
    )

    # Windows (transparent reflectors)
    window_surface = gs.surfaces.Glass(color=(0.1, 0.2, 0.3, 0.5))
    # Front window
    scene.add_entity(
        morph=gs.options.morphs.Box(
            pos=(0.7, 0.0, 0.65),
            size=(0.7, 0.8, 0.3),
        ),
        surface=window_surface,
    )
    # Rear window
    scene.add_entity(
        morph=gs.options.morphs.Box(
            pos=(-0.7, 0.0, 0.65),
            size=(0.7, 0.8, 0.3),
        ),
        surface=window_surface,
    )

    # Wheels (metallic)
    wheel_surface = gs.surfaces.Aluminium(color=(0.9, 0.9, 0.9))
    wheel_positions = [
        (0.6, -0.55, 0.1),
        (0.6, 0.55, 0.1),
        (-0.6, -0.55, 0.1),
        (-0.6, 0.55, 0.1),
    ]
    for pos in wheel_positions:
        scene.add_entity(
            morph=gs.options.morphs.Cylinder(
                pos=pos,
                radius=0.18,
                height=0.3,
            ),
            surface=wheel_surface,
        )

    # Environment lights
    scene.add_mesh_light(
        morph=gs.options.morphs.Box(pos=(0.0, 0.0, 3.0), size=(0.5, 0.5, 0.1)),
        color=(1.0, 1.0, 1.0),
        intensity=15.0,
    )

    ########################## build scene ##########################
    scene.build()

    ########################## render loop ##########################
    while True:
        scene.step()


if __name__ == "__main__":
    main()