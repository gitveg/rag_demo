import os
import numpy as np
import genesis as gs


def main():
    gs.init(precision="32", logging_level="info")

    # Create the simulation scene with both MPM and rigid body solvers
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=4e-3,
            substeps=10,
        ),
        mpm_options=gs.options.MPMOptions(
            lower_bound=(-1.0, -0.5, 0.0),
            upper_bound=(1.0, 0.5, 1.5),
        ),
        rigid_options=gs.options.RigidOptions(
            dt=4e-3,
            enable_collision=True,
            gravity=(0, 0, -9.8),
        ),
        vis_options=gs.options.VisOptions(
            visualize_mpm_boundary=True,
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(0.5, -1.5, 1.0),
            camera_lookat=(0.0, 0.0, 0.3),
            camera_fov=30,
        ),
        show_viewer=True,
    )

    # ----- Bowl: static rigid objects forming an open-top container -----
    # Floor
    scene.add_entity(gs.morphs.Plane())

    # Walls (thin boxes)
    scene.add_entity(
        gs.morphs.Box(pos=(-0.5, 0.0, 0.25), size=(0.05, 1.0, 0.5))
    )
    scene.add_entity(
        gs.morphs.Box(pos=(0.5, 0.0, 0.25), size=(0.05, 1.0, 0.5))
    )
    scene.add_entity(
        gs.morphs.Box(pos=(0.0, -0.5, 0.25), size=(1.0, 0.05, 0.5))
    )
    scene.add_entity(
        gs.morphs.Box(pos=(0.0, 0.5, 0.25), size=(1.0, 0.05, 0.5))
    )

    # ----- Liquid emitters with different colors -----
    liquid_material = gs.materials.MPM.Liquid()

    # Red liquid – left side
    emitter_left = scene.add_emitter(
        material=liquid_material,
        max_particles=10000,
        surface=gs.options.surfaces.Rough(color=(1.0, 0.0, 0.0, 1.0)),
    )
    emitter_left.pos = np.array([-0.6, 0.0, 0.8])
    emitter_left.vel = np.array([2.0, 0.0, 0.0])

    # Blue liquid – right side
    emitter_right = scene.add_emitter(
        material=liquid_material,
        max_particles=10000,
        surface=gs.options.surfaces.Rough(color=(0.0, 0.0, 1.0, 1.0)),
    )
    emitter_right.pos = np.array([0.6, 0.0, 0.8])
    emitter_right.vel = np.array([-2.0, 0.0, 0.0])

    # Build and run simulation
    scene.build()

    for _ in range(500):
        scene.step()


if __name__ == "__main__":
    main()