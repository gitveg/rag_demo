import genesis as gs
import numpy as np

def main():
    gs.init(backend=gs.cpu)  # Use CPU for simplicity; change to gs.gpu if needed.

    scene = gs.Scene(
        sim_options=gs.options.SimOptions(dt=1e-2),
        rigid_options=gs.options.RigidOptions(),
        viewer_options=gs.options.ViewerOptions(camera_pos=(3.0, 3.0, 3.0)),
        show_viewer=True,
    )

    # Central attractive radial force field (vacuum-like)
    force_field = gs.force_fields.CentralForce(
        center=(0.0, 0.0, 0.0),
        strength=5000.0,   # Strong pull
    )
    scene.add_force_field(force_field)

    # Add several surrounding objects at different positions
    object_positions = [
        (2.0, 0.0, 0.5),
        (-1.5, 1.5, 0.5),
        (0.0, -2.0, 0.5),
        (-2.0, 0.0, 0.5),
        (1.0, -1.5, 0.5),
        (0.0, 1.5, 0.5),
    ]
    for pos in object_positions:
        scene.add_entity(
            material=gs.materials.Rigid(rho=100.0),
            morph=gs.morphs.Sphere(pos=pos, radius=0.1),
            surface=gs.surfaces.Default(color=(0.8, 0.3, 0.3)),
        )

    scene.build(n_envs=0)

    # Simulate for a few seconds
    for _ in range(300):
        scene.step()

    if scene.viewer.is_alive:
        scene.viewer.stop()

if __name__ == "__main__":
    main()