import numpy as np
import genesis as gs


def main():
    ########################## init ##########################
    gs.init(seed=0, precision="32")

    ########################## create a scene ##########################
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=4e-3,
            substeps=20,
        ),
        mpm_options=gs.options.MPMOptions(
            lower_bound=(-2.0, -2.0, 0.0),
            upper_bound=(2.0, 2.0, 2.0),
        ),
        vis_options=gs.options.VisOptions(
            visualize_mpm_boundary=True,
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(1.8, -1.2, 1.5),
            camera_lookat=(0.0, 0.0, 0.4),
        ),
        show_viewer=True,
    )

    ########################## entities ##########################
    # Floor
    scene.add_entity(
        morph=gs.morphs.Plane(),
        surface=gs.options.surfaces.Rough(),
    )

    # Glass container dimensions
    c_bottom_z = 0.35
    c_height = 0.4
    c_width = 0.5
    c_depth = 0.4
    wall_t = 0.025

    # Container bottom
    scene.add_entity(
        morph=gs.morphs.Box(
            size=(c_width, c_depth, wall_t),
            pos=(0.0, 0.0, c_bottom_z),
            fixed=True,
        ),
        surface=gs.options.surfaces.Glass(),
    )

    # Container walls (left, right, front, back)
    wall_configs = [
        (-1, 0, wall_t, c_depth),    # left wall
        (1, 0, wall_t, c_depth),     # right wall
        (0, -1, c_width, wall_t),    # front wall
        (0, 1, c_width, wall_t),     # back wall
    ]
    for wx, wy, sx, sy in wall_configs:
        scene.add_entity(
            morph=gs.morphs.Box(
                size=(sx, sy, c_height),
                pos=(
                    wx * (c_width / 2 - wall_t / 2),
                    wy * (c_depth / 2 - wall_t / 2),
                    c_bottom_z + c_height / 2,
                ),
                fixed=True,
            ),
            surface=gs.options.surfaces.Glass(),
        )

    # Faucet: vertical pipe beside the container
    faucet_x = 0.35
    faucet_bottom_z = c_bottom_z + c_height
    faucet_pipe_height = 0.35

    scene.add_entity(
        morph=gs.morphs.Cylinder(
            radius=0.03,
            height=faucet_pipe_height,
            pos=(faucet_x, 0.0, faucet_bottom_z + faucet_pipe_height / 2),
            fixed=True,
        ),
        surface=gs.options.surfaces.Rough(),
    )

    # Faucet: horizontal spout extending over the container
    spout_length = 0.4
    spout_z = faucet_bottom_z + faucet_pipe_height
    scene.add_entity(
        morph=gs.morphs.Cylinder(
            radius=0.025,
            height=spout_length,
            pos=(faucet_x - spout_length / 2, 0.0, spout_z),
            fixed=True,
        ),
        surface=gs.options.surfaces.Rough(),
    )

    # Faucet: small vertical tip at the end of the spout
    tip_x = faucet_x - spout_length
    tip_height = 0.06
    scene.add_entity(
        morph=gs.morphs.Cylinder(
            radius=0.02,
            height=tip_height,
            pos=(tip_x, 0.0, spout_z - tip_height / 2),
            fixed=True,
        ),
        surface=gs.options.surfaces.Rough(),
    )

    ########################## fluid emitter (faucet water) ##########################
    scene.add_emitter(
        material=gs.materials.MPM.Liquid(rho=1000.0),
        max_particles=40000,
        surface=gs.options.surfaces.Water(),
    )

    ########################## build and run ##########################
    scene.build()

    for _ in range(1200):
        scene.step()


if __name__ == "__main__":
    main()