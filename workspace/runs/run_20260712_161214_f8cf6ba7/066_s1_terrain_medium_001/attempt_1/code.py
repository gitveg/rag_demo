import genesis as gs

def main():
    gs.init(backend=gs.gpu)

    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(15.0, -20.0, 10.0),
            camera_lookat=(0.0, 0.0, 0.0),
        ),
        show_viewer=True,
    )

    # bumpy terrain with 3x3 grid of subterrains
    terrain = scene.add_entity(
        gs.morphs.Terrain(
            n_subterrains=(3, 3),
            subterrain_size=(6.0, 6.0),
            horizontal_scale=2.0,
            vertical_scale=3.0,
            subterrain_types=[
                ["random_uniform_terrain", "wave_terrain", "random_uniform_terrain"],
                ["wave_terrain", "random_uniform_terrain", "wave_terrain"],
                ["random_uniform_terrain", "wave_terrain", "random_uniform_terrain"],
            ],
        ),
    )

    # three rigid spheres at different locations, above the terrain
    sphere1 = scene.add_entity(
        gs.morphs.Sphere(radius=0.5, pos=(3.0, 10.0, 3.0), material=gs.materials.Rigid()),
    )
    sphere2 = scene.add_entity(
        gs.morphs.Sphere(radius=0.5, pos=(-4.0, 10.0, -2.0), material=gs.materials.Rigid()),
    )
    sphere3 = scene.add_entity(
        gs.morphs.Sphere(radius=0.5, pos=(0.0, 10.0, -4.0), material=gs.materials.Rigid()),
    )

    scene.build()

    # let them roll for a while
    for _ in range(1000):
        scene.step()

if __name__ == "__main__":
    main()