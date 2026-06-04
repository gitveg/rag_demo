"""
User Query: Apply a constant upward force to a sphere to counteract gravity so it hovers in place.
task_id: s1_force_field_simple_003
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
        surface=gs.surfaces.Rough(color=(0.6, 0.6, 0.6, 1.0)),
    )

    sphere = scene.add_entity(
        morph=gs.morphs.Sphere(pos=(0.0, 0.0, 1.0), radius=0.2),
        material=gs.materials.Rigid(rho=1000, friction=0.4, restitution=0.1),
        surface=gs.surfaces.Default(color=(0.2, 0.6, 1.0, 1.0)),
    )

    scene.add_camera(
        pos=(3.0, -3.0, 2.0),
        lookat=(0.0, 0.0, 1.0),
        resolution=(1280, 720),
    )

    scene.add_force_field(
        gs.options.ForceField(
            type="constant",
            direction=(0.0, 0.0, 1.0),
            strength=9.81,
        )
    )

    scene.build()

    for i in range(500):
        scene.step()
        if i % 50 == 0:
            print(f"step={i}")

    print("Simulation finished.")


if __name__ == "__main__":
    main()