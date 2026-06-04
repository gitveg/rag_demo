"""
User Query: Simulate a rigid box tumbling down a slope. Set up two cameras: one tracking the box from the side, and one from above. Record both views simultaneously as separate video files.
task_id: s1_camera_complex_001
"""

import genesis as gs


def main():
    gs.init()

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(dt=0.01),
        renderer=gs.options.renderers.Rasterizer(),
        show_viewer=False,
    )

    scene.add_entity(
        morph=gs.morphs.Plane(),
        material=gs.materials.Rigid(rho=2000, friction=0.9, restitution=0.1),
        surface=gs.surfaces.Rough(color=(0.7, 0.7, 0.7, 1.0)),
    )

    slope_angle = 0.45
    slope = scene.add_entity(
        morph=gs.morphs.Box(
            pos=(0.0, 0.0, 0.4),
            size=(6.0, 2.5, 0.2),
        ),
        material=gs.materials.Rigid(rho=2500, friction=0.8, restitution=0.05),
        surface=gs.surfaces.Iron(color=(0.45, 0.48, 0.52, 1.0)),
    )

    box = scene.add_entity(
        morph=gs.morphs.Box(
            pos=(-1.8, 0.0, 1.45),
            size=(0.35, 0.25, 0.2),
        ),
        material=gs.materials.Rigid(rho=600, friction=0.6, restitution=0.15),
        surface=gs.surfaces.Default(color=(0.85, 0.25, 0.2, 1.0)),
    )

    side_cam = scene.add_camera(
        res=(640, 480),
        pos=(-3.5, -4.0, 1.6),
        lookat=(0.0, 0.0, 0.7),
        fov=50,
    )

    top_cam = scene.add_camera(
        res=(640, 480),
        pos=(0.0, 0.0, 8.0),
        lookat=(0.0, 0.0, 0.5),
        fov=40,
    )

    side_cam.start_recording("box_side_view.mp4")
    top_cam.start_recording("box_top_view.mp4")

    scene.build()

    slope.set_qpos([0.0, 0.0, 0.4, 0.0, slope_angle, 0.0])
    box.set_qpos([-1.8, 0.0, 1.45, 0.3, 0.1, 0.2])

    n_steps = 600
    for _ in range(n_steps):
        scene.step()

        box_pos = box.get_pos()
        side_cam.set_pose(
            pos=(box_pos[0] - 2.4, box_pos[1] - 3.2, box_pos[2] + 1.0),
            lookat=(box_pos[0], box_pos[1], box_pos[2] + 0.1),
        )
        top_cam.set_pose(
            pos=(box_pos[0], box_pos[1], max(6.0, box_pos[2] + 6.0)),
            lookat=(box_pos[0], box_pos[1], box_pos[2]),
        )

        side_cam.render()
        top_cam.render()

    side_cam.stop_recording()
    top_cam.stop_recording()


if __name__ == "__main__":
    main()