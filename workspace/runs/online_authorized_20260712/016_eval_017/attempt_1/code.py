import genesis as gs


def main():
    gs.init()

    scene = gs.Scene(
        rigid_options=gs.options.RigidOptions(
            dt=0.01,
            gravity=(0.0, 0.0, -10.0),
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.5, 0.0, 2.5),
            camera_lookat=(0.0, 0.0, 0.5),
            camera_fov=40,
            run_in_thread=False,
        ),
        show_viewer=True,
        show_FPS=True,
    )

    # Ground plane
    plane = scene.add_entity(gs.morphs.Plane())

    # Franka robot from XML file
    robot = scene.add_entity(
        gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
    )

    # Red rigid box placed on the ground in front of the robot
    box = scene.add_entity(
        morph=gs.morphs.Box(
            pos=(0.5, 0.0, 0.025),   # half of box height to sit on the plane
            size=(0.05, 0.05, 0.05),
            fixed=True,
        ),
        material=gs.materials.Rigid(),
        surface=gs.surfaces.Plastic(color=(1.0, 0.0, 0.0, 1.0)),
    )

    scene.build()

    # Run the simulation for some steps so the viewer can be observed
    for _ in range(1000):
        scene.step()


if __name__ == "__main__":
    main()