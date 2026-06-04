import argparse
import threading
import time
import numpy as np
import genesis as gs

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(backend=gs.cpu)

    ########################## create a scene ##########################
    viewer_options = gs.options.ViewerOptions(
        camera_pos=(5.0, 5.0, 3.0),
        camera_lookat=(0.0, 0.0, 0.5),
        camera_fov=30,
        max_FPS=60,
    )

    scene = gs.Scene(
        viewer_options=viewer_options,
        show_viewer=args.vis,
        show_FPS=True,
    )

    ########################## add entities ##########################
    # Ground plane (sandy desert terrain)
    plane_morph = gs.options.morphs.Plane()
    plane_material = gs.materials.Rigid(rho=200.0, friction=0.5)
    scene.add_entity(
        morph=plane_morph,
        material=plane_material,
    )

    # Drone
    drone_morph = gs.options.morphs.Drone()
    drone_entity = scene.add_entity(
        morph=drone_morph,
        material=gs.materials.Rigid(rho=200.0),
    )

    ########################## build scene ##########################
    scene.build()

    ########################## add wind force field ##########################
    # Wind gust occasionally pushes the drone
    wind_field = gs.force_fields.Wind(
        direction=(1.0, 0.0, 0.0),
        strength=10.0,
        radius=2.0,
        center=(2.0, 0.0, 1.0),
    )
    scene.add_force_field(wind_field)
    wind_field.deactivate()  # start inactive

    ########################## simulation loop ##########################
    # Control wind activation roughly every 2-5 seconds
    last_toggle = time.time()
    wind_active = False

    for i in range(1000):
        now = time.time()
        if now - last_toggle > np.random.uniform(2.0, 5.0):
            if wind_active:
                wind_field.deactivate()
                wind_active = False
            else:
                # Update wind center near drone position
                drone_pos = drone_entity.get_pos()
                wind_field.center = (drone_pos[0] + 2.0, drone_pos[1], drone_pos[2])
                wind_field.activate()
                wind_active = True
            last_toggle = now

        scene.step()

if __name__ == "__main__":
    main()