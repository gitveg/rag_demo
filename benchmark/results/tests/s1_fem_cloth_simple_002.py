"""
User Query: A square piece of fabric is suspended in the air and falls onto a static floor.
task_id: s1_fem_cloth_simple_002
"""

import genesis as gs


def main():
    gs.init()

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(dt=0.01),
        renderer=gs.options.renderers.Rasterizer(),
    )

    scene.add_entity(
        morph=gs.morphs.Plane(),
        material=gs.materials.Rigid(rho=1000, friction=0.8, restitution=0.1),
        surface=gs.surfaces.Rough(color=(0.7, 0.7, 0.7, 1.0)),
    )

    scene.add_entity(
        morph=gs.morphs.Box(pos=(0.0, 0.0, 1.0), size=(1.0, 1.0, 0.02)),
        material=gs.materials.FEM.Cloth(
            density=0.5,
            youngs_modulus=5e4,
            poissons_ratio=0.3,
            thickness=0.01,
        ),
        surface=gs.surfaces.Default(color=(0.8, 0.2, 0.2, 1.0)),
    )

    scene.build()

    for _ in range(300):
        scene.step()


if __name__ == "__main__":
    main()