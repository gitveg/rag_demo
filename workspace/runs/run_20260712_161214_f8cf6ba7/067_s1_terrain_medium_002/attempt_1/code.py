import genesis as gs

def main():
    gs.init()

    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(10, -10, 10),
            camera_lookat=(0, 0, 0),
        ),
        show_viewer=True,
    )

    # Uneven rocky terrain with a 2x2 grid of two subtypes
    terrain = scene.add_entity(
        gs.morphs.Terrain(
            n_subterrains=(2, 2),
            subterrain_size=(6.0, 6.0),
            horizontal_scale=0.1,
            vertical_scale=0.5,
            subterrain_types=[
                ["fractal_terrain", "random_uniform_terrain"],
                ["fractal_terrain", "random_uniform_terrain"],
            ],
        ),
    )

    # Drop several rigid cubes at different locations above the terrain
    cube1 = scene.add_entity(
        gs.morphs.Box(pos=(1.5, 1.5, 2.0), size=(0.2, 0.2, 0.2)),
        material=gs.materials.Rigid(),
    )
    cube2 = scene.add_entity(
        gs.morphs.Box(pos=(-1.5, 1.5, 2.5), size=(0.2, 0.2, 0.2)),
        material=gs.materials.Rigid(),
    )
    cube3 = scene.add_entity(
        gs.morphs.Box(pos=(0.0, -1.5, 2.0), size=(0.2, 0.2, 0.2)),
        material=gs.materials.Rigid(),
    )
    cube4 = scene.add_entity(
        gs.morphs.Box(pos=(2.0, -2.0, 2.5), size=(0.2, 0.2, 0.2)),
        material=gs.materials.Rigid(),
    )

    scene.build()

    # Simulate until cubes settle
    for _ in range(1000):
        scene.step()

if __name__ == "__main__":
    main()