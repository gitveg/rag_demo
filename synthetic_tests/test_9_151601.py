"""
User Query: Configure an MPM emitter with a velocity field defined by a mathematical function (e.g., a vortex) and limit the total number of particles emitted to a fixed budget.
"""

import argparse
import numpy as np
import genesis as gs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(precision="32", logging_level="info")

    ########################## create a scene ##########################
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=4e-3,
            substeps=20,
        ),
        mpm_options=gs.options.MPMOptions(
            lower_bound=(-1.0, -1.0, -0.1),
            upper_bound=(1.0, 1.0, 1.0),
            grid_density=64,
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(4.5, 1.0, 1.42),
            camera_lookat=(0.0, 0.0, 0.3),
            camera_fov=22,
            max_FPS=120,
        ),
        show_viewer=args.vis,
        vis_options=gs.options.VisOptions(),
    )

    ########################## define velocity field ##########################
    def vortex_velocity(position):
        # Example: 2D vortex in the xy‑plane
        x, y, z = position
        r = np.sqrt(x**2 + y**2)
        vx = -y / (r + 1e-6)
        vy =  x / (r + 1e-6)
        vz = 0.0
        return np.array([vx, vy, vz])

    ########################## add MPM emitter ##########################
    material = gs.materials.MPM.Base()
    max_particles = 10000   # fixed particle budget
    emitter = scene.add_emitter(material=material, max_particles=max_particles)

    ########################## build and run ##########################
    scene.build()
    for _ in range(100):
        scene.step()


if __name__ == "__main__":
    main()