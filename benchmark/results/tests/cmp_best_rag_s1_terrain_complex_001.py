import genesis as gs

def main():
    # Initialize Genesis
    gs.init(backend=gs.gpu)  # or gs.cpu if no GPU

    # Define a 3x3 grid of sub-terrains, half sloped, half stairs (checkerboard)
    # Sloped cells: (0,0), (0,2), (1,1), (2,0), (2,2)
    # Stairs cells: (0,1), (1,0), (1,2), (2,1)
    sub_types = [
        ["sloped_terrain", "stairs_terrain", "sloped_terrain"],
        ["stairs_terrain", "sloped_terrain", "stairs_terrain"],
        ["sloped_terrain", "stairs_terrain", "sloped_terrain"],
    ]

    # Create the scene with interactive viewer
    scene = gs.Scene(show_viewer=True)

    # Add the multi‑terrain entity (static by default)
    terrain = scene.add_entity(
        gs.morphs.Terrain(
            n_subterrains=(3, 3),
            subterrain_types=sub_types,
        )
    )

    # Place a box near the top of a sloped cell – here (0,0)
    box = scene.add_entity(
        gs.morphs.Box(
            pos=(0.5, 0.5, 2.5),  # elevated above the terrain
            size=(0.2, 0.2, 0.2),
        ),
    )

    # Place a sphere near the top of a stairs cell – here (2,1)
    sphere = scene.add_entity(
        gs.morphs.Sphere(
            pos=(2.5, 1.5, 2.5),
            radius=0.15,
        ),
    )

    # Build the scene (required before stepping)
    scene.build()

    # Run the simulation for a few seconds
    for _ in range(1000):
        scene.step()

if __name__ == "__main__":
    main()