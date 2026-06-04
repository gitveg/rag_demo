"""
User Query: A soft elastic ball bounces on the ground.
task_id: s1_fem_elastic_simple_001
"""

import genesis as gs


def main():
    gs.init()

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(dt=0.01),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.0, -3.0, 2.0),
            camera_lookat=(0.0, 0.0, 0.6),
        ),
        renderer=gs.options.renderers.Rasterizer(),
    )

    scene.add_entity(
        morph=gs.morphs.Plane(),
        material=gs.materials.Rigid(rho=2000, friction=0.8, restitution=0.2),
        surface=gs.surfaces.Rough(color=(0.7, 0.7, 0.7, 1.0)),
    )

    scene.add_entity(
        morph=gs.morphs.Sphere(pos=(0.0, 0.0, 1.2), radius=0.2),
        material=gs.materials.FEM.Elastic(
            density=1000,
            youngs_modulus=1e5,
            poissons_ratio=0.3,
        ),
        surface=gs.surfaces.Default(color=(0.9, 0.2, 0.2, 1.0)),
    )

    scene.build()

    for _ in range(500):
        scene.step()


if __name__ == "__main__":
    main()