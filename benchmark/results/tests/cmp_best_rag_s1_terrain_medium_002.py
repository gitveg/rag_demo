import genesis as gs

def main():
    gs.init(backend=gs.gpu)

    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(8, -8, 6),
            camera_lookat=(0, 0, 0),
            camera_fov=40,
            max_FPS=60,
        ),
        rigid_options=gs.options.RigidOptions(
            dt=0.01,
            gravity=(0, 0, -9.81),
            constraint_solver=gs.constraint_solver.Native,
        ),
    )

    # Create uneven terrain using both random_uniform and fractal generation
    terrain = scene.add_entity(
        gs.morphs.Terrain(
            pos=(0, 0, 0),
            euler=(0, 0, 0),
            type='terrain',
            terrain_size=(10, 10),
            terrain_height_scale=0.5,
            terrain_subdiv=256,
            terrain_level=None,
            terrain_smooth_h_scale=None,
            terrain_smooth_v_scale=None,
            terrain_flat=None,
            random_uniform_terrain=True,
            terrain_random=(2, 0.001, 1, 0),
            terrain_fractal=(2, 6, 0.5, 4, 0),
            visual_material=gs.materials.RigidVisual(
                color=(0.6, 0.4, 0.2),
                roughness=1.0,
            ),
        ),
    )

    # Drop cubes at different locations above the terrain
    cube_positions = [
        (-3, -3, 3),
        (0, -2, 2.5),
        (3, -1, 2.0),
        (-2, 3, 3.5),
        (2, 2, 2.0),
        (-3, 0, 3.0),
        (0, 0, 2.5),
    ]
    for pos in cube_positions:
        scene.add_entity(
            gs.morphs.Box(pos=pos, size=(0.5, 0.5, 0.5)),
        )

    scene.build()

    # Run simulation for a few seconds to let cubes settle
    for _ in range(500):
        scene.step()

if __name__ == "__main__":
    main()