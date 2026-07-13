import argparse
import numpy as np
import genesis as gs

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=True)
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(precision="32")

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=2e-3,
        ),
        sph_options=gs.options.SPHOptions(
            lower_bound=(-1.0, -1.0, 0.0),
            upper_bound=(1.0, 1.0, 1.0),
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(1.5, 2.0, 1.2),
            camera_lookat=(0.0, 0.0, 0.2),
            camera_fov=40,
        ),
        show_viewer=args.vis,
    )

    ########################## bowl (rigid container) ##########################
    # Bottom plate
    scene.add_entity(
        material=gs.materials.Rigid(),
        morph=gs.morphs.Box(pos=(0.0, 0.0, 0.0), size=(0.32, 0.32, 0.01)),
        surface=gs.surfaces.Default(color=(0.7, 0.7, 0.7)),
    )
    # Walls
    wall_thickness = 0.02
    wall_height = 0.3
    wall_positions = [
        (-0.32, 0.0, wall_height/2),   # left
        (0.32, 0.0, wall_height/2),    # right
        (0.0, 0.32, wall_height/2),    # front
        (0.0, -0.32, wall_height/2),   # back
    ]
    wall_sizes = [
        (wall_thickness, 0.66, wall_height),  # left/right
        (wall_thickness, 0.66, wall_height),
        (0.66, wall_thickness, wall_height),
        (0.66, wall_thickness, wall_height),
    ]
    for i in range(4):
        scene.add_entity(
            material=gs.materials.Rigid(),
            morph=gs.morphs.Box(pos=wall_positions[i], size=wall_sizes[i]),
            surface=gs.surfaces.Default(color=(0.7, 0.7, 0.7)),
        )

    ########################## liquid streams (two blocks) ##########################
    # Left stream (red)
    scene.add_entity(
        material=gs.materials.SPH.Liquid(mu=0.01),
        morph=gs.morphs.Box(lower=(-0.40, -0.08, 0.35), upper=(-0.25, 0.08, 0.45)),
        surface=gs.surfaces.Default(color=(1.0, 0.2, 0.3, 1.0), vis_mode="particle"),
    )
    # Right stream (blue)
    scene.add_entity(
        material=gs.materials.SPH.Liquid(mu=0.01),
        morph=gs.morphs.Box(lower=(0.25, -0.08, 0.35), upper=(0.40, 0.08, 0.45)),
        surface=gs.surfaces.Default(color=(0.2, 0.4, 1.0, 1.0), vis_mode="particle"),
    )

    ########################## build & run ##########################
    scene.build(n_envs=0)

    if args.vis:
        scene.start_recording()

    # Simulate for 3 seconds (1500 steps)
    for _ in range(1500):
        scene.step()

    if args.vis:
        scene.viewer.save_video("mixing_liquids.mp4")

if __name__ == "__main__":
    main()