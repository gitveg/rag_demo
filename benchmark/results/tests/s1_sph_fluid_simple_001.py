"""
User Query: A blob of water falls into a shallow basin.
task_id: s1_sph_fluid_simple_001
"""

import genesis as gs


def main():
    gs.init()

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=0.005,
            substeps=10,
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.5, -3.5, 2.2),
            camera_lookat=(0.0, 0.0, 0.5),
        ),
        renderer=gs.options.renderers.Rasterizer(),
    )

    scene.add_entity(
        gs.Entity(
            morph=gs.morphs.Plane(),
            material=gs.materials.Rigid(
                rho=1000,
                friction=0.8,
                restitution=0.1,
            ),
            surface=gs.surfaces.Rough(color=(0.7, 0.7, 0.72, 1.0)),
        )
    )

    wall_thickness = 0.12
    basin_size = 1.6
    wall_height = 0.35
    floor_height = 0.06

    scene.add_entity(
        gs.Entity(
            morph=gs.morphs.Box(
                pos=(0.0, 0.0, floor_height * 0.5),
                size=(basin_size, basin_size, floor_height),
            ),
            material=gs.materials.Rigid(
                rho=1200,
                friction=0.9,
                restitution=0.05,
            ),
            surface=gs.surfaces.Iron(color=(0.45, 0.47, 0.5, 1.0)),
        )
    )

    half = basin_size * 0.5
    wall_z = floor_height + wall_height * 0.5

    wall_positions_sizes = [
        ((half - wall_thickness * 0.5, 0.0, wall_z), (wall_thickness, basin_size, wall_height)),
        ((-half + wall_thickness * 0.5, 0.0, wall_z), (wall_thickness, basin_size, wall_height)),
        ((0.0, half - wall_thickness * 0.5, wall_z), (basin_size, wall_thickness, wall_height)),
        ((0.0, -half + wall_thickness * 0.5, wall_z), (basin_size, wall_thickness, wall_height)),
    ]

    for pos, size in wall_positions_sizes:
        scene.add_entity(
            gs.Entity(
                morph=gs.morphs.Box(pos=pos, size=size),
                material=gs.materials.Rigid(
                    rho=1200,
                    friction=0.9,
                    restitution=0.05,
                ),
                surface=gs.surfaces.Iron(color=(0.45, 0.47, 0.5, 1.0)),
            )
        )

    scene.add_entity(
        gs.Entity(
            morph=gs.morphs.Box(
                pos=(0.0, 0.0, 0.16),
                size=(1.05, 1.05, 0.12),
            ),
            material=gs.materials.SPH.Liquid(sampler="regular"),
            surface=gs.surfaces.Glass(color=(0.3, 0.55, 0.95, 0.5)),
        )
    )

    scene.add_entity(
        gs.Entity(
            morph=gs.morphs.Sphere(
                pos=(0.0, 0.0, 1.1),
                radius=0.22,
            ),
            material=gs.materials.SPH.Liquid(sampler="regular"),
            surface=gs.surfaces.Glass(color=(0.2, 0.5, 1.0, 0.5)),
        )
    )

    scene.add_camera(
        res=(1280, 720),
        pos=(3.2, -3.0, 2.0),
        lookat=(0.0, 0.0, 0.45),
        fov=45,
    )

    scene.build()

    for _ in range(900):
        scene.step()


if __name__ == "__main__":
    main()