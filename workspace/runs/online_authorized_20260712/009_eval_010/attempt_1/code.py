import genesis as gs
import numpy as np

def main():
    gs.init()

    # disable gravity so spheres stay in mid-air
    sim_options = gs.options.SimOptions(dt=0.01, gravity=(0.0, 0.0, 0.0))

    scene = gs.Scene(
        sim_options=sim_options,
        show_viewer=False,       # headless; we'll record and save a video
        show_FPS=False,
    )

    # two spheres moving toward each other
    sphere_left = scene.add_entity(
        morph=gs.morphs.Sphere(pos=(-0.5, 0.0, 1.0), radius=0.1),
        material=gs.materials.Rigid(),
        surface=gs.surfaces.Default(color=(1.0, 0.0, 0.0, 1.0)),
    )
    sphere_right = scene.add_entity(
        morph=gs.morphs.Sphere(pos=(0.5, 0.0, 1.0), radius=0.1),
        material=gs.materials.Rigid(),
        surface=gs.surfaces.Default(color=(0.0, 0.0, 1.0, 1.0)),
    )

    scene.build()

    # record video of the collision
    scene.start_recording()

    # set initial velocities (approach each other)
    sphere_left.set_velocity(lin_vel=(1.0, 0.0, 0.0), ang_vel=(0.0, 0.0, 0.0))
    sphere_right.set_velocity(lin_vel=(-1.0, 0.0, 0.0), ang_vel=(0.0, 0.0, 0.0))

    # simulate until well after the collision
    for _ in range(100):
        scene.step()

    # save the recorded video
    scene.viewer.save_video(filename="two_spheres_collision.mp4")
    print("Simulation complete. Video saved as two_spheres_collision.mp4")

if __name__ == "__main__":
    main()