import genesis as gs
import torch

def main():
    gs.init()

    scene = gs.Scene(
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(0.0, 2.0, 3.0),
            camera_lookat=(0.0, 0.0, 1.0),
        ),
        show_viewer=True,
    )

    # Ground plane to eventually catch the spheres (optional)
    plane = scene.add_entity(
        gs.morphs.Plane(),
        material=gs.materials.Rigid(),
    )

    # Rigid material
    mat_rigid = gs.materials.Rigid()

    # Two spheres placed with an initial horizontal gap
    sphere1 = scene.add_entity(
        gs.morphs.Sphere(pos=(-0.5, 0.0, 1.0), radius=0.2),
        material=mat_rigid,
    )
    sphere2 = scene.add_entity(
        gs.morphs.Sphere(pos=(0.5, 0.0, 1.0), radius=0.2),
        material=mat_rigid,
    )

    scene.build()

    # Give the spheres initial velocities toward each other
    vx = 1.0   # speed in m/s
    sphere1.set_dofs_velocity(torch.tensor([ vx, 0.0, 0.0, 0.0, 0.0, 0.0]))
    sphere2.set_dofs_velocity(torch.tensor([-vx, 0.0, 0.0, 0.0, 0.0, 0.0]))

    # Simulate until collision and a bit after
    for _ in range(200):
        scene.step()

if __name__ == "__main__":
    main()