"""
User Query: Build an hourglass scene: sand fills the upper half and flows through a narrow opening into the lower half. Include glass walls so the sand stays contained.
task_id: s1_mpm_sand_complex_001
"""

import genesis as gs


def main():
    gs.init()

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(dt=0.005),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.0, -4.0, 2.4),
            camera_lookat=(0.0, 0.0, 1.0),
        ),
        renderer=gs.options.renderers.RayTracer(),
    )

    scene.add_entity(
        morph=gs.morphs.Plane(),
        material=gs.materials.Rigid(rho=1000, friction=0.8, restitution=0.1),
        surface=gs.surfaces.Rough(color=(0.85, 0.85, 0.85, 1.0)),
    )

    glass_surface = gs.surfaces.Glass(color=(0.8, 0.9, 1.0, 0.25))
    rigid_glass = gs.materials.Rigid(rho=2500, friction=0.2, restitution=0.0)

    wall_thickness = 0.04
    wall_height = 1.2
    wall_z = 0.6

    scene.add_entity(
        morph=gs.morphs.Cylinder(pos=(0.0, 0.0, wall_z), radius=0.75, height=wall_height),
        material=rigid_glass,
        surface=glass_surface,
    )

    scene.add_entity(
        morph=gs.morphs.Cylinder(pos=(0.0, 0.0, wall_z), radius=0.35, height=wall_height),
        material=rigid_glass,
        surface=glass_surface,
    )

    scene.add_entity(
        morph=gs.morphs.Box(pos=(0.0, 0.0, 0.60), size=(0.18, 0.18, 0.12)),
        material=rigid_glass,
        surface=glass_surface,
    )

    scene.add_entity(
        morph=gs.morphs.Box(pos=(0.0, 0.0, 1.05), size=(1.5, wall_thickness, 0.2)),
        material=rigid_glass,
        surface=glass_surface,
    )
    scene.add_entity(
        morph=gs.morphs.Box(pos=(0.0, 0.0, 1.05), size=(wall_thickness, 1.5, 0.2)),
        material=rigid_glass,
        surface=glass_surface,
    )

    scene.add_entity(
        morph=gs.morphs.Box(pos=(0.0, 0.0, 0.15), size=(1.5, wall_thickness, 0.2)),
        material=rigid_glass,
        surface=glass_surface,
    )
    scene.add_entity(
        morph=gs.morphs.Box(pos=(0.0, 0.0, 0.15), size=(wall_thickness, 1.5, 0.2)),
        material=rigid_glass,
        surface=glass_surface,
    )

    scene.add_entity(
        morph=gs.morphs.Box(pos=(0.0, 0.0, 1.45), size=(1.5, 1.5, 0.06)),
        material=rigid_glass,
        surface=glass_surface,
    )

    sand = scene.add_entity(
        morph=gs.morphs.Cylinder(pos=(0.0, 0.0, 1.12), radius=0.28, height=0.42),
        material=gs.materials.MPM.Sand(sampler="regular"),
        surface=gs.surfaces.Rough(color=(0.88, 0.76, 0.48, 1.0)),
    )

    scene.build()

    for _ in range(1600):
        scene.step()


if __name__ == "__main__":
    main()