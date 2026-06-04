"""
User Query: Drop a heavy rigid metallic sphere into a tank filled with water and observe the splash and the sphere sinking.
task_id: s1_cross_domain_complex_004
"""

import genesis as gs


def main():
    gs.init()

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=0.005,
            substeps=10,
            gravity=(0.0, 0.0, -9.81),
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(4.5, -4.5, 3.0),
            camera_lookat=(0.0, 0.0, 0.8),
        ),
        renderer=gs.options.renderers.Rasterizer(),
    )

    scene.add_entity(
        morph=gs.morphs.Plane(),
        material=gs.materials.Rigid(rho=2000, friction=0.8, restitution=0.1),
        surface=gs.surfaces.Rough(color=(0.75, 0.75, 0.75, 1.0)),
    )

    wall_thickness = 0.08
    tank_size = 2.0
    wall_height = 1.4
    floor_z = wall_thickness * 0.5

    rigid_glass = gs.materials.Rigid(rho=2500, friction=0.4, restitution=0.05)
    glass_surface = gs.surfaces.Glass(color=(0.8, 0.9, 1.0, 0.35))

    scene.add_entity(
        morph=gs.morphs.Box(
            pos=(0.0, 0.0, floor_z),
            size=(tank_size, tank_size, wall_thickness),
        ),
        material=rigid_glass,
        surface=glass_surface,
    )

    scene.add_entity(
        morph=gs.morphs.Box(
            pos=(tank_size * 0.5 + wall_thickness * 0.5, 0.0, wall_height * 0.5),
            size=(wall_thickness, tank_size, wall_height),
        ),
        material=rigid_glass,
        surface=glass_surface,
    )

    scene.add_entity(
        morph=gs.morphs.Box(
            pos=(-(tank_size * 0.5 + wall_thickness * 0.5), 0.0, wall_height * 0.5),
            size=(wall_thickness, tank_size, wall_height),
        ),
        material=rigid_glass,
        surface=glass_surface,
    )

    scene.add_entity(
        morph=gs.morphs.Box(
            pos=(0.0, tank_size * 0.5 + wall_thickness * 0.5, wall_height * 0.5),
            size=(tank_size + 2 * wall_thickness, wall_thickness, wall_height),
        ),
        material=rigid_glass,
        surface=glass_surface,
    )

    scene.add_entity(
        morph=gs.morphs.Box(
            pos=(0.0, -(tank_size * 0.5 + wall_thickness * 0.5), wall_height * 0.5),
            size=(tank_size + 2 * wall_thickness, wall_thickness, wall_height),
        ),
        material=rigid_glass,
        surface=glass_surface,
    )

    liquid = scene.add_entity(
        morph=gs.morphs.Box(
            pos=(0.0, 0.0, 0.45),
            size=(1.7, 1.7, 0.8),
        ),
        material=gs.materials.SPH.Liquid(sampler="regular"),
        surface=gs.surfaces.Glass(color=(0.35, 0.6, 0.95, 0.5)),
    )

    sphere = scene.add_entity(
        morph=gs.morphs.Sphere(
            pos=(0.0, 0.0, 1.8),
            radius=0.18,
        ),
        material=gs.materials.Rigid(rho=7800, friction=0.3, restitution=0.05),
        surface=gs.surfaces.Iron(color=(0.55, 0.57, 0.62, 1.0)),
    )

    scene.add_camera(
        res=(1280, 720),
        pos=(4.5, -4.5, 3.0),
        lookat=(0.0, 0.0, 0.8),
        fov=40,
    )

    scene.build()

    for _ in range(800):
        scene.step()


if __name__ == "__main__":
    main()