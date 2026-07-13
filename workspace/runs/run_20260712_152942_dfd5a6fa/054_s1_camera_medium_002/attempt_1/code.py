import genesis as gs


def main():
    gs.init()

    scene = gs.Scene(
        vis_options=gs.options.VisOptions(rendered_envs_idx=(0,)),
        profiling_options=gs.options.ProfilingOptions(show_FPS=False),
        show_viewer=True,
    )

    # ground plane
    scene.add_entity(gs.morphs.Plane())

    # two moving cubes
    cube1 = scene.add_entity(
        gs.morphs.Box(size=(0.1, 0.1, 0.1), pos=(0.0, -0.5, 0.5))
    )
    cube2 = scene.add_entity(
        gs.morphs.Box(size=(0.1, 0.1, 0.1), pos=(0.5, 0.0, 0.5))
    )

    # top‑down camera
    cam_top = scene.add_camera(
        res=(640, 480),
        pos=(0.0, 0.0, 3.0),
        lookat=(0.0, 0.0, 0.5),
        fov=40,
        GUI=True,
    )

    # ground‑level camera
    cam_ground = scene.add_camera(
        res=(640, 480),
        pos=(3.0, 0.0, 0.2),
        lookat=(0.0, 0.0, 0.5),
        fov=40,
        GUI=True,
    )

    scene.build()

    cube1.set_dofs_velocity([0.0, 2.0, 0.0, 0.0, 0.0, 0.0])
    cube2.set_dofs_velocity([-1.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    for _ in range(200):
        scene.step()


if __name__ == "__main__":
    main()