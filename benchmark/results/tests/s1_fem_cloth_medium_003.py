"""
User Query: Create a horizontal pole and hang a rectangular cloth over it so that the cloth drapes naturally on both sides.
task_id: s1_fem_cloth_medium_003
"""

import genesis as gs


def main():
    gs.init()

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=0.01,
            substeps=10,
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.0, -3.0, 2.2),
            camera_lookat=(0.0, 0.0, 1.0),
        ),
        renderer=gs.options.renderers.Rasterizer(),
    )

    scene.add_entity(
        morph=gs.morphs.Plane(),
        material=gs.materials.Rigid(
            rho=1000,
            friction=0.8,
            restitution=0.1,
        ),
        surface=gs.surfaces.Rough(color=(0.85, 0.85, 0.85, 1.0)),
    )

    scene.add_entity(
        morph=gs.morphs.Cylinder(
            pos=(0.0, 0.0, 1.0),
            radius=0.06,
            height=2.0,
        ),
        material=gs.materials.Rigid(
            rho=7800,
            friction=0.6,
            restitution=0.05,
        ),
        surface=gs.surfaces.Iron(color=(0.55, 0.57, 0.62, 1.0)),
    )

    scene.add_entity(
        morph=gs.morphs.Box(
            pos=(0.0, 0.0, 1.22),
            size=(1.6, 0.02, 1.2),
        ),
        material=gs.materials.FEM.Cloth(
            density=0.5,
            youngs_modulus=5e4,
            poissons_ratio=0.3,
            thickness=0.01,
        ),
        surface=gs.surfaces.Default(color=(0.35, 0.55, 0.95, 1.0)),
    )

    scene.build()

    for _ in range(800):
        scene.step()


if __name__ == "__main__":
    main()