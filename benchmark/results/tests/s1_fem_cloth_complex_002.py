"""
User Query: Use a cloth mesh (gs.morphs.Mesh(file="meshes/cloth.obj")) to create a tablecloth over a box table. Drop several rigid cubes onto the cloth and observe realistic folds and deformation.
task_id: s1_fem_cloth_complex_002
"""

import genesis as gs


def main():
    gs.init()

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=0.005,
            substeps=10,
            gravity=(0, 0, -9.81),
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(3.5, -3.0, 2.2),
            camera_lookat=(0.0, 0.0, 0.7),
        ),
        renderer=gs.options.renderers.RayTracer(),
    )

    scene.add_entity(
        morph=gs.morphs.Plane(),
        material=gs.materials.Rigid(rho=2000, friction=0.9, restitution=0.1),
        surface=gs.surfaces.Rough(color=(0.82, 0.82, 0.82, 1.0)),
    )

    table_height = 0.55
    tabletop_thickness = 0.08
    tabletop_size = (1.4, 1.0, tabletop_thickness)

    scene.add_entity(
        morph=gs.morphs.Box(
            pos=(0.0, 0.0, table_height - tabletop_thickness * 0.5),
            size=tabletop_size,
        ),
        material=gs.materials.Rigid(rho=900, friction=0.8, restitution=0.05),
        surface=gs.surfaces.Iron(color=(0.45, 0.33, 0.22, 1.0)),
    )

    leg_size = (0.08, 0.08, table_height - tabletop_thickness)
    leg_z = (table_height - tabletop_thickness) * 0.5
    leg_offsets = [
        (0.58, 0.38),
        (0.58, -0.38),
        (-0.58, 0.38),
        (-0.58, -0.38),
    ]
    for lx, ly in leg_offsets:
        scene.add_entity(
            morph=gs.morphs.Box(
                pos=(lx, ly, leg_z),
                size=leg_size,
            ),
            material=gs.materials.Rigid(rho=900, friction=0.8, restitution=0.05),
            surface=gs.surfaces.Iron(color=(0.38, 0.27, 0.18, 1.0)),
        )

    scene.add_entity(
        morph=gs.morphs.Mesh(
            file="meshes/cloth.obj",
            pos=(0.0, 0.0, table_height + 0.28),
            scale=1.35,
        ),
        material=gs.materials.FEM.Cloth(
            density=0.5,
            youngs_modulus=5e4,
            poissons_ratio=0.3,
            thickness=0.01,
        ),
        surface=gs.surfaces.Default(color=(0.86, 0.18, 0.18, 1.0)),
    )

    cube_size = 0.12
    cube_positions = [
        (-0.28, -0.18, table_height + 0.75),
        (0.00, -0.10, table_height + 0.95),
        (0.24, 0.12, table_height + 1.15),
        (-0.18, 0.22, table_height + 1.35),
        (0.16, -0.26, table_height + 1.55),
        (0.32, 0.28, table_height + 1.75),
    ]
    cube_colors = [
        (0.95, 0.75, 0.20, 1.0),
        (0.20, 0.60, 0.95, 1.0),
        (0.30, 0.85, 0.40, 1.0),
        (0.90, 0.35, 0.35, 1.0),
        (0.75, 0.35, 0.90, 1.0),
        (0.95, 0.55, 0.15, 1.0),
    ]

    for pos, color in zip(cube_positions, cube_colors):
        scene.add_entity(
            morph=gs.morphs.Box(pos=pos, size=(cube_size, cube_size, cube_size)),
            material=gs.materials.Rigid(rho=700, friction=0.7, restitution=0.1),
            surface=gs.surfaces.Rough(color=color),
        )

    scene.add_camera(
        pos=(3.0, -2.8, 2.0),
        lookat=(0.0, 0.0, 0.7),
        res=(1280, 720),
        fov=50,
    )

    scene.build()

    for _ in range(1800):
        scene.step()


if __name__ == "__main__":
    main()