import numpy as np
import genesis as gs
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    args = parser.parse_args()

    # Initialize
    gs.init(precision="32", logging_level="info")

    # Scene configuration
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=4e-3,
            substeps=20,
        ),
        mpm_options=gs.options.MPMOptions(
            lower_bound=(-0.6, -0.6, -0.1),
            upper_bound=(0.6, 0.6, 1.2),
            grid_density=64,
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(2.0, 2.0, 1.5),
            camera_lookat=(0.0, 0.0, 0.3),
            camera_fov=40,
            max_FPS=60,
        ),
        show_viewer=args.vis,
    )

    # ---------- Environment ----------
    # Floor (large flat box)
    scene.add_entity(
        material=gs.materials.Rigid(),
        morph=gs.morphs.Box(pos=(0, 0, -0.05), size=(2.0, 2.0, 0.1)),
        surface=gs.surfaces.Default(color=(0.5, 0.5, 0.5, 1.0)),
    )

    # ---------- Sink basin (transparent container) ----------
    # Bottom
    scene.add_entity(
        material=gs.materials.Rigid(),
        morph=gs.morphs.Box(pos=(0, 0, 0.175), size=(0.5, 0.5, 0.05)),
        surface=gs.surfaces.Default(color=(0.9, 0.95, 1.0, 0.4)),
    )
    # Walls
    wall_thick = 0.02
    wall_height = 0.3
    wall_base_z = 0.35  # center z of wall (0.2 + 0.15)
    basin_size = 0.5  # inner length from -0.25 to 0.25

    # Left wall
    scene.add_entity(
        material=gs.materials.Rigid(),
        morph=gs.morphs.Box(pos=(-0.25, 0, wall_base_z), size=(wall_thick, basin_size, wall_height)),
        surface=gs.surfaces.Default(color=(0.9, 0.95, 1.0, 0.4)),
    )
    # Right wall
    scene.add_entity(
        material=gs.materials.Rigid(),
        morph=gs.morphs.Box(pos=(0.25, 0, wall_base_z), size=(wall_thick, basin_size, wall_height)),
        surface=gs.surfaces.Default(color=(0.9, 0.95, 1.0, 0.4)),
    )
    # Front wall
    scene.add_entity(
        material=gs.materials.Rigid(),
        morph=gs.morphs.Box(pos=(0, -0.25, wall_base_z), size=(basin_size, wall_thick, wall_height)),
        surface=gs.surfaces.Default(color=(0.9, 0.95, 1.0, 0.4)),
    )
    # Back wall
    scene.add_entity(
        material=gs.materials.Rigid(),
        morph=gs.morphs.Box(pos=(0, 0.25, wall_base_z), size=(basin_size, wall_thick, wall_height)),
        surface=gs.surfaces.Default(color=(0.9, 0.95, 1.0, 0.4)),
    )

    # ---------- Faucet ----------
    # Spout (small box above the sink)
    faucet_pos = (0.0, 0.0, 0.75)
    scene.add_entity(
        material=gs.materials.Rigid(),
        morph=gs.morphs.Box(pos=faucet_pos, size=(0.06, 0.06, 0.1)),
        surface=gs.surfaces.Default(color=(0.4, 0.4, 0.4, 1.0)),
    )
    # Arm connecting faucet to a stand (optional)
    scene.add_entity(
        material=gs.materials.Rigid(),
        morph=gs.morphs.Box(pos=(-0.2, 0.0, 0.7), size=(0.05, 0.05, 0.4)),
        surface=gs.surfaces.Default(color=(0.4, 0.4, 0.4, 1.0)),
    )

    # ---------- Water emitter (continuous flow) ----------
    emitter = scene.add_emitter(
        material=gs.materials.MPM.Liquid(),
        max_particles=50000,
        surface=gs.surfaces.Default(
            color=(0.2, 0.5, 1.0, 1.0),
            vis_mode="particle",
        ),
    )
    emitter.set_rate(500)
    emitter.set_velocity(np.array([0.0, 0.0, -2.0]))
    emitter.set_position(np.array([faucet_pos[0], faucet_pos[1], faucet_pos[2] - 0.05]))

    # ---------- Build and run ----------
    scene.build(n_envs=0)

    while True:
        scene.step()

if __name__ == "__main__":
    main()