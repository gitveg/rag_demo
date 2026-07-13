import genesis as gs

def main():
    ########################## init ##########################
    gs.init(backend=gs.cpu)

    ########################## create a scene ##########################
    viewer_options = gs.options.ViewerOptions(
        camera_pos=(2.5, 0.0, 1.5),
        camera_lookat=(0.0, 0.0, 0.5),
        camera_fov=30,
        max_FPS=60,
    )
    scene = gs.Scene(viewer_options=viewer_options, show_viewer=True)

    ########################## entities ##########################
    # uneven terrain using fractal generation
    scene.add_entity(gs.morphs.Terrain(fractal_terrain=True))

    # Crazyflie 2.X drone
    drone = scene.add_entity(
        gs.morphs.Drone(file="urdf/drones/cf2x.urdf", model="CF2X")
    )

    ########################## turbulent wind ##########################
    turb = gs.force_fields.Turbulence()
    scene.add_force_field(turb)

    ########################## build and activate ##########################
    scene.build()
    turb.activate()

    ########################## simulation loop ##########################
    for _ in range(1000):
        scene.step()

if __name__ == "__main__":
    main()