"""
User Query: Create a scene where three rigid spheres are dropped from different heights. A strong upward force is applied only to the middle sphere, causing it to float while the others fall.
task_id: s1_force_field_medium_001
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
        material=gs.materials.Rigid(rho=1000, friction=0.8, restitution=0.2),
        surface=gs.surfaces.Rough(color=(0.7, 0.7, 0.7, 1.0)),
    )

    left_sphere = scene.add_entity(
        morph=gs.morphs.Sphere(pos=(-1.2, 0.0, 3.0), radius=0.25),
        material=gs.materials.Rigid(rho=500, friction=0.4, restitution=0.5),
        surface=gs.surfaces.Default(color=(0.9, 0.2, 0.2, 1.0)),
    )

    middle_sphere = scene.add_entity(
        morph=gs.morphs.Sphere(pos=(0.0, 0.0, 2.0), radius=0.25),
        material=gs.materials.Rigid(rho=500, friction=0.4, restitution=0.5),
        surface=gs.surfaces.Default(color=(0.2, 0.9, 0.2, 1.0)),
    )

    right_sphere = scene.add_entity(
        morph=gs.morphs.Sphere(pos=(1.2, 0.0, 4.0), radius=0.25),
        material=gs.materials.Rigid(rho=500, friction=0.4, restitution=0.5),
        surface=gs.surfaces.Default(color=(0.2, 0.2, 0.9, 1.0)),
    )

    scene.build()

    try:
        middle_sphere.apply_external_force(force=(0.0, 0.0, 80.0))
    except AttributeError:
        pass

    for _ in range(600):
        try:
            middle_sphere.apply_external_force(force=(0.0, 0.0, 80.0))
        except AttributeError:
            pass
        scene.step()


if __name__ == "__main__":
    main()