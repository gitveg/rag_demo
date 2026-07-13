import genesis as gs

def main():
    gs.init(backend=gs.gpu)
    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(0, -10, 8),
            camera_lookat=(0, 0, 0),
        ),
        show_viewer=True,
    )

    # Define a 3x3 grid of sub-terrains: alternating sloped and stairs
    subterrain_types = [
        ["sloped_terrain", "stairs_terrain", "sloped_terrain"],
        ["stairs_terrain", "sloped_terrain", "stairs_terrain"],
        ["sloped_terrain", "stairs_terrain", "sloped_terrain"],
    ]
    cell_size = 2.0
    n_rows, n_cols = 3, 3

    # Add terrain
    scene.add_entity(
        morph=gs.morphs.Terrain(
            n_subterrains=(n_rows, n_cols),
            subterrain_size=(cell_size, cell_size),
            horizontal_scale=0.1,
            vertical_scale=0.1,
            subterrain_types=subterrain_types,
        ),
    )

    # Position objects above the terrain
    # cell (0,0) is sloped, cell (0,1) is stairs
    # world coordinates: (col-1)*cell_size for x, (1-row)*cell_size for y
    box_pos   = (-cell_size,  cell_size, 2.0)
    sphere_pos = (0.0,         cell_size, 2.0)

    # Add a rigid box
    scene.add_entity(
        gs.morphs.Box(pos=box_pos, size=(0.5, 0.5, 0.5)),
        material=gs.materials.Rigid(),
    )

    # Add a rigid sphere
    scene.add_entity(
        gs.morphs.Sphere(pos=sphere_pos, radius=0.3),
        material=gs.materials.Rigid(),
    )

    scene.build()

    # Run the simulation
    for _ in range(500):
        scene.step()

if __name__ == "__main__":
    main()